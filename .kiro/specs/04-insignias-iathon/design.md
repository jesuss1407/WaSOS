# Diseño: 04 Insignias técnicas de la Kiro IAthon

Contrato: #[[file:.kiro/steering/api-contract.md]] · Requisitos: `requirements.md` de esta carpeta.

## Arquitectura mínima en AWS (us-east-1, stack `alerta-piura`)
```
Verificador del portal ──HTTPS──► API Gateway HTTP API (CORS, throttling 20 rps / burst 50)
                                   │ GET /health · POST|GET /items · GET /items/{id} · POST /jobs · GET /jobs/{jobId}
                                   ▼
                          Lambda "api" (Python 3.12, router por routeKey en app.py)
                                   │ env TEAM_ID (parámetro TeamId) · env TABLE_NAME
                                   ▼
                          DynamoDB ItemsTable (on-demand, PK id)   ← separada de Reportes (R4.2)
```
No se agregan servicios: se reutilizan la HTTP API y la Lambda de la spec 01. Sin colas, sin Step Functions.

| Recurso (`backend/template.yaml`) | Cambio | Requisitos |
|---|---|---|
| Parámetro `TeamId` | `Type: String`, `MinLength: 1`, sin default → env `TEAM_ID` | R1.2 |
| `ItemsTable` | `AWS::DynamoDB::Table`, `PAY_PER_REQUEST`, PK `id` (S) → env `TABLE_NAME`, salida `TablaItems` | R2.1, R3.1 |
| `ApiFunction` | Política `ItemsSoloCrearLeerListar`: `PutItem`, `GetItem`, `Scan` sobre `ItemsTable.Arn` | R4.3 |
| Eventos HttpApi | `Salud`, `CrearItem`, `ObtenerItem`, `ListarItems`, `CrearTrabajo`, `ObtenerTrabajo` | R4.4 |

## Componentes
- `rutas/publicas.py` → `salud`: `{"status":"ok","team": os.environ["TEAM_ID"]}`.
- `rutas/items.py` → `crear_item`, `obtener_item`, `listar_items`; `_es_item` (tiene `value`) filtra trabajos.
- `rutas/trabajos.py` → `crear_trabajo`, `obtener_trabajo`; `_ahora_ms` aislado para simular el reloj en tests.
- `dominio/trabajos.py` (puro) → `procesar(entrada)` = `entrada[::-1]`; `estado(entrada, listo_en_ms, ahora_ms)`.
- `datos/items.py` → `TABLE` (Table de boto3, reemplazable con `monkeypatch`), `guardar`, `obtener`, `listar`.

## Modelo en ItemsTable
- Ítem: `{id: uuid32, value, creado_en: ISO UTC con microsegundos}`.
- Trabajo: `{id: uuid32, tipo: "job", input, creado_en, listo_en: epoch ms = creación + 2000}`.

## Decisiones
- **Resolver al leer** (R3.2-R3.3): `GET /jobs` compara `listo_en` con la hora actual y calcula `output`. Cumple el
  plazo de 12 s del verificador sin cola, sin segunda Lambda y sin escrituras extra. Roadmap: SQS si el trabajo fuera real.
- **Listado completo + orden** (R2.4): el scan no tiene orden, así que cortar en 100 podría omitir el ítem nuevo. Se
  recorren todas las páginas, se descartan trabajos y se ordena por `creado_en` antes de recortar.
- **Despliegue:** `TEAM_ID=T051 scripts/deploy_backend.sh` con bucket de artefactos propio, no `--resolve-s3`
  (la cuenta lo niega; ver `tech.md`).

## Errores
| Caso | Respuesta |
|---|---|
| `value`/`input` inválido o cuerpo no objeto | 400 `{error, detalles}` |
| Id inexistente, con formato inválido o de otro tipo | 404 |
| Excepción no controlada | 500 genérico (detalle solo en CloudWatch) |

## Pruebas
- `tests/test_health.py`, `tests/test_items.py`, `tests/test_jobs.py` con `TablaFalsa` (`conftest.py`): `monkeypatch`
  de `datos.items.TABLE`, scan paginado de 2 en 2 y proyección como DynamoDB; reloj simulado para `/jobs`.
- `tests/test_contrato.py`: 15 rutas iguales en contrato, `app.py`, `template.yaml` y `api.js`.
- E2E contra la API real: crear, leer y listar; consultar `/jobs` cada 1,5 s hasta `done`.
