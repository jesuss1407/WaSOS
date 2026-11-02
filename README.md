# WaSOS · mapa ciudadano de riesgo FEN en Piura

> El proyecto se llamaba **Alerta Piura** hasta el 30-oct-2026. Los recursos de AWS conservan el nombre anterior
> (stack `alerta-piura`, buckets y tabla) para no cambiar la URL de la API ni perder datos. Ver "Decisiones".

Web móvil para que vecinos de Piura reporten puntos críticos del Fenómeno El Niño costero con una foto, sin
registrarse. Claude (Amazon Bedrock) clasifica la foto, el backend calcula una prioridad 0-100 con motivos visibles y
las autoridades atienden desde un tablero priorizado con panel de necesidades por distrito.

## URLs (desplegado el 30-oct-2026, us-east-1)
| Qué | URL |
|---|---|
| Reportar (vecino) | https://main.d2z9k6uh1qqa6x.amplifyapp.com/ |
| Mapa público | https://main.d2z9k6uh1qqa6x.amplifyapp.com/mapa |
| Tablero (autoridades) | https://main.d2z9k6uh1qqa6x.amplifyapp.com/tablero |
| API | https://splg8tml5k.execute-api.us-east-1.amazonaws.com |

La clave del tablero está en `backend/.admin-key` (no se versiona). Se envía en el header `X-Admin-Key`.

## Estado del alcance
| ID | Funcionalidad | Estado | Dónde |
|---|---|---|---|
| M1 | Reporte sin login: cámara, GPS con pin ajustable, distrito autodetectado, tipo, descripción, vulnerables, necesidades, consentimiento Ley 29733 | ✅ | `frontend/src/pages/Reportar.jsx` |
| M2 | Clasificación IA de la foto con salida JSON validada y fallback | ✅ | `backend/src/ia/clasificador.py` |
| M3 | Prioridad 0-100, nivel y motivos legibles | ✅ | `backend/src/dominio/prioridad.py` |
| M4 | Mapa público OSM, solo reportes válidos, color por nivel, sin fotos | ✅ | `frontend/src/pages/Mapa.jsx` |
| M5 | Tablero con clave: lista priorizada + mapa, filtros, foto, estados, necesidades por distrito | ✅ | `frontend/src/pages/Tablero.jsx` |
| M6 | Datos demo: 10 distritos, 9 zonas críticas con fuente, 26 reportes | ✅ | `data/` |
| S1 | "Yo también lo veo" con recálculo de prioridad | ✅ | `POST /reportes/{id}/confirmar` |
| S2 | Exportar CSV (protegido contra inyección de fórmulas) | ✅ | `GET /admin/export.csv` |
| S3 | Parte situacional IA para el COER | ✅ | `POST /admin/parte-situacional` |
| S4 | Cola offline en localStorage con reintento idempotente | ✅ | `frontend/src/lib/colaOffline.js` |

## Arquitectura
```
Celular ── React + Vite (Amplify Hosting) ── Leaflet + OpenStreetMap
   │ 1) POST /uploads ──────────► URL prefirmada PUT (5 min)
   │ 2) PUT foto JPEG ≤300 KB ──► S3 privado fotos/{uuid}.jpg (canvas elimina EXIF)
   │ 3) POST /reportes ─────────► API Gateway HTTP API (CORS, 20 rps / burst 50)
   ▼
Lambda Python 3.12 "api" (router único)
   ├─ ia/clasificador.py ── Bedrock Mantle: Claude Sonnet 5 (respaldo Opus 4.8), messages.parse + Pydantic
   ├─ dominio/prioridad.py ── fórmula + distancia a zonas críticas (haversine ≤300 m)
   └─ DynamoDB "Reportes" (on-demand, PITR)
IaC: AWS SAM (backend/template.yaml) · Logs: CloudWatch (JSON, 30 días)
```
Contrato de API, modelo de datos y enums: [`.kiro/steering/api-contract.md`](.kiro/steering/api-contract.md).

## Desplegar
Requisitos: AWS CLI v2 con credenciales, SAM CLI, Python 3.12, Node 20+.
```bash
TEAM_ID=T051 scripts/deploy_backend.sh   # sam build + sam deploy (genera backend/.admin-key la primera vez)
uv run --python 3.12 --with boto3 python scripts/seed.py --tabla <TablaReportes>   # datos demo
scripts/deploy_frontend.sh         # npm build + deploy manual en Amplify Hosting
```
Si cambia la URL de la API, actualizar `frontend/.env.production`.

## Probar
```bash
cd backend && uv run --python 3.12 --with-requirements requirements-dev.txt pytest -q tests   # 94 tests, ~3 s, sin AWS real
cd frontend && npm test                                                                      # 4 tests (node --test)
curl -s https://splg8tml5k.execute-api.us-east-1.amazonaws.com/health                         # {"status": "ok", "team": "T051"}
python3 scripts/smoke_test.py https://splg8tml5k.execute-api.us-east-1.amazonaws.com foto.jpg   # E2E contra la API real
uv run --python 3.12 --with "anthropic[bedrock]" --with pillow python scripts/check_bedrock.py  # acceso a modelos
```
Los tests de integración usan DynamoDB y S3 simulados con moto y credenciales falsas (`tests/conftest.py`), así que
no pueden tocar la cuenta real. La IA se simula, incluido el caso de Bedrock caído.

