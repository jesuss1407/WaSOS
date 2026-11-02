"""Insignia "Asíncrono o agente" (Kiro IAthon): POST /jobs y GET /jobs/{jobId} con una tabla falsa."""
import json

import pytest

import app
from dominio import trabajos
from rutas import trabajos as rutas_trabajos

# `tabla`: ItemsTable falsa (conftest.py)


@pytest.fixture
def reloj(monkeypatch):
    """Reloj controlable en milisegundos para no esperar 2 s reales."""
    estado = {"ms": 1_000_000}
    monkeypatch.setattr(rutas_trabajos, "_ahora_ms", lambda: estado["ms"])
    return estado


def llamar(ruta, body=None, job_id=None):
    r = app.handler({"routeKey": ruta, "headers": {}, "body": json.dumps(body) if body is not None else None,
                     "pathParameters": {"jobId": job_id} if job_id else None, "isBase64Encoded": False}, None)
    assert r["headers"]["Content-Type"].startswith("application/json")
    return r["statusCode"], json.loads(r["body"])


def test_trabajo_pasa_de_queued_a_done_con_la_entrada_invertida(tabla, reloj):
    st, creado = llamar("POST /jobs", body={"input": "abc1"})
    assert st == 202 and set(creado) == {"jobId"}
    job_id = creado["jobId"]

    assert llamar("GET /jobs/{jobId}", job_id=job_id) == (200, {"jobId": job_id, "status": "queued", "output": None})

    reloj["ms"] += trabajos.ESPERA_MS  # 2 s después: listo (el verificador espera hasta 12 s)
    assert llamar("GET /jobs/{jobId}", job_id=job_id) == (200, {"jobId": job_id, "status": "done", "output": "1cba"})


def test_procesar_invierte_caracter_por_caracter():
    assert trabajos.procesar("abc1") == "1cba"
    assert trabajos.procesar("Piura-ñ7") == "7ñ-aruiP"


def test_trabajo_inexistente_o_id_de_item_404(tabla, reloj):
    assert llamar("GET /jobs/{jobId}", job_id="0" * 32)[0] == 404
    assert llamar("GET /jobs/{jobId}", job_id="no-es-un-id")[0] == 404
    _, item = llamar("POST /items", body={"value": "soy-un-item"})
    assert llamar("GET /jobs/{jobId}", job_id=item["id"])[0] == 404


@pytest.mark.parametrize("body", [{}, [1], {"input": ""}, {"input": 5}, {"input": "x" * 1025}])
def test_input_invalido_400_sin_guardar(tabla, body):
    assert llamar("POST /jobs", body=body)[0] == 400
    assert tabla.datos == {}
