"""Rutas públicas (sin login): salud, subir foto, crear reporte, mapa público y "yo también lo veo"."""
import logging
import os
import uuid

from botocore.exceptions import ClientError

from datos import repositorio as repo
from dominio.catalogos import DISTRITOS, ESTADOS_ACTIVOS, NIVELES
from dominio.validacion import ID_RE, ErrorValidacion, validar_reporte
from ia import clasificador
from rutas.http import ErrorHttp, ahora_iso, leer_json, path_param, query, respuesta
from rutas.servicio import a_publico, calcular_para, ordenar

logger = logging.getLogger(__name__)
MAX_FOTO_BYTES = 1_500_000  # el cliente comprime a <=300 KB; margen para navegadores antiguos


def salud(event):
    """Insignia "API viva" de la Kiro IAthon: claves fijas en inglés, `team` = parámetro TeamId de SAM."""
    return respuesta(200, {"status": "ok", "team": os.environ.get("TEAM_ID", "")})


def crear_upload(event):
    body = leer_json(event)
    if body.get("content_type", "image/jpeg") != "image/jpeg":
        raise ErrorHttp(400, "Solo se acepta image/jpeg")
    foto_key = f"fotos/{uuid.uuid4().hex}.jpg"
    return respuesta(200, {"upload_url": repo.url_subida(foto_key), "foto_key": foto_key})


def crear_reporte(event):
    try:
        datos = validar_reporte(leer_json(event))
    except ErrorValidacion as e:
        raise ErrorHttp(400, "Datos inválidos", e.errores) from e

    # id = uuid de la foto: un reintento (cola offline) no duplica el reporte
    id_ = datos["foto_key"][len("fotos/"):-len(".jpg")]
    try:
        existente = repo.obtener(id_)
        return respuesta(200, a_publico(existente))
    except repo.NoEncontrado:
        pass

    try:
        imagen = repo.leer_foto(datos["foto_key"], MAX_FOTO_BYTES)
    except repo.NoEncontrado as e:
        raise ErrorHttp(400, "No se encontró la foto: súbala primero con POST /uploads") from e
    except ValueError as e:
        raise ErrorHttp(413, str(e)) from e

    ia = clasificador.clasificar(imagen, datos["tipo"], datos.get("descripcion", ""))
    ahora = ahora_iso()
    reporte = {
        "id": id_,
        "creado_en": ahora,
        "actualizado_en": ahora,
        "lat": datos["lat"],
        "lon": datos["lon"],
        "distrito": datos["distrito"],
        "tipo_usuario": datos["tipo"],
        "descripcion": datos.get("descripcion", ""),
        "vulnerables": datos["vulnerables"],
        "necesidades": datos["necesidades"],
        "foto_key": datos["foto_key"],
        "ia": ia,
        "confirmaciones": 0,
        "estado": "nuevo",
        "brigada": None,
        "historial": [{"estado": "nuevo", "fecha": ahora, "nota": "Reporte ciudadano"}],
        "origen": "ciudadano",
    }
    reporte.update(calcular_para(reporte))
    try:
        repo.guardar(reporte)
    except ClientError as e:  # carrera con un reintento simultáneo
        if e.response["Error"]["Code"] != "ConditionalCheckFailedException":
            raise
        return respuesta(200, a_publico(repo.obtener(id_)))
    logger.info("Reporte creado id=%s nivel=%s estado_ia=%s", id_, reporte["nivel"], ia["estado_ia"])
    return respuesta(201, a_publico(reporte))


def listar_reportes(event):
    q = query(event)
    distrito, nivel = q.get("distrito"), q.get("nivel")
    if distrito and distrito not in DISTRITOS:
        raise ErrorHttp(400, "Distrito no válido")
    if nivel and nivel not in NIVELES:
        raise ErrorHttp(400, "Nivel no válido")
    reportes = [r for r in repo.listar()
                if (r.get("ia") or {}).get("es_valida", True)
                and r.get("estado") != "descartado"
                and (not distrito or r["distrito"] == distrito)
                and (not nivel or r["nivel"] == nivel)]
    return respuesta(200, [a_publico(r) for r in ordenar(reportes)])


def confirmar(event):
    id_ = path_param(event, "id")
    if not ID_RE.match(id_):
        raise ErrorHttp(400, "id inválido")
    try:
        actual = repo.obtener(id_)
    except repo.NoEncontrado as e:
        raise ErrorHttp(404, "Reporte no encontrado") from e
    if actual.get("estado") not in ESTADOS_ACTIVOS or not (actual.get("ia") or {}).get("es_valida", True):
        raise ErrorHttp(409, "Este reporte ya no admite confirmaciones")
    r = repo.incrementar_confirmaciones(id_, ahora_iso())
    confirmaciones = int(r.get("confirmaciones", 0))
    p = calcular_para(r)
    repo.actualizar_prioridad(id_, p["prioridad"], p["nivel"], p["motivos"], confirmaciones)
    return respuesta(200, {"id": id_, "confirmaciones": confirmaciones, **p})
