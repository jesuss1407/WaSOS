import pytest

from dominio.geo import haversine_m, zona_critica_cercana
from dominio.prioridad import calcular_prioridad, nivel_de

BASE = dict(severidad=3, tipo="aniego_via", vulnerables=False, zona_cercana=None,
            confirmaciones=0, riesgo_vida=False, riesgo_salud=False, es_valida=True)


def p(**kw):
    return calcular_prioridad(**{**BASE, **kw})


def test_formula_base():
    # 100 * (0.40*3/5 + 0.20*0.6) = 36
    assert p()["prioridad"] == 36
    assert p()["nivel"] == "MEDIA"


def test_maximo_con_riesgo_vida_tiene_tope_100():
    r = p(severidad=5, tipo="desborde_rio_quebrada", vulnerables=True,
          zona_cercana={"nombre": "Dos Grifos", "distancia_m": 120}, confirmaciones=9, riesgo_vida=True)
    assert r["prioridad"] == 100
    assert r["nivel"] == "CRÍTICA"


def test_foto_no_valida_limita_a_20():
    r = p(severidad=5, tipo="inundacion_vivienda", vulnerables=True, es_valida=False)
    assert r["prioridad"] == 20
    assert r["nivel"] == "BAJA"
    assert any("no muestra un riesgo" in m for m in r["motivos"])


def test_confirmaciones_saturan_en_5():
    assert p(confirmaciones=5)["prioridad"] == p(confirmaciones=50)["prioridad"] == 46


@pytest.mark.parametrize("valor,nivel", [(100, "CRÍTICA"), (75, "CRÍTICA"), (74, "ALTA"), (50, "ALTA"),
                                         (49, "MEDIA"), (25, "MEDIA"), (24, "BAJA"), (0, "BAJA")])
def test_umbrales_de_nivel(valor, nivel):
    assert nivel_de(valor) == nivel


def test_motivos_legibles():
    r = p(severidad=4, vulnerables=True, zona_cercana={"nombre": "Dos Grifos", "distancia_m": 120},
          confirmaciones=3)
    assert r["motivos"] == ["Severidad IA 4/5", "A 120 m de zona crítica: Dos Grifos",
                            "Personas vulnerables", "3 vecinos confirman"]


def test_fallback_ia_marca_verificacion_manual():
    r = p(ia_disponible=False)
    assert "IA no disponible: verificar manualmente" in r["motivos"]


def test_haversine_aproximado():
    # 0.001 grados de latitud ~ 111 m
    assert 105 < haversine_m(-5.19, -80.63, -5.191, -80.63) < 117


def test_zona_critica_dentro_y_fuera_del_radio():
    zonas = [{"nombre": "Z", "lat": -5.19, "lon": -80.63}]
    cerca = zona_critica_cercana(-5.1915, -80.63, zonas)
    assert cerca and cerca["nombre"] == "Z" and cerca["distancia_m"] <= 300
    assert zona_critica_cercana(-5.20, -80.63, zonas) is None
