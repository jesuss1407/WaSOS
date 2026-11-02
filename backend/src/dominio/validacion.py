"""Validación de entradas en el borde de confianza (la API es pública y sin login)."""
import re

from dominio.catalogos import (BBOX, DESCRIPCION_MAX, DISTRITOS, ESTADOS, NECESIDADES,
                               TIPOS)

FOTO_KEY_RE = re.compile(r"^fotos/[0-9a-f]{32}\.jpg$")
ID_RE = re.compile(r"^[0-9a-f]{32}$")


class ErrorValidacion(Exception):
    def __init__(self, errores: dict):
        super().__init__("Datos inválidos")
        self.errores = errores


def _numero(valor):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValueError
    return float(valor)


def validar_reporte(body: dict) -> dict:
    """Valida el cuerpo de POST /reportes. Devuelve un dict limpio o lanza ErrorValidacion."""
    if not isinstance(body, dict):
        raise ErrorValidacion({"body": "Se esperaba un objeto JSON"})
    errores = {}
    limpio = {}

    foto_key = body.get("foto_key")
    if not isinstance(foto_key, str) or not FOTO_KEY_RE.match(foto_key):
        errores["foto_key"] = "foto_key inválida (use la devuelta por POST /uploads)"
    else:
        limpio["foto_key"] = foto_key

    try:
        lat = _numero(body.get("lat"))
        lon = _numero(body.get("lon"))
        if not (BBOX["lat_min"] <= lat <= BBOX["lat_max"] and BBOX["lon_min"] <= lon <= BBOX["lon_max"]):
            errores["ubicacion"] = "La ubicación está fuera de la región Piura"
        else:
            limpio["lat"], limpio["lon"] = round(lat, 6), round(lon, 6)
    except (TypeError, ValueError):
        errores["ubicacion"] = "lat y lon deben ser números"

    distrito = body.get("distrito")
    if distrito not in DISTRITOS:
        errores["distrito"] = "Distrito no válido"
    else:
        limpio["distrito"] = distrito

    tipo = body.get("tipo")
    if tipo not in TIPOS:
        errores["tipo"] = "Tipo no válido"
    else:
        limpio["tipo"] = tipo

    descripcion = body.get("descripcion") or ""
    if not isinstance(descripcion, str):
        errores["descripcion"] = "La descripción debe ser texto"
    elif len(descripcion) > DESCRIPCION_MAX:
        errores["descripcion"] = f"Máximo {DESCRIPCION_MAX} caracteres"
    else:
        limpio["descripcion"] = descripcion.strip()

    vulnerables = body.get("vulnerables", False)
    if not isinstance(vulnerables, bool):
        errores["vulnerables"] = "vulnerables debe ser true o false"
    else:
        limpio["vulnerables"] = vulnerables

    necesidades = body.get("necesidades", [])
    if not isinstance(necesidades, list) or any(n not in NECESIDADES for n in necesidades):
        errores["necesidades"] = "Necesidades no válidas"
    else:
        limpio["necesidades"] = sorted(set(necesidades))

    if body.get("consentimiento") is not True:
        errores["consentimiento"] = "Se requiere el consentimiento (Ley 29733)"

    if errores:
        raise ErrorValidacion(errores)
    return limpio


def validar_cambio_estado(body: dict) -> dict:
    if not isinstance(body, dict):
        raise ErrorValidacion({"body": "Se esperaba un objeto JSON"})
    errores = {}
    estado = body.get("estado")
    if estado not in ESTADOS:
        errores["estado"] = "Estado no válido"
    brigada = body.get("brigada")
    if brigada is not None and (not isinstance(brigada, str) or len(brigada) > 80):
        errores["brigada"] = "Brigada: texto de hasta 80 caracteres"
    nota = body.get("nota")
    if nota is not None and (not isinstance(nota, str) or len(nota) > 300):
        errores["nota"] = "Nota: texto de hasta 300 caracteres"
    if estado == "en_atencion" and not (isinstance(brigada, str) and brigada.strip()):
        errores["brigada"] = "Asigne una brigada para pasar a 'en_atencion'"
    if errores:
        raise ErrorValidacion(errores)
    return {
        "estado": estado,
        "brigada": brigada.strip() if isinstance(brigada, str) and brigada.strip() else None,
        "nota": nota.strip() if isinstance(nota, str) and nota.strip() else None,
    }
