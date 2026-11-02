"""Reglas geográficas: bbox de la región Piura y distrito autodetectado por cercanía al centroide."""
import re
from pathlib import Path

import pytest

from dominio.catalogos import BBOX
from dominio.geo import distrito_mas_cercano, distritos
from dominio.validacion import ErrorValidacion, validar_reporte

RAIZ = Path(__file__).resolve().parents[2]
VALIDO = {"foto_key": "fotos/" + "b" * 32 + ".jpg", "lat": -5.19, "lon": -80.65, "distrito": "Piura",
          "tipo": "aniego_via", "vulnerables": False, "necesidades": [], "consentimiento": True}


@pytest.mark.parametrize("lat,lon,esperado", [
    (-5.1953, -80.6301, "Piura"),                   # Plaza de Armas de Piura
    (-5.1990, -80.6120, "Castilla"),
    (-5.1840, -80.6738, "Veintiséis de Octubre"),   # San Martín
    (-5.2659, -80.6757, "Catacaos"),
    (-5.3200, -80.6640, "Cura Mori"),
    (-4.9353, -80.3424, "Tambogrande"),
    (-4.6578, -80.2433, "Las Lomas"),
    (-4.9039, -80.6853, "Otro (región)"),           # Sullana: a más de 25 km de todo centroide
    (-5.3750, -79.6050, "Otro (región)"),           # Canchaque (sierra)
    (-4.6400, -79.7160, "Otro (región)"),           # Ayabaca
])
def test_distrito_mas_cercano(lat, lon, esperado):
    assert distrito_mas_cercano(lat, lon) == esperado


def test_cada_centroide_se_detecta_a_si_mismo():
    for d in distritos():
        assert distrito_mas_cercano(d["lat"], d["lon"]) == d["nombre"]


@pytest.mark.parametrize("lat,lon,aceptado", [
    (-4.0, -79.2, True), (-6.4, -81.4, True),       # las esquinas del bbox están incluidas
    (-3.99, -80.6, False), (-6.41, -80.6, False),   # fuera por latitud
    (-5.2, -79.19, False), (-5.2, -81.41, False),   # fuera por longitud
    (-12.05, -77.04, False),                        # Lima
])
def test_bbox_region_piura(lat, lon, aceptado):
    if aceptado:
        assert validar_reporte({**VALIDO, "lat": lat, "lon": lon})["lat"] == lat
    else:
        with pytest.raises(ErrorValidacion) as e:
            validar_reporte({**VALIDO, "lat": lat, "lon": lon})
        assert e.value.errores["ubicacion"] == "La ubicación está fuera de la región Piura"


@pytest.mark.parametrize("lat", [True, "-5.19", None])
def test_coordenadas_no_numericas_rechazadas(lat):
    with pytest.raises(ErrorValidacion) as e:
        validar_reporte({**VALIDO, "lat": lat})
    assert e.value.errores["ubicacion"] == "lat y lon deben ser números"


def test_bbox_y_radio_del_frontend_iguales_al_backend():
    js = (RAIZ / "frontend" / "src" / "lib" / "geo.js").read_text(encoding="utf-8")
    m = re.search(r"BBOX = \{ latMin: (-?[\d.]+), latMax: (-?[\d.]+), lonMin: (-?[\d.]+), lonMax: (-?[\d.]+) \}", js)
    assert m, "No se encontró BBOX en frontend/src/lib/geo.js"
    assert tuple(map(float, m.groups())) == (BBOX["lat_min"], BBOX["lat_max"], BBOX["lon_min"], BBOX["lon_max"])
    assert "maxKm = 25" in js  # mismo umbral que distrito_mas_cercano(max_km=25)
