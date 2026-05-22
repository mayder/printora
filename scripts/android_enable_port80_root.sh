#!/usr/bin/env bash
set -euo pipefail

HTTP_PORT="${HTTP_PORT:-8085}"

if ! command -v su >/dev/null 2>&1; then
  echo "root indisponivel: su nao encontrado" >&2
  exit 1
fi

if ! su -c id >/dev/null 2>&1; then
  echo "root indisponivel: su nao autorizado" >&2
  exit 1
fi

su -c "iptables -t nat -D PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports ${HTTP_PORT} 2>/dev/null || true"
su -c "iptables -t nat -D OUTPUT -p tcp -o lo --dport 80 -j REDIRECT --to-ports ${HTTP_PORT} 2>/dev/null || true"
su -c "iptables -t nat -I PREROUTING 1 -p tcp --dport 80 -j REDIRECT --to-ports ${HTTP_PORT}"
su -c "iptables -t nat -I OUTPUT 1 -p tcp -o lo --dport 80 -j REDIRECT --to-ports ${HTTP_PORT}"

echo "porta 80 redirecionada para ${HTTP_PORT}"
