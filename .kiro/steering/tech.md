---
inclusion: always
---
# Stack técnico

## Backend
- Python 3.12 en AWS Lambda (x86_64, 1024 MB, timeout 29 s), una sola función "api" con router por `routeKey`.
- API Gateway **HTTP API** (payload 2.0), CORS al dominio de Amplify + localhost, throttling 20 rps / burst 50.
- DynamoDB `Reportes` on-demand (PK `id`), PITR activado. Listados con Scan + orden en la Lambda (volumen de demo).
- S3 privado para fotos (`fotos/{uuid}.jpg`), subida con URL prefirmada PUT (5 min) y lectura prefirmada GET (15 min).
- IaC: AWS SAM (`backend/template.yaml`). Despliegue: `TEAM_ID=T051 scripts/deploy_backend.sh` (`sam build` + `sam deploy`;
  `TeamId` → env `TEAM_ID` → `GET /health`).
  - La cuenta de la hackatón niega `s3:PutBucketPublicAccessBlock`: no declarar `PublicAccessBlockConfiguration`
    (los buckets nuevos ya bloquean acceso público por defecto) y usar bucket de artefactos propio, no `--resolve-s3`.
- Dependencias: solo `anthropic[bedrock]` (en `backend/src/requirements.txt`). boto3 viene en el runtime.
- Tests: `cd backend && uv run --python 3.12 --with-requirements requirements-dev.txt pytest -q tests`
  (unitarios + integración con DynamoDB/S3 simulados por moto; `conftest.py` fija credenciales falsas para no tocar AWS real).
  Frontend: `cd frontend && npm test` (`node --test`, funciones puras de `src/lib/geo.js`).

## IA (Claude en Amazon Bedrock)
- Endpoint `bedrock-mantle` (Messages API) con `anthropic.AnthropicBedrockMantle(aws_region="us-east-1")`.
- Salida estructurada con `client.messages.parse(..., output_format=ClasificacionIA, output_config={"effort": "low"})`.
- `MODEL_IDS` (variable de entorno, lista en orden): `anthropic.claude-sonnet-5,anthropic.claude-opus-4-8`.
  `anthropic.claude-opus-5-5` respondió 529 (overloaded) el 30-oct; `anthropic.claude-haiku-5-5` no existe en Mantle.
- IAM: `bedrock-mantle:CreateInference`. Siempre `max_tokens` explícito. Sin prefill ni `temperature`.
- Detalle en `.kiro/steering/ia-bedrock.md`.

## Frontend
- React 19 + Vite 8 (JavaScript), react-router-dom 7, Leaflet 1.9 + react-leaflet 5 con teselas de OpenStreetMap.
- Hosting: AWS Amplify Hosting con deploy manual (zip de `dist/`) vía `scripts/deploy_frontend.sh`.
  Regla de reescritura SPA configurada en la app de Amplify.
- `VITE_API_URL` en `frontend/.env.production`.

## Reglas
- No Cognito en el MVP: clave compartida en header `X-Admin-Key` (parámetro NoEcho de SAM, comparación `hmac.compare_digest`).
  La clave vive en `backend/.admin-key` (fuera de git).
- Validar toda entrada en la Lambda (bbox Piura, enums, longitudes, consentimiento). Nunca loguear datos personales.
- CSV con protección contra inyección de fórmulas.
- Coordenadas y montos: floats a `Decimal` antes de DynamoDB (`datos/repositorio.a_dynamo`).
