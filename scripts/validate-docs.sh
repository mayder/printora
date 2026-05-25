#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/common.sh"

log "validando documentação"

while IFS= read -r file; do
  count="$(awk 'BEGIN{n=0} /^```/{n++} END{print n}' "$file")"
  if (( count % 2 != 0 )); then
    fail "bloco markdown quebrado em $file"
  fi
done < <(find . -maxdepth 1 -type f -name '*.md' -print)

grep -F "Printora é" README.md >/dev/null || fail "README.md deve apresentar o projeto"
grep -F "docs/INSTALL_MACOS.md" README.md >/dev/null || fail "README.md deve apontar para guia macOS"
grep -F "docs/INSTALL_WINDOWS.md" README.md >/dev/null || fail "README.md deve apontar para guia Windows"
grep -F "docs/INSTALL_ANDROID_TERMUX.md" README.md >/dev/null || fail "README.md deve apontar para guia Android/Termux"
grep -F "docs/INSTALL_LINUX_RASPBERRY.md" README.md >/dev/null || fail "README.md deve apontar para guia Linux/Raspberry"
