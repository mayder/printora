#!/usr/bin/env bash
set -euo pipefail

PRINTORA_BASE_PATH="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
PRINTORA_ACTIVE_SLOT_FILE="$PRINTORA_BASE_PATH/shared/active-slot"

fail() {
  echo "[printora-cloud] ERRO: $*" >&2
  exit 1
}

require_root() {
  [[ "$(id -u)" -eq 0 ]] || fail "execução exige root via sudo controlado"
}

validate_slot() {
  [[ "${1:-}" == "blue" || "${1:-}" == "green" ]] || fail "slot inválido: ${1:-vazio}"
}

slot_port() {
  case "$1" in
    blue) echo 8069 ;;
    green) echo 8070 ;;
    replica) echo 8071 ;;
    *) fail "slot inválido: $1" ;;
  esac
}

active_slot() {
  local slot="blue"
  if [[ -s "$PRINTORA_ACTIVE_SLOT_FILE" ]]; then
    slot="$(tr -d '[:space:]' < "$PRINTORA_ACTIVE_SLOT_FILE")"
  fi
  validate_slot "$slot"
  echo "$slot"
}

other_slot() {
  if [[ "$1" == "blue" ]]; then echo green; else echo blue; fi
}

wait_until_ready() {
  local port="$1"
  local attempts="${2:-45}"
  local attempt
  for attempt in $(seq 1 "$attempts"); do
    if curl --max-time 2 -fsS "http://127.0.0.1:$port/ready" >/dev/null; then
      return 0
    fi
    sleep 1
  done
  return 1
}

activate_replica() {
  local release_dir="$1"
  local replica_link="$PRINTORA_BASE_PATH/slots/replica"
  local previous_release=""
  local replica_port
  [[ -d "$release_dir/backend" ]] || fail "backend da release da réplica ausente"
  if [[ -L "$replica_link" ]]; then
    previous_release="$(readlink -f "$replica_link")"
  fi
  replica_port="$(slot_port replica)"
  ln -sfn "$release_dir" "$replica_link.next"
  mv -Tf "$replica_link.next" "$replica_link"
  systemctl restart printora-cloud@replica.service
  if wait_until_ready "$replica_port" 60; then
    echo "[printora-cloud] replica_release=$(basename "$release_dir") status=ready"
    return 0
  fi
  systemctl stop printora-cloud@replica.service || true
  if [[ -n "$previous_release" && -d "$previous_release" ]]; then
    ln -sfn "$previous_release" "$replica_link.next"
    mv -Tf "$replica_link.next" "$replica_link"
    systemctl restart printora-cloud@replica.service || true
  fi
  fail "réplica não ficou ready; upstream atual foi preservado"
}

start_standby() {
  local slot="$1"
  local port
  validate_slot "$slot"
  [[ -L "$PRINTORA_BASE_PATH/slots/$slot" ]] || return 0
  port="$(slot_port "$slot")"
  systemctl restart "printora-cloud@$slot.service"
  if wait_until_ready "$port" 60; then
    echo "[printora-cloud] standby_slot=$slot status=ready"
    return 0
  fi
  systemctl stop "printora-cloud@$slot.service" || true
  echo "[printora-cloud] ALERTA: standby_slot=$slot status=failed" >&2
  return 1
}

restart_durable_workers() {
  local target=printora-cloud-workers.target
  if [[ ! -f /etc/systemd/system/$target ]]; then return 0; fi
  systemctl stop "$target" || true
  if [[ ! -f "$PRINTORA_BASE_PATH/current/backend/app/worker.py" ]]; then
    echo "[printora-cloud] workers=disabled release=not_compatible"
    return 0
  fi
  systemctl start "$target"
  local queue
  for queue in outbox critical default bulk; do
    systemctl is-active --quiet "printora-cloud-worker@$queue.service" \
      || fail "worker $queue não iniciou"
  done
  echo "[printora-cloud] workers=restarted status=ready"
}

switch_nginx_to_slot() {
  local slot="$1"
  local target="$PRINTORA_BASE_PATH/shared/nginx/upstream-$slot.conf"
  local link="/etc/nginx/conf.d/printora-cloud-active.conf"
  local previous=""
  validate_slot "$slot"
  [[ -s "$target" ]] || fail "upstream ausente: $target"
  if [[ -L "$link" ]]; then previous="$(readlink "$link")"; fi
  ln -sfn "$target" "$link"
  if ! nginx -t; then
    if [[ -n "$previous" ]]; then ln -sfn "$previous" "$link"; else rm -f "$link"; fi
    fail "nginx rejeitou upstream do slot $slot"
  fi
  systemctl reload nginx
}
