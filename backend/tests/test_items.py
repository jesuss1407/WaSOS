"""Insignia "Persistencia" (Kiro IAthon): POST /items, GET /items/{id} y GET /items con una tabla falsa."""
import json

import pytest

import app

# `tabla`: ItemsTable falsa con scan paginado (conftest.py)


def llamar(ruta, body=None, id_=None):
    r = app.handler({"routeKey": ruta, "headers": {}, "body": json.dumps(body) if body is not None else None,
                     "pathParameters": {"id": id_} if id_ else None, "isBase64Encoded": False}, None)
    assert r["headers"]["Content-Type"].startswith("application/json")
    return r["statusCode"], json.loads(r["body"])


def test_crear_obtener_y_listar_item(tabla):
    st, creado = llamar("POST /items", body={"value": "nonce-abc123"})
    assert st == 201 and creado["value"] == "nonce-abc123" and set(creado) == {"id", "value"}

    assert llamar("GET /items/{id}", id_=creado["id"]) == (200, creado)

    st, lista = llamar("GET /items")
    assert st == 200 and creado in lista


def test_listar_pagina_el_scan_y_devuelve_hasta_100_con_el_mas_reciente(tabla, monkeypatch):
    for i in range(150):
        tabla.put_item(Item={"id": f"{i:032x}", "value": f"v{i}", "creado_en": f"2026-10-30T10:00:{i:03d}"})
    _, nuevo = llamar("POST /items", body={"value": "recien-creado"})

    st, lista = llamar("GET /items")
    assert st == 200 and len(lista) == 100
    assert lista[0] == nuevo  # el más reciente primero, aunque el scan lo devuelva en otra página
    assert tabla.scans > 1    # recorrió varias páginas, no solo la primera


def test_item_inexistente_404(tabla):
    assert llamar("GET /items/{id}", id_="0" * 32)[0] == 404
    assert llamar("GET /items/{id}", id_="no-es-un-id")[0] == 404


def test_trabajos_de_jobs_no_salen_por_items(tabla):
    tabla.put_item(Item={"id": "a" * 32, "tipo": "job", "input": "x", "creado_en": "2026-10-30T23:00:00", "listo_en": 0})
    _, creado = llamar("POST /items", body={"value": "solo-yo"})
    assert llamar("GET /items") == (200, [creado])
    assert llamar("GET /items/{id}", id_="a" * 32)[0] == 404


@pytest.mark.parametrize("body", [{}, [1], {"value": ""}, {"value": 123}, {"value": "x" * 1025}])
def test_value_invalido_400_sin_guardar(tabla, body):
    assert llamar("POST /items", body=body)[0] == 400
    assert tabla.datos == {}