Verificado el 30-oct-2026: E2E con foto real → `inundacion_vivienda`, severidad 4, prioridad 82 CRÍTICA
("A 25 m de zona crítica: Óvalo Dos Grifos", "Personas vulnerables", "Riesgo sanitario"). Prueba de navegador
(Chromium headless, viewport móvil con GPS simulado) de Reportar → Mapa → Tablero sin errores de consola.

## Evidencias de las reglas clave
| Regla | Implementación | Prueba |
|---|---|---|
| Bbox región Piura (lat −6,4…−4,0; lon −81,4…−79,2) | `backend/src/dominio/validacion.py` → `validar_reporte`; cliente: `frontend/src/lib/geo.js` → `dentroDeRegion` (también al tocar o arrastrar el pin) | `test_geo.py::test_bbox_region_piura`, `test_bbox_y_radio_del_frontend_iguales_al_backend`, `test_api_integracion.py::test_reporte_fuera_de_piura_400_sin_guardar`, `geo.test.js` |
| Distrito autodetectado por cercanía al centroide (≤25 km, si no "Otro (región)") | `frontend/src/lib/geo.js` → `distritoMasCercano` (lo usa `Reportar.jsx`); espejo en `backend/src/dominio/geo.py` → `distrito_mas_cercano` | `test_geo.py::test_distrito_mas_cercano` (10 casos), `geo.test.js` |
| Bloqueo optimista en `PATCH /admin/reportes/{id}` | `backend/src/datos/repositorio.py` → `cambiar_estado`: `ConditionExpression="estado = :actual"` → `ConflictoEstado` → 409 en `rutas/admin.py::actualizar` | `test_api_integracion.py::test_edicion_concurrente_409_no_pisa_el_cambio_ajeno`, `test_cambiar_estado_con_estado_esperado_viejo_lanza_conflicto` |
| Confirmaciones simultáneas (S1) sin prioridad vieja | `repositorio.py` → `incrementar_confirmaciones` (`ADD` atómico) + `actualizar_prioridad` condicionada a `confirmaciones = :c` | `test_confirmacion_retrasada_no_pisa_la_prioridad_mas_reciente` |
| CSV sin inyección de fórmulas (S2) | `backend/src/rutas/admin.py` → `_celda` (antepone `'` a textos que empiezan con `= + - @`, tab o CR; los números pasan intactos) usada por `exportar_csv` | `test_admin_csv.py`, `test_api_integracion.py::test_export_csv_neutraliza_formulas_y_conserva_numeros` |
| Fallback si Bedrock falla (M2) | `backend/src/ia/clasificador.py` → `clasificar` / `fallback` | `test_si_bedrock_falla_el_reporte_se_guarda_con_fallback` |
| Mapa público sin datos sensibles (M4) | `backend/src/rutas/servicio.py` → `a_publico` | `test_mapa_publico_sin_datos_sensibles_y_coordenadas_redondeadas` |
| Rutas y enums alineados con el contrato | `.kiro/steering/api-contract.md` | `test_contrato.py` (contrato = `app.py` = `template.yaml` = `api.js`; enums backend = frontend) |

Fragmento del bloqueo optimista (`repositorio.cambiar_estado`):
```python
resp = _tabla().update_item(Key={"id": id_}, UpdateExpression=expr,
                            ConditionExpression="estado = :actual", ...)   # el estado no cambió desde la lectura
except ClientError as e:
    if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
        raise ConflictoEstado(id_)   # → 409 "El reporte cambió mientras lo editaba; recargue"
```

