# Diseño: 01 Backend API

Contrato y modelo de datos: #[[file:.kiro/steering/api-contract.md]]

## Componentes (`backend/template.yaml`)
| Recurso | Detalle | Requisitos |
|---|---|---|
| `FotosBucket` (S3) | Privado por defecto, SSE-S3, CORS PUT/GET al dominio de Amplify, policy `aws:SecureTransport` | R1.3 |
| `ReportesTable` (DynamoDB) | On-demand, PK `id`, PITR | R2.1 |
| `HttpApi` | HTTP API, CORS (`content-type`, `x-admin-key`), throttling 20/50 | R6.1 |
| `ApiFunction` (Lambda) | Python 3.12, 1024 MB, 29 s, 15 rutas (incluye `GET /health`, `/items` y `/jobs`) → `app.handler` | todos |

IAM mínimo: CRUD en la tabla, `s3:GetObject`/`s3:PutObject` en `fotos/*`, `bedrock-mantle:CreateInference`.

## Secuencia de un reporte
```
Celular → POST /uploads → {upload_url, foto_key}
Celular → PUT upload_url (JPEG ≤300 KB, sin EXIF) → S3
Celular → POST /reportes {foto_key, lat, lon, ...}
  Lambda: validar_reporte → obtener(id) [idempotencia] → leer_foto (head + get, ≤1,5 MB)
        → clasificador.clasificar (Bedrock, ≤23 s, fallback) → calcular_para (prioridad + zona crítica)
        → guardar (ConditionExpression attribute_not_exists) → 201 ReportePublico
```

## Archivos
- `src/app.py`: `RUTAS = {"POST /reportes": publicas.crear_reporte, ...}`; `_verificar_admin` con `hmac.compare_digest`;
  `ErrorHttp` → JSON `{error, detalles}`; excepciones no controladas → 500 genérico + `logger.exception`.
- `src/rutas/http.py`: `respuesta`, `leer_json` (máx. 20 KB), `query`, `path_param`, `header`, `ahora_iso`.
- `src/rutas/publicas.py`: `crear_upload`, `crear_reporte`, `listar_reportes`, `confirmar`.
- `src/rutas/admin.py`: `listar`, `actualizar`, `resumen`, `exportar_csv`, `parte_situacional`.
- `src/rutas/servicio.py`: `tipo_efectivo`, `calcular_para`, `a_publico`, `ordenar`.
- `src/datos/repositorio.py`: `guardar`, `obtener`, `listar` (Scan paginado), `incrementar_confirmaciones` (ADD atómico),
  `actualizar_prioridad`, `cambiar_estado` (bloqueo optimista `estado = :actual`), `url_subida`, `url_lectura`, `leer_foto`.
- `src/dominio/validacion.py`: `validar_reporte`, `validar_cambio_estado` → `ErrorValidacion(errores)`.

## Decisiones
- `id` = uuid de la foto: hace idempotente el reintento de la cola offline (R2.4) sin tabla extra.
- Scan + orden en memoria: suficiente para cientos de reportes. Roadmap: GSI `distrito`+`prioridad`.
- Clave compartida en vez de Cognito: ahorra ~40 min; se presenta Cognito como roadmap.
- La cuenta de la hackatón niega `s3:PutBucketPublicAccessBlock`: se confía en el bloqueo por defecto de buckets nuevos
  y se usa un bucket de artefactos propio para SAM.

## Manejo de errores
| Caso | Respuesta |
|---|---|
| JSON inválido / campos inválidos | 400 `{error, detalles}` |
| Sin clave admin | 401 |
| Reporte inexistente | 404 |
| Transición inválida / edición concurrente / confirmar inactivo | 409 |
| Foto > 1,5 MB o cuerpo > 20 KB | 413 |
| Falla de Bedrock | No es error: fallback y 201 |
| Excepción no controlada | 500 genérico (detalle solo en CloudWatch) |

## Concurrencia
- **PATCH de estado (bloqueo optimista):** `admin.actualizar` lee el reporte, valida la transición contra el estado leído y
  llama `repositorio.cambiar_estado(id, estado_actual, nuevo, ...)` con `ConditionExpression="estado = :actual"`. Si otro
  operador cambió el estado entre la lectura y la escritura, DynamoDB rechaza la escritura
  (`ConditionalCheckFailedException` → `ConflictoEstado`) y la API responde 409 "El reporte cambió mientras lo editaba;
  recargue". El cambio del otro operador no se pisa.
- **Confirmaciones (S1):** `incrementar_confirmaciones` usa `ADD` atómico; `actualizar_prioridad` solo escribe si
  `confirmaciones = :c` sigue siendo el conteo con el que se calculó, así una escritura tardía no deja una prioridad vieja.
- **Alta de reporte:** `put_item` con `attribute_not_exists(id)`; ante carrera con un reintento se devuelve el existente.

## Pruebas
- Unitarias: prioridad, geo (bbox con bordes, distrito por centroide), validación, CSV (`_celda`), datos demo, contrato
  (rutas y enums iguales en contrato, `app.py`, `template.yaml`, `api.js` y catálogos).
- Integración (`tests/test_api_integracion.py`): el handler real contra DynamoDB y S3 simulados con moto y credenciales
  falsas; IA simulada. Cubre fallback de IA, idempotencia, bbox 400, vista pública, 401, flujo de estados, 409 por
  transición inválida y por edición concurrente, resumen, CSV con fórmula maliciosa y confirmaciones.
- Comando: `cd backend && uv run --python 3.12 --with-requirements requirements-dev.txt pytest -q tests` (94 tests).
- E2E: `python3 scripts/smoke_test.py <ApiUrl> foto.jpg` (uploads → PUT → reportes → listado).
