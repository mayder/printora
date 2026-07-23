#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
config="$base_path/shared/backup-target.conf"
[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
[[ -s "$config" ]] || { echo "configuração de backup externo ausente" >&2; exit 1; }
set -a
source "$config"
set +a

restic forget \
  --tag printora-cloud-postgresql \
  --keep-daily 14 \
  --keep-weekly 8 \
  --keep-monthly 12 \
  --dry-run
echo "retenção apenas pré-visualizada; nenhum snapshot ou bloco foi removido"
