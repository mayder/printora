#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -s "$SCRIPT_DIR/common.sh" && -s /usr/local/libexec/printora-cloud/common.sh ]]; then
  SCRIPT_DIR=/usr/local/libexec/printora-cloud
fi
source "$SCRIPT_DIR/common.sh"

require_root
release_sha="${1:-}"
[[ "$release_sha" =~ ^[0-9a-f]{7,64}$ ]] || fail "SHA de release inválido"
postgresql_env=/etc/printora-cloud/postgresql.env
[[ -s "$postgresql_env" ]] || fail "configuração PostgreSQL ausente"
release_dir="$PRINTORA_BASE_PATH/releases/$release_sha"
[[ -x "$release_dir/venv/bin/python" ]] || fail "venv da release ausente"
[[ -s "$release_dir/frontend/dist/index.html" ]] || fail "frontend da release ausente"

source_slot="$(active_slot)"
candidate_slot="$(other_slot "$source_slot")"
candidate_port="$(slot_port "$candidate_slot")"
source "$postgresql_env"
[[ "${PRINTORA_DATABASE_URL:-}" == postgresql://* ]] || fail "URL PostgreSQL inválida"

candidate_env="$PRINTORA_BASE_PATH/shared/slots/$candidate_slot.env"
candidate_env_next="$candidate_env.next"
umask 0027
{
  printf 'PRINTORA_PORT=%s\n' "$candidate_port"
  printf 'PRINTORA_SLOT=%s\n' "$candidate_slot"
  printf 'PRINTORA_RUNTIME_PROFILE=cloud\n'
  printf "PRINTORA_DATABASE_URL='%s'\n" "$PRINTORA_DATABASE_URL"
} > "$candidate_env_next"
chown deploy:deploy "$candidate_env_next"
chmod 0640 "$candidate_env_next"
mv -f "$candidate_env_next" "$candidate_env"

candidate_link="$PRINTORA_BASE_PATH/slots/$candidate_slot"
ln -sfn "$release_dir" "$candidate_link.next"
mv -Tf "$candidate_link.next" "$candidate_link"
systemctl restart "printora-cloud@$candidate_slot.service"
if ! wait_until_ready "$candidate_port" 60; then
  systemctl stop "printora-cloud@$candidate_slot.service" || true
  fail "canário PostgreSQL não ficou ready; tráfego permaneceu no slot $source_slot"
fi
curl --max-time 5 -fsS "http://127.0.0.1:$candidate_port/health" >/dev/null
curl --max-time 5 -fsS "http://127.0.0.1:$candidate_port/api/catalog" >/dev/null
printers_status="$(curl --max-time 5 -sS -o /dev/null -w '%{http_code}' \
  "http://127.0.0.1:$candidate_port/api/printers")"
[[ "$printers_status" == "401" ]] || fail "canário não preservou autenticação de impressoras"
echo "[printora-cloud] canary_slot=$candidate_slot source_slot=$source_slot backend=postgresql status=ready traffic_switched=false"