## Hooks de Kiro (`.kiro/hooks/`)
Formato v1 de Kiro IDE 1.0: `trigger` + `matcher` + `action`. Es el reemplazo documentado del antiguo `when`/`then`
de los archivos `.kiro.hook`: "the `when`/`then` structure becomes `trigger`/`matcher`/`action`"
([Kiro IDE 1.0, Hooks](https://kiro.dev/docs/ide/whats-new-v1/hooks.md)).
| Archivo | Cuando (trigger + matcher) | Entonces (action) |
|---|---|---|
| `pytest-backend.json` | `PostFileSave` de un archivo que cumple `backend/.*\.py$` | `command`: `pytest -q tests` (94 tests) |
| `revisar-contrato-api.json` | `PostFileSave` de `.kiro/steering/api-contract.md` | `agent`: revisa rutas, eventos SAM, `api.js` y enums; puede correr `tests/test_contrato.py` |
| `revisar-tasks-spec.kiro.hook` | `when`: `fileEdited` en `.kiro/specs/*/{requirements,design,tasks}.md` | `then`: `askAgent` revisa que `tasks.md` cubra cada requisito con archivo y test reales |

Los triggers de archivo se disparan con los cambios que hace el agente. Si editas a mano, corre los tests tú mismo.

## Insignia "API viva" (Kiro IAthon)
`GET /health` es pública y responde 200 con `{"status": "ok", "team": "T051"}`. El valor de `team` sale del
parámetro `TeamId` de `backend/template.yaml`, que llega a la Lambda como `TEAM_ID`; `scripts/deploy_backend.sh` exige
la variable `TEAM_ID` para no desplegar con un id equivocado. Código: `rutas/publicas.py` → `salud`. Prueba:
`tests/test_health.py`. En el portal, la `ApiUrl` (sin barra final) va en "Perfil del equipo".

## Insignia "Persistencia" (Kiro IAthon)
Rutas públicas: `POST /items` (`{"value": "..."}` → 201 `{"id", "value"}`), `GET /items/{id}` (200 o 404) y
`GET /items` (arreglo con hasta 100 ítems, los más recientes primero). Se guardan en `ItemsTable`, una tabla aparte de
`Reportes` (env `TABLE_NAME`), y la Lambda solo tiene `PutItem`, `GetItem` y `Scan` sobre ella. El listado recorre
todas las páginas del scan y ordena por `creado_en` antes de recortar, porque el scan no tiene orden y cortar antes
podría dejar fuera el ítem recién creado. Código: `rutas/items.py` y `datos/items.py`. Prueba: `tests/test_items.py`
(tabla falsa con `monkeypatch` de `datos.items.TABLE`, scan paginado de 2 en 2).

## Insignia "Asíncrono o agente" (Kiro IAthon)
Rutas públicas: `POST /jobs` (`{"input": "..."}` → 202 `{"jobId"}`) y `GET /jobs/{jobId}` →
`{"jobId", "status": "queued" | "done", "output"}`. El trabajo se guarda en `ItemsTable` con `tipo = "job"` y
`listo_en` = creación + 2 s, y se resuelve al leer: desde `listo_en` responde `done` con el `input` invertido carácter
por carácter (`"abc1"` → `"1cba"`). Sin colas ni procesos extra. `/items` ignora los trabajos (no tienen `value`).
Código: `dominio/trabajos.py` (puro) y `rutas/trabajos.py`. Prueba: `tests/test_jobs.py` (tabla falsa y reloj simulado).
Verificado en producción el 30-oct-2026: `done` a los 3,2 s de crear el trabajo (el verificador espera hasta 12 s).

## Decisiones y diferencias con `plan.md`
- **Nombre:** el proyecto pasó de "Alerta Piura" a **WaSOS** (30-oct-2026). Cambió todo lo visible: título, manifest,
  barra superior, nombre del CSV (`wasos-*.csv`) y la línea "Fuente" del parte situacional. Se mantienen a propósito:
  el stack `alerta-piura` y sus recursos (renombrarlos crea otra `ApiUrl` y deja atrás los datos) y las claves de
  `localStorage` `alerta-piura:*` (renombrarlas perdería los reportes en cola offline de los celulares).
  `plan.md` conserva el nombre original como registro histórico.
- **Modelo:** `anthropic.claude-opus-5-5` respondió 529 (overloaded) en la cuenta; se usa `anthropic.claude-sonnet-5`
  (~3 s) con `anthropic.claude-opus-4-8` de respaldo, como prevé el plan. Configurable con el parámetro `ModelIds`.
- **Permisos de la cuenta:** se niega `s3:PutBucketPublicAccessBlock`. El bucket queda privado por los valores por
  defecto de S3 y SAM usa un bucket de artefactos propio (`alerta-piura-artefactos-<cuenta>`).
- **Zonas críticas:** 9 en lugar de ~12, solo las que tienen fuente citable. Las coordenadas son aproximadas
  (`coordenada_aproximada: true`); "Óvalo Dos Grifos" no figura en OSM y está marcada `verificada_osm: false`.
- **Datos demo:** los 26 reportes de `seed_reportes.json` no tienen foto (`origen: "demo"`, `estado_ia: "demo"`). Los
  reportes con foto del tablero se crearon en las pruebas E2E con una foto de dominio público de FEMA (no es Piura).
- **`tasks.md`:** el plan pedía generarlos en Kiro; aquí documentan las tareas ya implementadas con trazabilidad a requisitos.
- **Sin service worker:** la cola offline cubre el caso crítico (enviar sin señal) con menos riesgo.

## Privacidad y seguridad
Sin nombre ni teléfono · consentimiento explícito (Ley 29733) · EXIF eliminado en el navegador · fotos solo en el
tablero con URL de 15 min · mapa público sin fotos ni texto libre y con coordenadas a 4 decimales · validación de
entrada en la Lambda · clave admin con comparación en tiempo constante · CORS restringido · throttling.

## Más documentación
- [`docs/ALCANCE.md`](docs/ALCANCE.md): investigación, decisiones, pitch y guion de demo.
- [`docs/KIRO-PLAYBOOK.md`](docs/KIRO-PLAYBOOK.md): cómo se usó Kiro (steering, specs, hooks).
- Specs: [`.kiro/specs/`](.kiro/specs/) (01 backend, 02 IA, 03 frontend, 04 insignias de la IAthon) ·
  Steering: [`.kiro/steering/`](.kiro/steering/)
