"""ItemsTable (PK id), separada de Reportes: ítems de la insignia "Persistencia" y trabajos de "Asíncrono o agente"."""
import os

import boto3

REGION = os.environ.get("AWS_REGION", "us-east-1")
TABLE = boto3.resource("dynamodb", region_name=REGION).Table(os.environ.get("TABLE_NAME", "Items"))
MAX_LISTADO = 100


def guardar(item: dict) -> None:
    TABLE.put_item(Item=item, ConditionExpression="attribute_not_exists(id)")


def obtener(id_: str) -> dict | None:
    return TABLE.get_item(Key={"id": id_}).get("Item")


def listar(maximo: int = MAX_LISTADO) -> list:
    """Recorre todas las páginas del scan y devuelve los `maximo` más recientes.

    El scan no tiene orden: cortar en la primera página (o en los primeros 100) podría dejar fuera el ítem recién
    creado. Por eso se lee la tabla completa y se ordena por `creado_en` antes de recortar.
    """
    items, kwargs = [], {"ProjectionExpression": "id, #v, creado_en", "ExpressionAttributeNames": {"#v": "value"}}
    while True:
        resp = TABLE.scan(**kwargs)
        items.extend(resp.get("Items", []))
        if "LastEvaluatedKey" not in resp:
            break
        kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
    items = [i for i in items if "value" in i]  # los trabajos de /jobs comparten tabla y no tienen `value`
    items.sort(key=lambda i: i.get("creado_en", ""), reverse=True)
    return items[:maximo]
