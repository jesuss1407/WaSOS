"""Rutas del tablero (protegidas con X-Admin-Key): lista priorizada, estados, resumen, CSV y parte IA."""
import csv
import io
from collections import Counter, defaultdict

from datos import repositorio as repo
from dominio.catalogos import (DISTRITOS, ESTADOS, ESTADOS_ACTIVOS, NECESIDADES, NIVELES,
                               TIPOS, TRANSICIONES)
from dominio.validacion import ID_RE, ErrorValidacion, validar_cambio_estado
from ia.parte_situacional import generar_parte
from rutas.http import ErrorHttp, ahora_iso, leer_json, path_param, query, respuesta
from rutas.servicio import a_publico, ordenar, tipo_efectivo


def _a_admin(r: dict) -> dict:
    vista = dict(r)
    vista["tipo"] = tipo_efectivo(r)
    vista["foto_url"] = repo.url_lectura(r["foto_key"]) if r.get("foto_key") else None
    vista["transiciones"] = sorted(TRANSICIONES.get(r.get("estado"), set()))
    return vista


def listar(event):
    q = query(event)
    filtros = {"distrito": (q.get("distrito"), DISTRITOS), "tipo": (q.get("tipo"), TIPOS),
               "estado": (q.get("estado"), ESTADOS), "nivel": (q.get("nivel"), NIVELES)}
    for campo, (valor, validos) in filtros.items():
        if valor and valor not in validos:
            raise ErrorHttp(400, f"Filtro {campo} no válido")
    reportes = [r for r in repo.listar()
                if (not filtros["distrito"][0] or r["distrito"] == filtros["distrito"][0])
                and (not filtros["tipo"][0] or tipo_efectivo(r) == filtros["tipo"][0])
                and (not filtros["estado"][0] or r["estado"] == filtros["estado"][0])
                and (not filtros["nivel"][0] or r["nivel"] == filtros["nivel"][0])]
    return respuesta(200, [_a_admin(r) for r in ordenar(reportes)])


def actualizar(event):
    id_ = path_param(event, "id")
    if not ID_RE.match(id_):
        raise ErrorHttp(400, "id inválido")
    try:
        cambio = validar_cambio_estado(leer_json(event))
    except ErrorValidacion as e:
        raise ErrorHttp(400, "Datos inválidos", e.errores) from e
    try:
        actual = repo.obtener(id_)
    except repo.NoEncontrado as e:
        raise ErrorHttp(404, "Reporte no encontrado") from e
    permitidos = TRANSICIONES.get(actual["estado"], set())
    if cambio["estado"] not in permitidos:
        raise ErrorHttp(409, f"Transición no permitida: {actual['estado']} -> {cambio['estado']}",
                        {"permitidas": sorted(permitidos)})
    ahora = ahora_iso()
    entrada = {"estado": cambio["estado"], "fecha": ahora, "nota": cambio["nota"] or "",
               "brigada": cambio["brigada"] or ""}
    try:
        r = repo.cambiar_estado(id_, actual["estado"], cambio["estado"], cambio["brigada"], entrada, ahora)
    except repo.ConflictoEstado as e:
        raise ErrorHttp(409, "El reporte cambió mientras lo editaba; recargue") from e
    return respuesta(200, _a_admin(r))


