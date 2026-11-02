---
inclusion: always
---
# Estructura del repositorio

```
.
├─ README.md                      # qué es, URLs, cómo desplegar y probar
├─ plan.md                        # plan original de la hackatón
├─ docs/ALCANCE.md                # investigación, decisiones, pitch y guion de demo
├─ docs/KIRO-PLAYBOOK.md          # cómo se usó Kiro (steering, specs, hooks)
├─ .kiro/steering/                # product, tech, structure, api-contract (always) · ia-bedrock (fileMatch)
├─ .kiro/specs/01-backend-api/ · 02-ia-priorizacion/ · 03-frontend-pwa-tablero/ · 04-insignias-iathon/
├─ .kiro/hooks/                   # v1 (.json): pytest al guardar .py, contrato al guardar api-contract.md
│                                 # when/then (.kiro.hook): revisar tasks.md al guardar una spec
├─ data/                          # FUENTE DE VERDAD: distritos_piura.json, zonas_criticas.json, seed_reportes.json
├─ backend/
│  ├─ template.yaml               # SAM: S3, DynamoDB, HTTP API, Lambda
│  ├─ src/app.py                  # handler + tabla de rutas (routeKey -> función)
│  ├─ src/rutas/                  # http.py (helpers), publicas.py (+ salud), admin.py, servicio.py,
│  │                              # items.py y trabajos.py (insignias de la IAthon)
│  ├─ src/ia/                     # clasificador.py (Bedrock Mantle), parte_situacional.py (S3)
│  ├─ src/dominio/                # catalogos.py (enums), prioridad.py (pura), geo.py, validacion.py, trabajos.py
│  ├─ src/datos/                  # repositorio.py (Reportes + S3), items.py (ItemsTable) y copia de data/*.json
│  ├─ requirements-dev.txt        # pytest + moto (solo pruebas)
│  └─ tests/                      # unitarios, test_contrato.py, test_api_integracion.py (moto),
│                                 # test_health/items/jobs.py (TablaFalsa de conftest.py)
├─ frontend/
│  ├─ src/pages/                  # Reportar.jsx, Mapa.jsx, Tablero.jsx
│  ├─ src/components/Mapas.jsx    # capas Leaflet, marcadores, leyenda
│  ├─ src/lib/                    # comprimirImagen.js, colaOffline.js (S4), geo.js (puro) + geo.test.js
│  ├─ src/api.js                  # cliente HTTP (único lugar con rutas de la API)
│  └─ src/catalogos.js            # enums y etiquetas (importa data/*.json)
└─ scripts/                       # deploy_backend.sh, deploy_frontend.sh, seed.py, smoke_test.py, check_bedrock.py
```

## Convenciones
- Código, nombres y textos en español (`crear_reporte`, `calcular_prioridad`, `Reportar.jsx`).
- Python: funciones puras en `dominio/` (sin I/O, testeables); I/O solo en `datos/` e `ia/`.
- Rutas nuevas: declarar el evento en `template.yaml` **y** la entrada en `RUTAS` de `app.py` **y** el método en `api.js`.
- `data/` se copia a `backend/src/datos/` en cada deploy; un test verifica que estén sincronizados.
- Enums: mismos valores en `api-contract.md`, `dominio/catalogos.py` y `frontend/src/catalogos.js`.
- Nombre visible: **WaSOS**. Recursos de AWS y claves de `localStorage` siguen como `alerta-piura` (no renombrar).

## Qué no hacer
- No cambiar las claves en inglés de `/health`, `/items` y `/jobs` (`status`, `team`, `value`, `jobId`, `output`):
  las verifica el portal de la IAthon.
- No guardar ítems ni trabajos en `Reportes`, ni reportes en `ItemsTable`.
- No desplegar sin `TEAM_ID=T051` ni con `--resolve-s3`; usar `scripts/deploy_backend.sh`.
- No usar datos personales reales en seeds, tests ni demos: solo datos simulados o públicos.
- No conectar servicios que no estén declarados en `backend/template.yaml`.
