# Cómo se usó Kiro

## Steering (`.kiro/steering/`)
| Archivo | Inclusión | Para qué |
|---|---|---|
| `product.md` | always | Problema, usuarios, MoSCoW, principios (privacidad, tono, inclusión) |
| `tech.md` | always | Stack, reglas de AWS/Bedrock, restricciones de la cuenta de la hackatón |
| `structure.md` | always | Árbol del repo y convenciones (rutas en 3 lugares, `data/` como fuente de verdad) |
| `api-contract.md` | always | Contrato de API, modelo de datos, enums y fórmula: la referencia compartida |
| `ia-bedrock.md` | fileMatch `backend/src/ia/**` | Cliente Mantle, schema, modelos probados, fallback |

## Specs (`.kiro/specs/`)
Cada spec tiene `requirements.md` (EARS con IDs R*.* y marca MUST/SHOULD), `design.md` (componentes, interfaces,
errores, pruebas) y `tasks.md` (tareas con trazabilidad a requisitos, archivo y test).
1. `01-backend-api`: SAM, S3, DynamoDB, rutas, validación, clave admin.
2. `02-ia-priorizacion`: clasificador Bedrock, prioridad explicable, parte situacional.
3. `03-frontend-pwa-tablero`: Reportar, Mapa, Tablero, compresión, cola offline.
4. `04-insignias-iathon`: `GET /health`, `/items` y `/jobs` para las insignias "API viva", "Persistencia" y
   "Asíncrono o agente" del portal (arquitectura mínima: misma HTTP API y Lambda + `ItemsTable`).

Para iterar: abrir la spec en el panel Specs y pedir "Update tasks" o ejecutar una tarea nueva desde `tasks.md`.

## Hooks (`.kiro/hooks/`)
Hay dos formatos. `revisar-tasks-spec.kiro.hook` usa el formato con claves `when` / `then` (el que pide la insignia
"Maestría Kiro"); Kiro IDE 1.0 lo muestra como hook *legacy* con un botón de actualización. No conviene actualizarlo
antes de la evaluación, porque la migración reemplaza `when`/`then` por `trigger`/`action`.

### `revisar-tasks-spec.kiro.hook`
- **Cuando (`when`):** `{"type": "fileEdited", "patterns": [".kiro/specs/*/requirements.md", ".kiro/specs/*/design.md", ".kiro/specs/*/tasks.md"]}`.
- **Entonces (`then`):** `{"type": "askAgent", "prompt": "…"}`. El agente lista requisitos `R*.*` sin tarea en
  `tasks.md`, comprueba que los archivos y tests citados existan, revisa el orden de las tareas y que `design.md` solo
  use servicios de `template.yaml`. Solo reporta.

Los otros dos hooks están implementados como archivos JSON en el formato v1 de Kiro IDE 1.0. En ese formato la pareja
"cuando / entonces" se escribe como `trigger` + `matcher` (cuando) y `action` (entonces). La documentación lo dice así:
"the `when`/`then` structure becomes `trigger`/`matcher`/`action`"
([Kiro IDE 1.0, Hooks](https://kiro.dev/docs/ide/whats-new-v1/hooks.md)). El campo `description` de cada hook repite
la regla en forma CUANDO … ENTONCES … para quien lea el archivo.

### `pytest-backend.json`
- **Cuando:** `"trigger": "PostFileSave"` y `"matcher": "backend/.*\\.py$"` (el agente guarda un `.py` del backend).
- **Entonces:** `"action": {"type": "command", "command": "cd backend && uv run --quiet --python 3.12 --with-requirements requirements-dev.txt pytest -q tests"}`.
- **Qué cubre:** prioridad, geo y bbox, validación, bloqueo optimista, CSV, contrato e integración con DynamoDB/S3
  simulados (94 tests, unos 3 s). Usa el timeout por defecto (60 s).

### `revisar-contrato-api.json`
- **Cuando:** `"trigger": "PostFileSave"` y `"matcher": "\\.kiro/steering/api-contract\\.md$"`.
- **Entonces:** `"action": {"type": "agent", "prompt": "Se modificó .kiro/steering/api-contract.md. Verifica …"}`.
  El agente compara las rutas de `app.py`, los eventos de `template.yaml`, los métodos de `api.js` y los enums de
  backend y frontend. Puede apoyarse en `tests/test_contrato.py`. Reporta diferencias sin modificar archivos.

Nota: según la documentación, `PostFileSave` se dispara cuando el agente guarda o modifica un archivo. Las ediciones
manuales en el editor no lo disparan, así que tras editar a mano conviene correr `pytest` directamente.

## Prompts útiles
- "Agrega la ruta X según `api-contract.md`: evento en `template.yaml`, entrada en `RUTAS` y método en `api.js`."
- "Ajusta el prompt de `ia/clasificador.py` para distinguir `aniego_via` de `inundacion_vivienda`; no cambies el schema."
- "Corre `scripts/smoke_test.py` contra la API y explica los motivos de prioridad devueltos."
