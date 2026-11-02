#!/usr/bin/env python3
"""Carga los reportes demo de data/seed_reportes.json en DynamoDB, con la misma fórmula de prioridad de la API.

Uso: python scripts/seed.py --tabla <TablaReportes> [--region us-east-1]
Idempotente: los ids se derivan del índice (uuid5), volver a correrlo sobrescribe los mismos reportes.
"""
import argparse
import json
import sys
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "backend" / "src"))

import boto3  # noqa: E402

from datos.repositorio import a_dynamo  # noqa: E402
from rutas.servicio import calcular_para  # noqa: E402

NS = uuid.UUID("6f1f2b9e-6c43-4a4e-9a51-0f6f6a1c2026")


def construir(i: int, s: dict) -> dict:
    historial = [{"estado": "nuevo", "fecha": s["creado_en"], "nota": "Reporte ciudadano (demo)"}]
    if s["estado"] in ("verificado", "en_atencion", "resuelto"):
        historial.append({"estado": "verificado", "fecha": s["creado_en"], "nota": "Verificado por operador (demo)"})
    if s["estado"] in ("en_atencion", "resuelto"):
        historial.append({"estado": "en_atencion", "fecha": s["creado_en"], "nota": "", "brigada": s.get("brigada") or ""})
    if s["estado"] == "resuelto":
        historial.append({"estado": "resuelto", "fecha": s["creado_en"], "nota": "Aniego evacuado (demo)"})
    r = {
        "id": uuid.uuid5(NS, f"seed-{i}").hex,
        "creado_en": s["creado_en"],
        "actualizado_en": s["creado_en"],
        "lat": s["lat"],
        "lon": s["lon"],
        "distrito": s["distrito"],
        "tipo_usuario": s["tipo"],
        "descripcion": s.get("descripcion", ""),
        "vulnerables": s["vulnerables"],
        "necesidades": s["necesidades"],
        "foto_key": None,
        "ia": {**s["ia"], "confianza": 0.0, "modelo": None, "estado_ia": "demo"},
        "confirmaciones": s["confirmaciones"],
        "estado": s["estado"],
        "brigada": s.get("brigada"),
        "historial": historial,
        "origen": "demo",
    }
    r.update(calcular_para(r))
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tabla", required=True)
    ap.add_argument("--region", default="us-east-1")
    a = ap.parse_args()
    seeds = json.loads((RAIZ / "data" / "seed_reportes.json").read_text(encoding="utf-8"))
    tabla = boto3.resource("dynamodb", region_name=a.region).Table(a.tabla)
    with tabla.batch_writer() as bw:
        for i, s in enumerate(seeds):
            r = construir(i, s)
            bw.put_item(Item=a_dynamo(r))
            print(f"{r['nivel']:8} {r['prioridad']:3}  {r['distrito']:22} {r['tipo_usuario']}")
    print(f"{len(seeds)} reportes demo cargados en {a.tabla}")


if __name__ == "__main__":
    main()
