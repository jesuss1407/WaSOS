#!/usr/bin/env python3
"""Prueba E2E contra la API desplegada: POST /uploads -> PUT a S3 -> POST /reportes -> GET /reportes.

Uso: python3 scripts/smoke_test.py <API_URL> <foto.jpg> [--lat -5.1906 --lon -80.6558]
Solo usa la librería estándar.
"""
import argparse
import json
import time
import urllib.request


def pedir(metodo, url, cuerpo=None, headers=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    h = {"Content-Type": "application/json", **(headers or {})}
    req = urllib.request.Request(url, data=datos, method=metodo, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=35) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"null")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("api")
    ap.add_argument("foto")
    ap.add_argument("--lat", type=float, default=-5.1906)   # cerca del óvalo Dos Grifos
    ap.add_argument("--lon", type=float, default=-80.6558)
    ap.add_argument("--tipo", default="aniego_via")
    a = ap.parse_args()
    api = a.api.rstrip("/")

    st, up = pedir("POST", f"{api}/uploads", {"content_type": "image/jpeg"})
    assert st == 200, (st, up)
    with open(a.foto, "rb") as f:
        foto = f.read()
    req = urllib.request.Request(up["upload_url"], data=foto, method="PUT", headers={"Content-Type": "image/jpeg"})
    with urllib.request.urlopen(req, timeout=30) as r:
        assert r.status == 200, r.status
    print(f"Foto subida: {up['foto_key']} ({len(foto) // 1024} KB)")

    t = time.time()
    st, rep = pedir("POST", f"{api}/reportes", {
        "foto_key": up["foto_key"], "lat": a.lat, "lon": a.lon, "distrito": "Veintiséis de Octubre",
        "tipo": a.tipo, "descripcion": "Prueba E2E: calle anegada", "vulnerables": True,
        "necesidades": ["motobomba"], "consentimiento": True})
    print(f"POST /reportes -> {st} en {time.time() - t:.1f} s")
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    assert st == 201, st

    st, lista = pedir("GET", f"{api}/reportes")
    assert st == 200
    print(f"GET /reportes -> {len(lista)} reportes; nuevo visible: {any(r['id'] == rep['id'] for r in lista)}")


if __name__ == "__main__":
    main()
