#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
log "validando arquivos obrigatórios"
require_file PATHS.toml
for key in scope governance roadmap backlog bugs screens tests decisions runbook readme mindmap_complete mindmap_executive; do
  file="$(toml_string_value files "$key")"
  [[ -n "$file" ]] || fail "PATHS.toml sem files.$key"
  require_file "$file"
done
require_file check.sh
require_file scripts/validate-layering.sh
for script in scripts/*.sh; do [[ -x "$script" ]] || fail "script sem permissão de execução: $script"; done
