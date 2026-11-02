"""Acceso a DynamoDB (tabla Reportes, PK id) y a las fotos en S3."""
import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr
from botocore.config import Config
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_REGION", "us-east-1")
TABLA = os.environ.get("TABLA_REPORTES", "Reportes")
BUCKET = os.environ.get("BUCKET_FOTOS", "")

_dynamo = boto3.resource("dynamodb", region_name=REGION)
_s3 = boto3.client("s3", region_name=REGION,
                   config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}))


class NoEncontrado(Exception):
    pass


class ConflictoEstado(Exception):
    pass


def a_dynamo(valor):
    """Convierte floats a Decimal (requisito de DynamoDB)."""
    if isinstance(valor, float):
        return Decimal(str(valor))
    if isinstance(valor, dict):
        return {k: a_dynamo(v) for k, v in valor.items() if v is not None}
    if isinstance(valor, list):
        return [a_dynamo(v) for v in valor]
    return valor


def de_dynamo(valor):
    if isinstance(valor, Decimal):
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    if isinstance(valor, dict):
        return {k: de_dynamo(v) for k, v in valor.items()}
    if isinstance(valor, (list, set)):
        return [de_dynamo(v) for v in valor]
    return valor


def _tabla():
    return _dynamo.Table(TABLA)


def guardar(reporte: dict) -> None:
    _tabla().put_item(Item=a_dynamo(reporte), ConditionExpression="attribute_not_exists(id)")


def obtener(id_: str) -> dict:
    item = _tabla().get_item(Key={"id": id_}).get("Item")
    if not item:
        raise NoEncontrado(id_)
    return de_dynamo(item)


def listar() -> list:
    """Scan completo (suficiente para el volumen del demo; roadmap: GSI distrito+prioridad)."""
    items, kwargs = [], {}
    while True:
        resp = _tabla().scan(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    return [de_dynamo(i) for i in items]


def incrementar_confirmaciones(id_: str, ahora: str) -> dict:
    try:
        resp = _tabla().update_item(
            Key={"id": id_},
            UpdateExpression="ADD confirmaciones :uno SET actualizado_en = :ahora",
            ConditionExpression=Attr("id").exists(),
            ExpressionAttributeValues={":uno": 1, ":ahora": ahora},
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NoEncontrado(id_) from e
        raise
    return de_dynamo(resp["Attributes"])


def actualizar_prioridad(id_: str, prioridad: int, nivel: str, motivos: list, confirmaciones: int) -> bool:
    """Guarda la prioridad calculada con `confirmaciones` solo si ese conteo sigue vigente.

    Evita que dos confirmaciones simultáneas dejen una prioridad vieja: si otra confirmación ya subió el
    conteo, esta escritura se descarta (la más reciente escribe la suya). Devuelve False si se descartó.
    """
    try:
        _tabla().update_item(
            Key={"id": id_},
            UpdateExpression="SET prioridad = :p, nivel = :n, motivos = :m",
            ConditionExpression="confirmaciones = :c",
            ExpressionAttributeValues={":p": prioridad, ":n": nivel, ":m": motivos, ":c": confirmaciones},
        )
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return False
        raise


def cambiar_estado(id_: str, estado_actual: str, nuevo_estado: str, brigada: str | None,
                   entrada_historial: dict, ahora: str) -> dict:
    """Actualiza el estado con bloqueo optimista (el estado no cambió desde la lectura)."""
    expr = "SET estado = :e, actualizado_en = :a, historial = list_append(if_not_exists(historial, :vacia), :h)"
    valores = {":e": nuevo_estado, ":a": ahora, ":h": [a_dynamo(entrada_historial)], ":vacia": [],
               ":actual": estado_actual}
    if brigada:
        expr += ", brigada = :b"
        valores[":b"] = brigada
    try:
        resp = _tabla().update_item(
            Key={"id": id_},
            UpdateExpression=expr,
            ConditionExpression="estado = :actual",
            ExpressionAttributeValues=valores,
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise ConflictoEstado(id_) from e
        raise
    return de_dynamo(resp["Attributes"])


# ---------- Fotos (S3 privado) ----------

def url_subida(foto_key: str, content_type: str = "image/jpeg", expira_s: int = 300) -> str:
    return _s3.generate_presigned_url(
        "put_object", Params={"Bucket": BUCKET, "Key": foto_key, "ContentType": content_type},
        ExpiresIn=expira_s)


def url_lectura(foto_key: str, expira_s: int = 900) -> str:
    return _s3.generate_presigned_url(
        "get_object", Params={"Bucket": BUCKET, "Key": foto_key}, ExpiresIn=expira_s)


def leer_foto(foto_key: str, max_bytes: int) -> bytes:
    """Lee la foto subida; lanza NoEncontrado si no existe y ValueError si excede el tamaño."""
    try:
        cabecera = _s3.head_object(Bucket=BUCKET, Key=foto_key)
    except ClientError as e:
        if e.response["Error"]["Code"] in ("404", "NoSuchKey", "NotFound"):
            raise NoEncontrado(foto_key) from e
        raise
    if cabecera["ContentLength"] > max_bytes:
        raise ValueError("La foto excede el tamaño permitido")
    return _s3.get_object(Bucket=BUCKET, Key=foto_key)["Body"].read()
