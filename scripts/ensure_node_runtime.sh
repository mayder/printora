#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="plan"
NODE_VERSION="${PRINTORA_NODE_VERSION:-$(tr -d '[:space:]' < "${ROOT_DIR}/.node-version")}"
NPM_VERSION="${PRINTORA_NPM_VERSION:-11.7.0}"
NVM_VERSION="${PRINTORA_NVM_VERSION:-v0.40.3}"
ENV_FILE="${ROOT_DIR}/.printora-node-env"

usage() {
  cat <<'USAGE'
Uso:
  scripts/ensure_node_runtime.sh --plan
  scripts/ensure_node_runtime.sh --apply

Garante Node compatível para o frontend sem alterar o Node global do sistema.
Quando necessário, instala Node via nvm no usuário atual e grava .printora-node-env.
USAGE
}

node_version_supported() {
  local version="$1" major minor patch
  if [[ ! "$version" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    return 1
  fi
  major=$((10#${BASH_REMATCH[1]}))
  minor=$((10#${BASH_REMATCH[2]}))
  patch=$((10#${BASH_REMATCH[3]}))
  (( patch >= 0 ))
  (( major == 22 && minor == 22 )) && return 0
  return 1
}

npm_version_supported() {
  local version="$1" major minor
  if [[ ! "$version" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+) ]]; then
    return 1
  fi
  major=$((10#${BASH_REMATCH[1]}))
  minor=$((10#${BASH_REMATCH[2]}))
  (( major == 11 && minor == 7 ))
}

node_path="$(command -v node 2>/dev/null || true)"
npm_path="$(command -v npm 2>/dev/null || true)"
node_version=""
npm_version=""
node_supported="false"
if [[ -n "$node_path" ]]; then
  node_version="$("$node_path" --version 2>/dev/null || true)"
  if node_version_supported "$node_version"; then
    node_supported="true"
  fi
fi
if [[ -n "$npm_path" ]]; then
  npm_version="$("$npm_path" --version 2>/dev/null || true)"
  if ! npm_version_supported "$npm_version"; then
    node_supported="false"
  fi
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan) MODE="plan"; shift ;;
    --apply) MODE="apply"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Argumento inválido: $1" >&2; usage >&2; exit 2 ;;
  esac
done

cat <<PLAN
Node runtime Printora
mode=$MODE
node=${node_path:-missing}
npm=${npm_path:-missing}
node_version=${node_version:-missing}
npm_version=${npm_version:-missing}
node_supported=$node_supported
env_file=$ENV_FILE
action=$(if [[ "$node_supported" == "true" && -n "$npm_path" ]]; then echo "usar Node atual"; else echo "instalar Node $NODE_VERSION via nvm para o Printora"; fi)
PLAN

if [[ "$MODE" == "plan" ]]; then
  exit 0
fi

if [[ "$node_supported" == "true" && -n "$npm_path" ]]; then
  rm -f "$ENV_FILE"
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "curl não encontrado para instalar nvm." >&2
  exit 1
fi

nvm_dir="${NVM_DIR:-$HOME/.nvm}"
if [[ ! -s "$nvm_dir/nvm.sh" ]]; then
  curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/$NVM_VERSION/install.sh" | PROFILE=/dev/null bash
fi

# shellcheck source=/dev/null
. "$nvm_dir/nvm.sh"
nvm install "$NODE_VERSION"
nvm use "$NODE_VERSION" >/dev/null
npm install --global "npm@$NPM_VERSION"

node_path="$(command -v node)"
npm_path="$(command -v npm)"
node_version="$("$node_path" --version)"
npm_version="$("$npm_path" --version)"
if ! node_version_supported "$node_version"; then
  echo "Node instalado via nvm continua incompatível: $node_version" >&2
  exit 1
fi
if ! npm_version_supported "$npm_version"; then
  echo "npm instalado via nvm continua incompatível: $npm_version" >&2
  exit 1
fi

cat >"$ENV_FILE" <<ENV
export PRINTORA_NODE_BIN="$node_path"
export PRINTORA_NPM_BIN="$npm_path"
export PATH="$(dirname "$node_path"):\$PATH"
ENV

echo "Node local do Printora pronto: $node_version"
