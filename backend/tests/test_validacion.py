import json
from pathlib import Path

import pytest

from dominio.catalogos import BBOX
from dominio.validacion import ErrorValidacion, validar_cambio_estado, validar_reporte

RAIZ = Path(__file__).resolve().parents[2]

VALIDO = {"foto_key": "fotos/" + "a" * 32 + ".jpg", "lat": -5.19, "lon": -80.65,
          "distrito": "Veintiséis de Octubre", "tipo": "dren_colmatado", "descripcion": "Dren lleno",
          "vulnerables": True, "necesidades": ["motobomba", "agua"], "consentimiento": True}


def test_reporte_valido():
    r = validar_reporte(VALIDO)
    assert r["necesidades"] == ["agua", "motobomba"]
    assert r["tipo"] == "dren_colmatado"


@pytest.mark.parametrize("campo,valor,clave", [
    ("consentimiento", False, "consentimiento"),
    ("lat", -12.05, "ubicacion"),          # Lima: fuera de la región
    ("lon", "x", "ubicacion"),
    ("tipo", "tsunami", "tipo"),
    ("necesidades", ["agua", "dinero"], "necesidades"),
    ("descripcion", "x" * 501, "descripcion"),
    ("foto_key", "../otro/archivo.jpg", "foto_key"),
    ("distrito", "Lima", "distrito"),
])
def test_reporte_invalido(campo, valor, clave):
    with pytest.raises(ErrorValidacion) as e:
        validar_reporte({**VALIDO, campo: valor})
    assert clave in e.value.errores


def test_en_atencion_requiere_brigada():
    with pytest.raises(ErrorValidacion):
        validar_cambio_estado({"estado": "en_atencion"})
    assert validar_cambio_estado({"estado": "en_atencion", "brigada": " B1 "})["brigada"] == "B1"


@pytest.mark.parametrize("archivo", ["distritos_piura.json", "zonas_criticas.json", "seed_reportes.json"])
def test_datos_demo_dentro_del_bbox(archivo):
    datos = json.loads((RAIZ / "data" / archivo).read_text(encoding="utf-8"))
    assert datos
    for d in datos:
        assert BBOX["lat_min"] <= d["lat"] <= BBOX["lat_max"]
        assert BBOX["lon_min"] <= d["lon"] <= BBOX["lon_max"]


def test_datos_lambda_sincronizados_con_data():
    for archivo in ["distritos_piura.json", "zonas_criticas.json"]:
        assert (RAIZ / "data" / archivo).read_bytes() == (RAIZ / "backend" / "src" / "datos" / archivo).read_bytes()
