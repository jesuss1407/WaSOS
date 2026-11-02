"""Integración del handler con DynamoDB y S3 simulados (moto). La IA se simula: no hay llamadas a Bedrock."""
import csv
import io
import json
import os
import uuid

import boto3
import pytest

import app
from datos import repositorio as repo
from ia import clasificador

CLAVE = os.environ["ADMIN_KEY"]
DOS_GRIFOS = (-5.190612, -80.655834)  # 6 decimales: el mapa público debe redondear a 4
IA_OK = {"tipo": "aniego_via", "severidad": 4, "es_valida": True, "riesgo_vida": False, "riesgo_salud": True,
         "descripcion": "Vía anegada de lado a lado", "confianza": 0.9, "modelo": "simulado", "estado_ia": "ok"}


def evento(ruta, body=None, id_=None, query=None, clave=None):
    headers = {"content-type": "application/json"}
    if clave:
        headers["x-admin-key"] = clave
    return {"routeKey": ruta, "headers": headers, "body": json.dumps(body) if body is not None else None,
            "pathParameters": {"id": id_} if id_ else None, "queryStringParameters": query,
            "isBase64Encoded": False}


def llamar(ruta, **kw):
    r = app.handler(evento(ruta, **kw), None)
    es_json = r["headers"]["Content-Type"].startswith("application/json")
    return r["statusCode"], (json.loads(r["body"]) if es_json else r["body"])


def subir_foto() -> str:
    key = f"fotos/{uuid.uuid4().hex}.jpg"
    boto3.client("s3").put_object(Bucket="fotos-test", Key=key, Body=b"\xff\xd8\xff\xe0prueba", ContentType="image/jpeg")
    return key


def cuerpo(foto_key, **extra):
    return {"foto_key": foto_key, "lat": DOS_GRIFOS[0], "lon": DOS_GRIFOS[1], "distrito": "Veintiséis de Octubre",
            "tipo": "aniego_via", "descripcion": "Calle anegada frente al colegio", "vulnerables": True,
            "necesidades": ["motobomba"], "consentimiento": True, **extra}


def patch(id_, **cambio):
    return llamar("PATCH /admin/reportes/{id}", id_=id_, body=cambio, clave=CLAVE)


@pytest.fixture
def ia_ok(monkeypatch):
    monkeypatch.setattr(clasificador, "clasificar", lambda *a, **k: dict(IA_OK))


@pytest.fixture
def reporte(aws, ia_ok):
    st, r = llamar("POST /reportes", body=cuerpo(subir_foto()))
    assert st == 201
    return r


# ---------- Reporte ciudadano ----------

def test_uploads_entrega_url_prefirmada_y_solo_acepta_jpeg(aws):
    st, r = llamar("POST /uploads", body={"content_type": "image/jpeg"})
    assert st == 200 and r["foto_key"].startswith("fotos/") and "X-Amz-Signature" in r["upload_url"]
    assert llamar("POST /uploads", body={"content_type": "image/png"})[0] == 400


def test_si_bedrock_falla_el_reporte_se_guarda_con_fallback(aws, monkeypatch):
    def bedrock_caido():
        raise RuntimeError("Bedrock no disponible")
    monkeypatch.setattr(clasificador, "_get_cliente", bedrock_caido)
    st, r = llamar("POST /reportes", body=cuerpo(subir_foto()))
    assert st == 201
    assert "IA no disponible: verificar manualmente" in r["motivos"]
    assert any(m.endswith("m de zona crítica: Óvalo Dos Grifos") for m in r["motivos"])
    guardado = repo.obtener(r["id"])
    assert guardado["ia"]["estado_ia"] == "fallback" and guardado["estado"] == "nuevo"


def test_reenviar_el_mismo_foto_key_no_duplica(aws, ia_ok):
    key = subir_foto()
    st1, r1 = llamar("POST /reportes", body=cuerpo(key))
    st2, r2 = llamar("POST /reportes", body=cuerpo(key))
    assert (st1, st2) == (201, 200) and r1["id"] == r2["id"] and len(repo.listar()) == 1


def test_reporte_fuera_de_piura_400_sin_guardar(aws, ia_ok):
    st, r = llamar("POST /reportes", body=cuerpo(subir_foto(), lat=-12.05, lon=-77.04))
    assert st == 400 and "ubicacion" in r["detalles"] and repo.listar() == []


def test_reporte_sin_foto_subida_400(aws, ia_ok):
    assert llamar("POST /reportes", body=cuerpo("fotos/" + "0" * 32 + ".jpg"))[0] == 400


# ---------- Mapa público ----------

def test_mapa_publico_sin_datos_sensibles_y_coordenadas_redondeadas(reporte):
    st, lista = llamar("GET /reportes")
    assert st == 200 and len(lista) == 1
    for campo in ("foto_key", "foto_url", "descripcion", "historial", "brigada", "tipo_usuario"):
        assert campo not in lista[0]
    assert (lista[0]["lat"], lista[0]["lon"]) == (-5.1906, -80.6558)


def test_mapa_publico_oculta_fotos_no_validas_y_descartados(aws, monkeypatch):
    monkeypatch.setattr(clasificador, "clasificar", lambda *a, **k: {**IA_OK, "es_valida": False, "severidad": 1})
    st, r = llamar("POST /reportes", body=cuerpo(subir_foto()))
    assert st == 201 and r["prioridad"] <= 20
    monkeypatch.setattr(clasificador, "clasificar", lambda *a, **k: dict(IA_OK))
    _, otro = llamar("POST /reportes", body=cuerpo(subir_foto()))
    assert patch(otro["id"], estado="descartado")[0] == 200
    assert llamar("GET /reportes")[1] == []


