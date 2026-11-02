"""Lambda "api": router único para API Gateway HTTP API (payload 2.0)."""
import hmac
import logging
import os

from rutas import admin, items, publicas, trabajos
from rutas.http import ErrorHttp, header, respuesta

logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)

RUTAS = {
    "GET /health": publicas.salud,
    "POST /items": items.crear_item,
    "GET /items/{id}": items.obtener_item,
    "GET /items": items.listar_items,
    "POST /jobs": trabajos.crear_trabajo,
    "GET /jobs/{jobId}": trabajos.obtener_trabajo,
    "POST /uploads": publicas.crear_upload,
    "POST /reportes": publicas.crear_reporte,
    "GET /reportes": publicas.listar_reportes,
    "POST /reportes/{id}/confirmar": publicas.confirmar,
    "GET /admin/reportes": admin.listar,
    "PATCH /admin/reportes/{id}": admin.actualizar,
    "GET /admin/resumen": admin.resumen,
    "GET /admin/export.csv": admin.exportar_csv,
    "POST /admin/parte-situacional": admin.parte_situacional,
}


def _verificar_admin(event):
    esperada = os.environ.get("ADMIN_KEY", "")
    recibida = header(event, "x-admin-key")
    if not esperada or not recibida or not hmac.compare_digest(recibida.encode(), esperada.encode()):
        raise ErrorHttp(401, "Clave de administrador inválida")


def handler(event, context):
    ruta = event.get("routeKey", "")
    fn = RUTAS.get(ruta)
    if fn is None:
        return respuesta(404, {"error": "Ruta no encontrada"})
    try:
        if " /admin/" in ruta:
            _verificar_admin(event)
        return fn(event)
    except ErrorHttp as e:
        cuerpo = {"error": e.mensaje}
        if e.detalles:
            cuerpo["detalles"] = e.detalles
        return respuesta(e.status, cuerpo)
    except Exception:  # noqa: BLE001
        logger.exception("Error no controlado en %s", ruta)
        return respuesta(500, {"error": "Error interno. Intente de nuevo."})
