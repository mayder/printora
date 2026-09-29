#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if ! command -v redis-server >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y redis-server redis-tools
fi
id redis >/dev/null
getent group deploy >/dev/null

install -d -o root -g root -m 0755 /etc/redis /etc/printora-cloud
install -o root -g root -m 0644 "$ROOT_DIR/packaging/redis/printora.conf" /etc/redis/printora.conf
install -o root -g deploy -m 0640 "$ROOT_DIR/packaging/redis/printora-users.acl" /etc/redis/printora-users.acl
install -o root -g root -m 0644 "$ROOT_DIR/packaging/systemd/redis-printora.service" /etc/systemd/system/redis-printora.service
printf 'PRINTORA_REDIS_URL=unix:///run/redis-printora/redis.sock?db=0\n' > /etc/printora-cloud/redis.env
chown root:deploy /etc/printora-cloud/redis.env
chmod 0640 /etc/printora-cloud/redis.env

systemctl daemon-reload
systemctl enable --now redis-printora.service
for _attempt in $(seq 1 50); do
  if redis-cli -s /run/redis-printora/redis.sock ping 2>/dev/null | grep -qx PONG; then
    echo "Redis dedicado e recomponível ativo somente por socket local."
    exit 0
  fi
  sleep 0.1
done
systemctl status redis-printora.service --no-pager >&2 || true
echo "ERRO: Redis não respondeu no socket dedicado" >&2
exit 1
