#!/usr/bin/env bash
# Publica el frontend (Vite) en AWS Amplify Hosting con deploy manual (zip de dist/).
# Uso: scripts/deploy_frontend.sh   (variables opcionales: AMPLIFY_APP_ID, BRANCH, AWS_REGION)
set -euo pipefail
cd "$(dirname "$0")/../frontend"

APP_ID="${AMPLIFY_APP_ID:-d2z9k6uh1qqa6x}"
BRANCH="${BRANCH:-main}"
REGION="${AWS_REGION:-us-east-1}"

npm ci --no-audit --no-fund
npm run build
rm -f ../dist.zip
(cd dist && zip -qr ../../dist.zip .)

read -r JOB_ID UPLOAD_URL < <(aws amplify create-deployment --app-id "$APP_ID" --branch-name "$BRANCH" \
  --region "$REGION" --query "[jobId,zipUploadUrl]" --output text)
curl -sf -X PUT -H "Content-Type: application/zip" --data-binary @../dist.zip "$UPLOAD_URL"
aws amplify start-deployment --app-id "$APP_ID" --branch-name "$BRANCH" --job-id "$JOB_ID" --region "$REGION" >/dev/null

echo "Desplegando job $JOB_ID..."
for _ in $(seq 1 60); do
  STATUS=$(aws amplify get-job --app-id "$APP_ID" --branch-name "$BRANCH" --job-id "$JOB_ID" \
    --region "$REGION" --query "job.summary.status" --output text)
  case "$STATUS" in
    SUCCEED) echo "Listo: https://${BRANCH}.${APP_ID}.amplifyapp.com"; exit 0 ;;
    FAILED|CANCELLED) echo "Deploy $STATUS"; exit 1 ;;
  esac
  sleep 5
done
echo "Tiempo de espera agotado (estado: $STATUS)"; exit 1
