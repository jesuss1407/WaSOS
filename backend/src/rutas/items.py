"""Rutas públicas de la insignia "Persistencia" (Kiro IAthon): POST /items, GET /items/{id}, GET /items."""
import re
import uuid
from datetime import datetime, timezone

from datos import items as repo_items
from rutas.http import ErrorHttp, leer_json, path_param, respuesta

ID_ITEM_RE = re.compile(r"^[0-9a-f]{32}$")
MAX_VALUE = 1024


def _publico(item: dict) -> dict:
    return {"id": item["id"], "value": item["value"]}


def _es_item(item: dict | None) -> bool:
    """ItemsTable también guarda trabajos de /jobs (sin `value`): no deben salir por /items."""
    return bool(item) and "value" in item


def crear_item(event):
    body = leer_json(event)
    valor = body.get("value") if isinstance(body, dict) else None
    if not isinstance(valor, str) or not valor or len(valor) > MAX_VALUE:
        raise ErrorHttp(400, "Datos inválidos", {"value": f"Texto obligatorio de hasta {MAX_VALUE} caracteres"})
    item = {"id": uuid.uuid4().hex, "value": valor,
            "creado_en": datetime.now(timezone.utc).isoformat(timespec="microseconds")}
    repo_items.guardar(item)
    return respuesta(201, _publico(item))


def obtener_item(event):
    id_ = path_param(event, "id")
    item = repo_items.obtener(id_) if ID_ITEM_RE.match(id_) else None
    if not _es_item(item):
        raise ErrorHttp(404, "Ítem no encontrado")
    return respuesta(200, _publico(item))


def listar_items(event):
    return respuesta(200, [_publico(i) for i in repo_items.listar()])
