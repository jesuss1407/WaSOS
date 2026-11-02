"""Helpers HTTP para eventos de API Gateway HTTP API (payload 2.0)."""
import base64
import json
from datetime import datetime, timezone
from decimal import Decimal


class ErrorHttp(Exception):
    def __init__(self, status: int, mensaje: str, detalles: dict | None = None):
        super().__init__(mensaje)
        self.status = status
        self.mensaje = mensaje
        self.detalles = detalles


def _por_defecto(o):
    if isinstance(o, Decimal):
        return int(o) if o == o.to_integral_value() else float(o)
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(f"No serializable: {type(o)}")


def respuesta(status: int, cuerpo, headers: dict | None = None) -> dict:
    h = {"Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store"}
    h.update(headers or {})
    return {"statusCode": status, "headers": h,
            "body": json.dumps(cuerpo, ensure_ascii=False, default=_por_defecto)}


def leer_json(event: dict) -> dict:
    cuerpo = event.get("body") or ""
    if event.get("isBase64Encoded"):
        cuerpo = base64.b64decode(cuerpo).decode("utf-8")
    if not cuerpo:
        return {}
    if len(cuerpo) > 20_000:
        raise ErrorHttp(413, "Cuerpo demasiado grande")
    try:
        return json.loads(cuerpo)
    except json.JSONDecodeError as e:
        raise ErrorHttp(400, "JSON inválido") from e


def query(event: dict) -> dict:
    return event.get("queryStringParameters") or {}


def path_param(event: dict, nombre: str) -> str:
    return (event.get("pathParameters") or {}).get(nombre, "")


def header(event: dict, nombre: str) -> str:
    return (event.get("headers") or {}).get(nombre.lower(), "")


def ahora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
