#!/usr/bin/env bash
# Despliega el backend (SAM): S3 privado, DynamoDB, HTTP API y Lambda Python 3.12.
# Uso: TEAM_ID=<id del portal> scripts/deploy_backend.sh   (opcionales: STACK, AWS_REGION, ALLOWED_ORIGINS)
set -euo pipefail
cd "$(dirname "$0")/.."

# Id público del equipo en el portal de la Kiro IAthon: GET /health lo devuelve tal cual en "team"
TEAM_ID="${TEAM_ID:?Defina TEAM_ID con el id público del equipo en el portal}"

STACK="${STACK:-alerta-piura}"
REGION="${AWS_REGION:-us-east-1}"
ORIGINS="${ALLOWED_ORIGINS:-https://main.d2z9k6uh1qqa6x.amplifyapp.com,http://localhost:5173}"
KEY_FILE="backend/.admin-key"

# Clave compartida del tablero: se genera una vez y no se versiona (.gitignore)
if [ ! -s "$KEY_FILE" ]; then
  python3 -c "import secrets; print(secrets.token_urlsafe(24))" > "$KEY_FILE"
  chmod 600 "$KEY_FILE"
fi

# data/ es la fuente de verdad; la Lambda empaqueta una copia
cp data/distritos_piura.json data/zonas_criticas.json backend/src/datos/

# Bucket de artefactos propio (la cuenta de la hackatón no permite el bucket gestionado de SAM)
ACCOUNT="$(aws sts get-caller-identity --query Account --output text)"
ARTEFACTOS="alerta-piura-artefactos-${ACCOUNT}"
aws s3api head-bucket --bucket "$ARTEFACTOS" 2>/dev/null || aws s3 mb "s3://${ARTEFACTOS}" --region "$REGION"

cd backend
sam build
sam deploy \
  --stack-name "$STACK" \
  --region "$REGION" \
  --s3-bucket "$ARTEFACTOS" \
  --s3-prefix backend \
  --capabilities CAPABILITY_IAM \
  --no-confirm-changeset \
  --no-fail-on-empty-changeset \
  --parameter-overrides "TeamId=$TEAM_ID" "AdminKey=$(cat .admin-key)" "AllowedOrigins=$ORIGINS"

aws cloudformation describe-stacks --stack-name "$STACK" --region "$REGION" \
  --query "Stacks[0].Outputs" --output table