def _agregar(reportes: list) -> dict:
    activos = [r for r in reportes if r.get("estado") in ESTADOS_ACTIVOS
               and (r.get("ia") or {}).get("es_valida", True)]
    por_distrito = defaultdict(lambda: {"total": 0, "niveles": Counter(), "necesidades": Counter(),
                                        "vulnerables": 0})
    for r in activos:
        d = por_distrito[r["distrito"]]
        d["total"] += 1
        d["niveles"][r["nivel"]] += 1
        d["necesidades"].update(r.get("necesidades", []))
        d["vulnerables"] += 1 if r.get("vulnerables") else 0
    distritos = []
    for nombre, d in por_distrito.items():
        distritos.append({
            "distrito": nombre,
            "total": d["total"],
            "vulnerables": d["vulnerables"],
            "niveles": {n: d["niveles"].get(n, 0) for n in NIVELES},
            "necesidades": dict(d["necesidades"].most_common()),
        })
    distritos.sort(key=lambda x: (x["niveles"]["CRÍTICA"], x["niveles"]["ALTA"], x["total"]), reverse=True)
    necesidades_total = Counter()
    for r in activos:
        necesidades_total.update(r.get("necesidades", []))
    return {
        "generado_en": ahora_iso(),
        "total": len(reportes),
        "total_activos": len(activos),
        "por_estado": {e: sum(1 for r in reportes if r.get("estado") == e) for e in ESTADOS},
        "por_nivel": {n: sum(1 for r in activos if r["nivel"] == n) for n in NIVELES},
        "por_distrito": distritos,
        "necesidades_total": {k: necesidades_total.get(k, 0) for k in NECESIDADES},
        "_activos": activos,
    }


def resumen(event):
    datos = _agregar(repo.listar())
    datos.pop("_activos")
    return respuesta(200, datos)


_COLUMNAS = ["id", "creado_en", "distrito", "lat", "lon", "tipo_usuario", "tipo_ia", "severidad",
             "es_valida", "riesgo_vida", "riesgo_salud", "prioridad", "nivel", "motivos",
             "necesidades", "vulnerables", "confirmaciones", "estado", "brigada", "descripcion",
             "estado_ia", "modelo", "origen"]


def _celda(valor) -> str:
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        return str(valor)  # números (lat/lon negativos) no son fórmulas
    texto = "" if valor is None else str(valor)
    # Evita inyección de fórmulas al abrir el CSV en Excel/Sheets
    return "'" + texto if texto[:1] in ("=", "+", "-", "@", "\t", "\r") else texto


def exportar_csv(event):
    salida = io.StringIO()
    w = csv.writer(salida)
    w.writerow(_COLUMNAS)
    for r in ordenar(repo.listar()):
        ia = r.get("ia") or {}
        w.writerow([_celda(v) for v in [
            r["id"], r["creado_en"], r["distrito"], r["lat"], r["lon"], r["tipo_usuario"],
            ia.get("tipo"), ia.get("severidad"), ia.get("es_valida"), ia.get("riesgo_vida"),
            ia.get("riesgo_salud"), r["prioridad"], r["nivel"], " | ".join(r.get("motivos", [])),
            " | ".join(r.get("necesidades", [])), r.get("vulnerables"), r.get("confirmaciones", 0),
            r["estado"], r.get("brigada"), r.get("descripcion"), ia.get("estado_ia"), ia.get("modelo"),
            r.get("origen")]])
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "text/csv; charset=utf-8",
                    "Content-Disposition": 'attachment; filename="wasos-reportes.csv"',
                    "Cache-Control": "no-store"},
        "body": "\ufeff" + salida.getvalue(),
    }


def parte_situacional(event):
    body = leer_json(event)
    distrito = body.get("distrito")
    if distrito and distrito not in DISTRITOS:
        raise ErrorHttp(400, "Distrito no válido")
    reportes = [r for r in repo.listar() if not distrito or r["distrito"] == distrito]
    agg = _agregar(reportes)
    top = ordenar(agg.pop("_activos"))[:10]
    datos = {
        "fecha": agg["generado_en"],
        "ambito": distrito or "Provincia de Piura y región",
        "total_activos": agg["total_activos"],
        "por_nivel": agg["por_nivel"],
        "top": [{**{k: v for k, v in a_publico(r).items()
                    if k in ("distrito", "nivel", "prioridad", "motivos", "estado")},
                 "tipo": TIPOS.get(tipo_efectivo(r), "Otro"),
                 "necesidades": [NECESIDADES[n] for n in r.get("necesidades", []) if n in NECESIDADES]}
                for r in top],
        "necesidades_por_distrito": {d["distrito"]: {NECESIDADES.get(k, k): v for k, v in d["necesidades"].items()}
                                     for d in agg["por_distrito"]},
    }
    return respuesta(200, generar_parte(datos))
