"""Lógica compartida entre rutas: tipo efectivo, recálculo de prioridad y vistas pública/admin."""
from dominio.geo import zona_critica_cercana
from dominio.prioridad import calcular_prioridad


def tipo_efectivo(r: dict) -> str:
    ia = r.get("ia") or {}
    return ia.get("tipo") if ia.get("estado_ia") in ("ok", "demo") and ia.get("tipo") else r["tipo_usuario"]


def calcular_para(r: dict) -> dict:
    ia = r.get("ia") or {}
    return calcular_prioridad(
        severidad=ia.get("severidad", 2),
        tipo=tipo_efectivo(r),
        vulnerables=bool(r.get("vulnerables")),
        zona_cercana=zona_critica_cercana(r["lat"], r["lon"]),
        confirmaciones=int(r.get("confirmaciones", 0)),
        riesgo_vida=bool(ia.get("riesgo_vida")),
        riesgo_salud=bool(ia.get("riesgo_salud")),
        es_valida=bool(ia.get("es_valida", True)),
        ia_disponible=ia.get("estado_ia") != "fallback",
    )


def a_publico(r: dict) -> dict:
    """Vista pública: sin foto, sin descripción libre del vecino, coordenadas a 4 decimales."""
    ia = r.get("ia") or {}
    return {
        "id": r["id"],
        "creado_en": r["creado_en"],
        "lat": round(float(r["lat"]), 4),
        "lon": round(float(r["lon"]), 4),
        "distrito": r["distrito"],
        "tipo": tipo_efectivo(r),
        "severidad": ia.get("severidad"),
        "descripcion_ia": ia.get("descripcion"),
        "riesgo_vida": bool(ia.get("riesgo_vida")),
        "riesgo_salud": bool(ia.get("riesgo_salud")),
        "es_valida": bool(ia.get("es_valida", True)),
        "necesidades": r.get("necesidades", []),
        "vulnerables": bool(r.get("vulnerables")),
        "prioridad": r["prioridad"],
        "nivel": r["nivel"],
        "motivos": r.get("motivos", []),
        "confirmaciones": int(r.get("confirmaciones", 0)),
        "estado": r["estado"],
    }


def ordenar(reportes: list) -> list:
    return sorted(reportes, key=lambda r: (r.get("prioridad", 0), r.get("creado_en", "")), reverse=True)
