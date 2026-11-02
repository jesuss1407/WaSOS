import os
import sys
from pathlib import Path

# Credenciales y recursos falsos ANTES de importar el código: ningún test puede tocar la cuenta real de AWS.
os.environ.update({
    "AWS_ACCESS_KEY_ID": "testing",
    "AWS_SECRET_ACCESS_KEY": "testing",
    "AWS_SESSION_TOKEN": "testing",
    "AWS_DEFAULT_REGION": "us-east-1",
    "AWS_REGION": "us-east-1",
    "TABLA_REPORTES": "Reportes-test",
    "BUCKET_FOTOS": "fotos-test",
    "ADMIN_KEY": "clave-de-prueba-0123456789",
    "TEAM_ID": "equipo-de-prueba",
    "TABLE_NAME": "Items-test",
})
os.environ.pop("AWS_PROFILE", None)

# moto debe importarse antes de crear clientes boto3 (repositorio.py los crea al importarse)
import boto3  # noqa: E402
import pytest  # noqa: E402
from moto import mock_aws  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


@pytest.fixture
def aws():
    """DynamoDB y S3 simulados en memoria (moto), con la misma tabla y bucket que usa la Lambda."""
    with mock_aws():
        boto3.client("dynamodb").create_table(
            TableName="Reportes-test",
            BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
        )
        boto3.client("s3").create_bucket(Bucket="fotos-test")
        yield


class TablaFalsa:
    """Imita la Table de boto3 de ItemsTable: put/get por `id` y scan paginado (`por_pagina` ítems por página)."""

    def __init__(self, por_pagina=2):
        self.datos, self.por_pagina, self.scans = {}, por_pagina, 0

    def put_item(self, Item, **_):
        self.datos[Item["id"]] = dict(Item)

    def get_item(self, Key):
        item = self.datos.get(Key["id"])
        return {"Item": dict(item)} if item else {}

    def scan(self, ExclusiveStartKey=None, ProjectionExpression=None, ExpressionAttributeNames=None, **_):
        self.scans += 1
        claves = sorted(self.datos)  # orden arbitrario respecto de la creación, como en DynamoDB
        inicio = claves.index(ExclusiveStartKey["id"]) + 1 if ExclusiveStartKey else 0
        pagina = claves[inicio:inicio + self.por_pagina]
        campos = None
        if ProjectionExpression:  # como DynamoDB: solo devuelve los atributos proyectados que existan
            nombres = ExpressionAttributeNames or {}
            campos = {nombres.get(c.strip(), c.strip()) for c in ProjectionExpression.split(",")}
        items = [{k: v for k, v in self.datos[c].items() if campos is None or k in campos} for c in pagina]
        resp = {"Items": items}
        if inicio + self.por_pagina < len(claves):
            resp["LastEvaluatedKey"] = {"id": pagina[-1]}
        return resp


@pytest.fixture
def tabla(monkeypatch):
    """ItemsTable falsa: reemplaza `datos.items.TABLE` (usada por /items y /jobs)."""
    from datos import items as repo_items
    t = TablaFalsa()
    monkeypatch.setattr(repo_items, "TABLE", t)
    return t
