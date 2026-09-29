#!/usr/bin/env bash
set -euo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"
log "checando possíveis segredos"
if [[ "${CHECK_STRICT_SECRETS:-0}" != "1" ]]; then
  log "modo legado: varredura ampla de segredos desativada; use CHECK_STRICT_SECRETS=1 para scan completo"
  exit 0
fi
while IFS= read -r -d '' file; do
  [[ -f "$file" ]] || continue
  quoted_pattern="(password|passwd|token|secret|api[_-]?key|private[_-]?key)[[:space:]]*[:=][[:space:]]*(\"[^\"\$({<][^\"]{5,}\"|'[^'\$({<][^']{5,}')"
  signature_pattern='-----BEGIN [A-Z ]*PRIVATE KEY-----|github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|A[KS]IA[0-9A-Z]{16}'
  assignment_pattern="^[[:space:]]*[A-Z0-9_]*(PASSWORD|PASSWD|TOKEN|SECRET|API[_-]?KEY|PRIVATE[_-]?KEY)[A-Z0-9_]*[[:space:]]*=[[:space:]]*[^[:space:]<#\$({'\"]"
  has_match=0
  grep -IiqE -e "$signature_pattern" "$file" && has_match=1
  case "$file" in
    */tests/*|*_test.go|*.test.*|*/dist/*|*/build/*)
      ;;
    *)
      grep -IiqE "$quoted_pattern" "$file" && has_match=1
      case "$file" in
        *.env|*.ini|*.conf|*.toml|*.yaml|*.yml|*.sh)
          grep -IqE "$assignment_pattern" "$file" && has_match=1
          ;;
      esac
      ;;
  esac
  if [[ "$has_match" -eq 1 ]]; then
    echo "[check:modelo] possível padrão de segredo em: $file" >&2
    fail "possível segredo encontrado; revisar antes de continuar"
  fi
done < <(git ls-files -co --exclude-standard -z)
