#!/usr/bin/env bash
set -euo pipefail
TABLE="${DYNAMODB_TABLE:-opsguardian-incidents}"
REGION="${AWS_REGION:-us-west-2}"
if aws dynamodb describe-table --table-name "$TABLE" --region "$REGION" >/dev/null 2>&1; then
  echo "DynamoDB table already exists: $TABLE"
  exit 0
fi
aws dynamodb create-table \
  --table-name "$TABLE" \
  --attribute-definitions AttributeName=incident_id,AttributeType=S \
  --key-schema AttributeName=incident_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$REGION"
aws dynamodb wait table-exists --table-name "$TABLE" --region "$REGION"
echo "Created $TABLE in $REGION"
