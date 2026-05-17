#!/usr/bin/env bash
set -euo pipefail

required_files=(
  "CODEX_PATHS.toml"
  "escopo.md"
  "QUALITY_ROADMAP.md"
  "GOVERNANCA.md"
  "DEMANDAS.md"
  "TESTS.md"
  "BUGS.md"
  "README.md"
  ".gitignore"
)

for file in "${required_files[@]}"; do
  if [[ ! -s "$file" ]]; then
    echo "Missing or empty required file: $file" >&2
    exit 1
  fi
done

if ! grep -q 'check_script = "check.sh"' CODEX_PATHS.toml; then
  echo "CODEX_PATHS.toml does not point to check.sh" >&2
  exit 1
fi

if grep -RInE '(password|passwd|token|secret|api[_-]?key|private[_-]?key)\s*[:=]\s*[^ <]' . \
  --exclude-dir=.git \
  --exclude=check.sh \
  --exclude=BUGS.md; then
  echo "Potential secret found. Review before continuing." >&2
  exit 1
fi

echo "MayderPrintLab checks passed."
