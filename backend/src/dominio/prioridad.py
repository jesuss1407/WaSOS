"""Priorización explicable 0-100 (función pura, sin I/O).

p = 100 x ( 0.40*(severidad/5) + 0.20*peso_tipo + 0.15*vulnerables
          + 0.15*cerca_zona_critica + 0.10*min(confirmaciones/5, 1) )
+10 si riesgo_vida (tope 100); es_valida=false -> p = min(p, 20)
Nivel: >=75 CRÍTICA, 50-74 ALTA, 25-49 MEDIA, <25 BAJA
"""
from dominio.catalogos import PESO_TIPO


def nivel_de(prioridad: int) -> str:
    if prioridad >= 75:
        return "CRÍTICA"
    if prioridad >= 50:
        return "ALTA"
    if prioridad >= 25:
        return "MEDIA"
    return "BAJA"


def calcular_prioridad(*, severidad: int, tipo: str, vulnerables: bool,
                       zona_cercana: dict | None, confirmaciones: int,
                       riesgo_vida: bool, riesgo_salud: bool, es_valida: bool,
                       ia_disponible: bool = True) -> dict:
    """Devuelve {"prioridad": int, "nivel": str, "motivos": [str]}.

    zona_cercana: {"nombre": str, "distancia_m": int} si el punto está a <=300 m de una zona crítica.
    """
    severidad = max(1, min(5, int(severidad)))
    confirmaciones = max(0, int(confirmaciones))
    peso_tipo = PESO_TIPO.get(tipo, PESO_TIPO["otro"])

    suma = (0.40 * (severidad / 5)
            + 0.20 * peso_tipo
            + 0.15 * (1 if vulnerables else 0)
            + 0.15 * (1 if zona_cercana else 0)
            + 0.10 * min(confirmaciones / 5, 1))
    p = 100 * suma
    if riesgo_vida:
        p += 10
    p = min(round(p), 100)
    if not es_valida:
        p = min(p, 20)

    motivos = []
    if ia_disponible:
        motivos.append(f"Severidad IA {severidad}/5")
    else:
        motivos.append(f"Severidad estimada {severidad}/5")
        motivos.append("IA no disponible: verificar manualmente")
    if riesgo_vida:
        motivos.append("Riesgo para la vida")
    if zona_cercana:
        motivos.append(f"A {zona_cercana['distancia_m']} m de zona crítica: {zona_cercana['nombre']}")
    if vulnerables:
        motivos.append("Personas vulnerables")
    if riesgo_salud:
        motivos.append("Riesgo sanitario (dengue / leptospirosis)")
    if confirmaciones == 1:
        motivos.append("1 vecino confirma")
    elif confirmaciones > 1:
        motivos.append(f"{confirmaciones} vecinos confirman")
    if not es_valida:
        motivos.append("Foto no muestra un riesgo claro: revisar")

    return {"prioridad": p, "nivel": nivel_de(p), "motivos": motivos}
