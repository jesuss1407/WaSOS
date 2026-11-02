"""Utilidades geográficas: distancia haversine, zona crítica y distrito más cercanos."""
import json
import math
from functools import lru_cache
from pathlib import Path

from dominio.catalogos import RADIO_ZONA_CRITICA_M

_DATOS = Path(__file__).resolve().parent.parent / "datos"
_RADIO_TIERRA_M = 6_371_000


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en metros entre dos puntos (lat/lon en grados)."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * _RADIO_TIERRA_M * math.asin(math.sqrt(a))


@lru_cache(maxsize=1)
def zonas_criticas() -> list:
    return json.loads((_DATOS / "zonas_criticas.json").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def distritos() -> list:
    return json.loads((_DATOS / "distritos_piura.json").read_text(encoding="utf-8"))


def zona_critica_cercana(lat: float, lon: float, zonas: list | None = None,
                         radio_m: float = RADIO_ZONA_CRITICA_M) -> dict | None:
    """Devuelve {"nombre", "distancia_m"} de la zona crítica más cercana dentro del radio, o None."""
    zonas = zonas_criticas() if zonas is None else zonas
    mejor = None
    for z in zonas:
        d = haversine_m(lat, lon, z["lat"], z["lon"])
        if d <= radio_m and (mejor is None or d < mejor["distancia_m"]):
            mejor = {"nombre": z["nombre"], "distancia_m": round(d)}
    return mejor


def distrito_mas_cercano(lat: float, lon: float, max_km: float = 25) -> str:
    """Distrito de la provincia de Piura con el centroide más cercano; 'Otro (región)' si está lejos."""
    mejor, mejor_d = "Otro (región)", None
    for d in distritos():
        dist = haversine_m(lat, lon, d["lat"], d["lon"])
        if mejor_d is None or dist < mejor_d:
            mejor, mejor_d = d["nombre"], dist
    if mejor_d is None or mejor_d > max_km * 1000:
        return "Otro (región)"
    return mejor
