#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root_dir"

if rg -ni '(^|[,[:space:]])(pan|cvv|cvc|card_number|security_code)[[:space:]]+(text|varchar|char|integer|bigint)' \
  backend/sql/0*_finance_*.sql backend/sql/postgresql/0*_finance_*.sql; then
  echo "schema financeiro não pode persistir dado bruto de cartão" >&2
  exit 1
fi

rg -q 'PaymentMode = Literal\["disabled", "sandbox"\]' backend/app/config.py || {
  echo "runtime financeiro deve permanecer limitado a disabled/sandbox" >&2
  exit 1
}
rg -q 'payload_sha256' backend/sql/078_finance_payments.sql || {
  echo "webhook financeiro deve persistir somente digest" >&2
  exit 1
}
if rg -n 'payment_webhook_events.*payload_json|payload_json.*payment_webhook_events' backend; then
  echo "payload bruto de webhook financeiro detectado" >&2
  exit 1
fi
rg -q 'checkout\.sandbox\.invalid' backend/app/payment_provider.py || {
  echo "checkout sandbox deve permanecer hospedado fora da aplicação" >&2
  exit 1
}

echo "segurança financeira: sandbox-only, checkout hospedado e zero PAN/CVV persistido"
