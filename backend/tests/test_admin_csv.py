import os

os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from rutas.admin import _celda  # noqa: E402


def test_celda_neutraliza_formulas_en_texto():
    assert _celda("=HYPERLINK(\"http://x\")").startswith("'")
    assert _celda("+51 999").startswith("'")
    assert _celda("@SUM(A1)").startswith("'")


def test_celda_no_altera_numeros_ni_texto_normal():
    assert _celda(-5.1968) == "-5.1968"
    assert _celda(82) == "82"
    assert _celda("Dren lleno") == "Dren lleno"
    assert _celda(None) == ""
