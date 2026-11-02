"""Rutas públicas de la insignia "Asíncrono o agente" (Kiro IAthon): POST /jobs y GET /jobs/{jobId}.

El trabajo se guarda en ItemsTable con `tipo = "job"` y `listo_en` (epoch ms). GET lo resuelve al leer: desde
`listo_en` responde "done" con la entrada invertida. Sin colas ni procesos extra.
"""
import time
import uuid
from datetime import datetime, timezone

from datos import items as repo_items
from dominio import trabajos
from rutas.http import ErrorHttp, leer_json, path_param, respuesta
from rutas.items import ID_ITEM_RE, MAX_VALUE

TIPO = "job"


def _ahora_ms() -> int:
    return int(time.time() * 1000)


def crear_trabajo(event):
    body = leer_json(event)
    entrada = body.get("input") if isinstance(body, dict) else None
    if not isinstance(entrada, str) or not entrada or len(entrada) > MAX_VALUE:
        raise ErrorHttp(400, "Datos inválidos", {"input": f"Texto obligatorio de hasta {MAX_VALUE} caracteres"})
    trabajo = {"id": uuid.uuid4().hex, "tipo": TIPO, "input": entrada,
               "creado_en": datetime.now(timezone.utc).isoformat(timespec="microseconds"),
               "listo_en": _ahora_ms() + trabajos.ESPERA_MS}
    repo_items.guardar(trabajo)
    return respuesta(202, {"jobId": trabajo["id"]})


def obtener_trabajo(event):
    id_ = path_param(event, "jobId")
    trabajo = repo_items.obtener(id_) if ID_ITEM_RE.match(id_) else None
    if not trabajo or trabajo.get("tipo") != TIPO:
        raise ErrorHttp(404, "Trabajo no encontrado")
    return respuesta(200, {"jobId": trabajo["id"],
                           **trabajos.estado(trabajo["input"], int(trabajo["listo_en"]), _ahora_ms())})
