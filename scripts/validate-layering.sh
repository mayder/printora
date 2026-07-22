#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
log "validando arquitetura por camadas"
enabled="$(toml_string_value quality.layering enabled)"
if [[ "$enabled" != "true" ]]; then log "quality.layering.enabled=false; pulando validação de camadas no modelo"; exit 0; fi
runtime_dirs=()
while IFS= read -r dir; do [[ -n "$dir" ]] && runtime_dirs+=("$dir"); done < <(toml_array_values quality runtime_dirs)
if [[ ${#runtime_dirs[@]} -eq 0 ]]; then
  log "runtime_dirs vazio; pulando validação de camadas no modelo"
  exit 0
fi
for dir in "${runtime_dirs[@]}"; do [[ -d "$dir" ]] || fail "runtime_dir inexistente: $dir"; done
if [[ "${STRICT_REACT_LAYERING:-1}" != "1" ]]; then
  log "layering React estrito desativado explicitamente"
  exit 0
fi
if find "${runtime_dirs[@]}" -type f \( -name '*.tsx' -o -name '*.jsx' \) | grep -q .; then
  if rg -n "(fetch\(|axios\.|localStorage\.|sessionStorage\.)" "${runtime_dirs[@]}" -g'*.tsx' -g'*.jsx' -g'**/pages/**' -g'**/components/**'; then
    fail "UI React não deve acessar HTTP/storage diretamente sem boundary documentada"
  fi
fi
