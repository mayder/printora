#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="plan"
YES="false"

usage() {
  cat <<'USAGE'
Uso:
  scripts/install_printora.sh --plan
  scripts/install_printora.sh --apply --yes

Instalação simples:
  1. prepara dependências sem trocar Node global;
  2. builda backend/frontend;
  3. configura o Printora para subir automaticamente no boot.
USAGE
}

is_termux() {
  [[ -n "${TERMUX_VERSION:-}" || "${PREFIX:-}" == *"com.termux"* ]]
}

print_dependency_plan() {
  if is_termux && command -v pkg >/dev/null 2>&1; then
    echo "Dependências Termux: python nodejs git openssh tmux rust clang make pkg-config curl termux-api"
    return
  fi
  if [[ "$(uname -s)" == "Linux" ]] && command -v apt-get >/dev/null 2>&1; then
    echo "Dependências apt: python3 python3-venv python3-pip git curl rsync build-essential pkg-config"
    echo "Node global não será alterado; Node compatível será instalado via nvm se necessário."
    return
  fi
  if [[ "$(uname -s)" == "Darwin" ]]; then
    echo "Dependências macOS esperadas: python3 git curl; Node será validado e isolado via nvm se necessário."
  fi
}

install_system_dependencies() {
  if is_termux && command -v pkg >/dev/null 2>&1; then
    yes | pkg update
    yes | pkg install python nodejs git openssh tmux rust clang make pkg-config curl termux-api
    return
  fi
  if [[ "$(uname -s)" == "Linux" ]] && command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update
    sudo apt-get install -y python3 python3-venv python3-pip git curl rsync build-essential pkg-config
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --plan) MODE="plan"; shift ;;
    --apply) MODE="apply"; shift ;;
    --yes) YES="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Argumento inválido: $1" >&2; usage >&2; exit 2 ;;
  esac
done

cd "$ROOT_DIR"

if [[ "$MODE" == "plan" ]]; then
  print_dependency_plan
  scripts/bootstrap_dev.sh
  scripts/install_printora_autostart.sh --plan
  exit 0
fi

[[ "$YES" == "true" || "${PRINTORA_ASSUME_YES:-}" == "1" ]] || {
  echo "--apply exige --yes." >&2
  exit 1
}

install_system_dependencies
scripts/bootstrap_dev.sh --apply
scripts/install_printora_autostart.sh --apply --yes

echo "Printora instalado e configurado para iniciar automaticamente."
