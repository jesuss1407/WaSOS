---
inclusion: always
---
# Contrato de API (fuente única de verdad)

Base: `https://splg8tml5k.execute-api.us-east-1.amazonaws.com` (salida `ApiUrl` del stack `alerta-piura`).
JSON UTF-8. Errores: `{"error": str, "detalles"?: {campo: mensaje}}` con 400/401/404/409/413/500.
Rutas admin: header `X-Admin-Key` (401 si falta o no coincide).

| Método | Ruta | Auth | Entrada | Salida |
|---|---|---|---|---|
| GET | `/health` | — | — | `{"status":"ok","team":<TEAM_ID>}` (insignia "API viva"; `team` = parámetro SAM `TeamId`) |
| POST | `/items` | — | `{value: str (1-1024)}` | 201 `{id, value}`; guarda en `ItemsTable` (env `TABLE_NAME`) (insignia "Persistencia") |
| GET | `/items/{id}` | — | — | `{id, value}`; 404 si no existe |
| GET | `/items` | — | — | `[{id, value}]` hasta 100, los más recientes; el scan recorre todas las páginas |
| POST | `/jobs` | — | `{input: str (1-1024)}` | 202 `{jobId}`; guarda en `ItemsTable` con `tipo="job"` y `listo_en` = creación + 2 s (insignia "Asíncrono o agente") |
| GET | `/jobs/{jobId}` | — | — | `{jobId, status: queued\|done, output}`; `output` = `input` invertido al estar `done` (null antes); 404 si no existe |
| POST | `/uploads` | — | `{content_type:"image/jpeg"}` | `{upload_url, foto_key}` (PUT prefirmado, 5 min) |
| POST | `/reportes` | — | `{foto_key, lat, lon, distrito, tipo, descripcion?, vulnerables, necesidades[], consentimiento:true}` | 201 `ReportePublico` (incluye `motivos`); 200 si el `foto_key` ya generó un reporte (idempotente) |
| GET | `/reportes` | — | `?distrito&nivel` | `[ReportePublico]` solo `es_valida`, sin `descartado`, ordenado por prioridad |
| POST | `/reportes/{id}/confirmar` | — | — | `{id, confirmaciones, prioridad, nivel, motivos}` (S1); 409 si no está activo |
| GET | `/admin/reportes` | Admin | `?distrito&tipo&estado&nivel` | `[Reporte]` + `foto_url` (GET prefirmado 15 min) + `transiciones[]` |
| PATCH | `/admin/reportes/{id}` | Admin | `{estado, brigada?, nota?}` | `Reporte`; 409 si la transición no está permitida o si el estado cambió desde la lectura (bloqueo optimista `estado = :actual`) |
| GET | `/admin/resumen` | Admin | — | `{total, total_activos, por_estado, por_nivel, por_distrito[{distrito,total,vulnerables,niveles,necesidades}], necesidades_total}` |
| GET | `/admin/export.csv` | Admin | — | `text/csv` con BOM (S2) |
| POST | `/admin/parte-situacional` | Admin | `{distrito?}` | `{texto, modelo, estado_ia}` (S3) |

## Validaciones (Lambda)
- `lat` ∈ [−6,4; −4,0] y `lon` ∈ [−81,4; −79,2] (bbox región Piura). `consentimiento` debe ser `true`.
- `foto_key` con formato `fotos/{uuid32}.jpg` y existente en S3 (≤1,5 MB; el cliente comprime a ≤300 KB).
- `tipo`, `necesidades[]`, `distrito` dentro de sus enums. `descripcion` ≤ 500 caracteres. `vulnerables` booleano.
- PATCH: `brigada` ≤ 80 y obligatoria para `en_atencion`; `nota` ≤ 300.

## ReportePublico
`id, creado_en, lat, lon (4 decimales), distrito, tipo (de la IA si estado_ia=ok), severidad, descripcion_ia,
riesgo_vida, riesgo_salud, es_valida, necesidades[], vulnerables, prioridad, nivel, motivos[], confirmaciones, estado`.
Nunca incluye foto, `foto_key` ni la descripción libre del vecino.

## Modelo de datos: DynamoDB `Reportes` (PK `id` = uuid de la foto)
`id, creado_en, actualizado_en, lat, lon, distrito, tipo_usuario, descripcion, vulnerables, necesidades[], foto_key,
ia{tipo, severidad, es_valida, riesgo_vida, riesgo_salud, descripcion, confianza, modelo, estado_ia: ok|fallback|demo, latencia_ms?, error_ia?},
prioridad, nivel, motivos[], confirmaciones, estado, brigada, historial[{estado, fecha, nota, brigada?}], origen: ciudadano|demo`

## Enums
- **tipo:** `inundacion_vivienda, aniego_via, desborde_rio_quebrada, dren_colmatado, basura_cauce, agua_estancada, desague_colapsado, deslizamiento_huaico, infraestructura_danada, otro`
- **necesidades:** `agua, viveres, evacuacion, atencion_medica, motobomba, abrigo_carpa, limpieza_dren`
- **distrito:** `Piura, Castilla, Veintiséis de Octubre, Catacaos, Cura Mori, El Tallán, La Arena, La Unión, Las Lomas, Tambogrande, Otro (región)`
- **estado:** `nuevo → verificado → en_atencion (brigada) → resuelto | descartado` (descartar desde cualquier estado activo)
- **nivel:** `CRÍTICA (≥75) · ALTA (50-74) · MEDIA (25-49) · BAJA (<25)`

## Prioridad (dominio/prioridad.py)
```
p = 100 × (0.40·sev/5 + 0.20·peso_tipo + 0.15·vulnerables + 0.15·cerca_zona_critica(≤300 m) + 0.10·min(conf/5,1))
+10 si riesgo_vida (tope 100); es_valida=false → p = min(p, 20)
peso_tipo: desborde/huaico/inundación_vivienda 1.0 · desagüe/infraestructura 0.8 · aniego/dren 0.6 · agua_estancada 0.5 · basura 0.4 · otro 0.3
```