# ---------- Tablero ----------

def test_admin_sin_clave_o_con_clave_incorrecta_401(aws):
    assert llamar("GET /admin/reportes")[0] == 401
    assert llamar("GET /admin/reportes", clave="no-es-la-clave")[0] == 401


def test_admin_lista_con_foto_prefirmada_y_transiciones(reporte):
    st, lista = llamar("GET /admin/reportes", clave=CLAVE)
    assert st == 200 and "X-Amz-Signature" in lista[0]["foto_url"]
    assert lista[0]["transiciones"] == ["descartado", "verificado"]


def test_flujo_de_estados_completo_con_historial(reporte):
    id_ = reporte["id"]
    assert patch(id_, estado="verificado")[0] == 200
    st, r = patch(id_, estado="en_atencion", brigada="Brigada MPP 03")
    assert st == 200 and r["brigada"] == "Brigada MPP 03"
    st, r = patch(id_, estado="resuelto", nota="Aniego evacuado")
    assert st == 200 and r["transiciones"] == []
    assert [h["estado"] for h in r["historial"]] == ["nuevo", "verificado", "en_atencion", "resuelto"]


def test_transicion_no_permitida_409(reporte):
    st, r = patch(reporte["id"], estado="resuelto")
    assert st == 409 and r["detalles"]["permitidas"] == ["descartado", "verificado"]


def test_en_atencion_exige_brigada_400(reporte):
    patch(reporte["id"], estado="verificado")
    st, r = patch(reporte["id"], estado="en_atencion")
    assert st == 400 and "brigada" in r["detalles"]


def test_edicion_concurrente_409_no_pisa_el_cambio_ajeno(reporte, monkeypatch):
    id_ = reporte["id"]
    obtener_real = repo.obtener
    lectura_vieja = obtener_real(id_)                 # el operador B abrió el reporte cuando estaba "nuevo"
    assert patch(id_, estado="verificado")[0] == 200  # el operador A lo verifica primero
    monkeypatch.setattr(repo, "obtener", lambda _id: lectura_vieja)
    st, r = patch(id_, estado="descartado")           # B intenta descartar con su lectura vieja
    assert st == 409 and r["error"] == "El reporte cambió mientras lo editaba; recargue"
    assert obtener_real(id_)["estado"] == "verificado"


def test_cambiar_estado_con_estado_esperado_viejo_lanza_conflicto(reporte):
    entrada = {"estado": "verificado", "fecha": "2026-10-30T12:00:00+00:00", "nota": ""}
    repo.cambiar_estado(reporte["id"], "nuevo", "verificado", None, entrada, entrada["fecha"])
    with pytest.raises(repo.ConflictoEstado):
        repo.cambiar_estado(reporte["id"], "nuevo", "descartado", None, entrada, entrada["fecha"])


def test_resumen_agrega_necesidades_por_distrito(reporte):
    st, r = llamar("GET /admin/resumen", clave=CLAVE)
    d = next(x for x in r["por_distrito"] if x["distrito"] == "Veintiséis de Octubre")
    assert st == 200 and d["necesidades"] == {"motobomba": 1} and d["vulnerables"] == 1


def test_export_csv_neutraliza_formulas_y_conserva_numeros(aws, ia_ok):
    malicioso = '=HYPERLINK("http://malicioso.example","clic")'
    llamar("POST /reportes", body=cuerpo(subir_foto(), descripcion=malicioso))
    r = app.handler(evento("GET /admin/export.csv", clave=CLAVE), None)
    assert r["statusCode"] == 200 and r["headers"]["Content-Type"].startswith("text/csv")
    assert r["body"].startswith("\ufeff")
    fila = next(csv.DictReader(io.StringIO(r["body"].lstrip("\ufeff"))))
    assert fila["descripcion"] == "'" + malicioso
    assert (fila["lat"], fila["lon"]) == ("-5.190612", "-80.655834")


# ---------- "Yo también lo veo" (S1) ----------

def test_confirmar_suma_y_recalcula_prioridad(reporte):
    id_ = reporte["id"]
    llamar("POST /reportes/{id}/confirmar", id_=id_)
    st, r = llamar("POST /reportes/{id}/confirmar", id_=id_)
    assert st == 200 and r["confirmaciones"] == 2 and "2 vecinos confirman" in r["motivos"]
    assert r["prioridad"] > reporte["prioridad"] and repo.obtener(id_)["prioridad"] == r["prioridad"]


def test_confirmacion_retrasada_no_pisa_la_prioridad_mas_reciente(reporte):
    id_ = reporte["id"]
    llamar("POST /reportes/{id}/confirmar", id_=id_)
    _, r2 = llamar("POST /reportes/{id}/confirmar", id_=id_)
    # escritura tardía de la primera confirmación (calculada con 1): se descarta
    assert repo.actualizar_prioridad(id_, 1, "BAJA", ["calculo viejo"], confirmaciones=1) is False
    assert repo.obtener(id_)["prioridad"] == r2["prioridad"]


def test_confirmar_reporte_descartado_409(reporte):
    patch(reporte["id"], estado="descartado")
    assert llamar("POST /reportes/{id}/confirmar", id_=reporte["id"])[0] == 409
