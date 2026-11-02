"""El contrato (.kiro/steering/api-contract.md) es la fuente de verdad: rutas y enums deben coincidir en todas partes."""
import re
from pathlib import Path

import app
from dominio import catalogos as c

RAIZ = Path(__file__).resolve().parents[2]
CONTRATO = (RAIZ / ".kiro" / "steering" / "api-contract.md").read_text(encoding="utf-8")


def rutas_contrato() -> set:
    return {f"{m} {p}" for m, p in re.findall(r"^\| (GET|POST|PATCH) \| `([^`]+)`", CONTRATO, re.M)}


def rutas_template() -> set:
    tpl = (RAIZ / "backend" / "template.yaml").read_text(encoding="utf-8")
    pares = re.findall(r'Path: ("?/[^,]+?"?), Method: (\w+)', tpl)
    return {f"{metodo} {ruta.strip(chr(34))}" for ruta, metodo in pares}


def enum_contrato(nombre: str) -> list:
    return [x.strip() for x in re.search(rf"\*\*{nombre}:\*\* `([^`]+)`", CONTRATO).group(1).split(",")]


def claves_js(nombre: str) -> list:
    js = (RAIZ / "frontend" / "src" / "catalogos.js").read_text(encoding="utf-8")
    cuerpo = re.search(rf"export const {nombre} = \{{(.*?)\n\}}", js, re.S).group(1)
    return re.findall(r"^\s+'?([\w]+)'?:", cuerpo, re.M)


def test_rutas_contrato_app_y_template_alineadas():
    assert len(rutas_contrato()) == 15
    assert rutas_contrato() == set(app.RUTAS) == rutas_template()


def test_rutas_del_contrato_existen_en_api_js():
    js = re.sub(r"\$\{(\w+)\}", r"{\1}", (RAIZ / "frontend" / "src" / "api.js").read_text(encoding="utf-8"))
    for ruta in rutas_contrato():
        assert f"'{ruta.split(' ', 1)[1]}" in js or f"`{ruta.split(' ', 1)[1]}" in js, ruta


def test_enums_alineados_contrato_backend_frontend():
    assert enum_contrato("tipo") == list(c.TIPOS) == claves_js("TIPOS")
    assert enum_contrato("necesidades") == list(c.NECESIDADES) == claves_js("NECESIDADES")
    assert enum_contrato("distrito") == c.DISTRITOS
    estados = re.search(r"\*\*estado:\*\* `([^`]+)`", CONTRATO).group(1)
    assert set(re.findall(r"[a-z_]+", estados)) - {"brigada"} == set(c.ESTADOS) == set(claves_js("ESTADOS"))
