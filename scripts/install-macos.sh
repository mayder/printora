#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

YES="false"
for arg in "$@"; do
  case "$arg" in
    --yes|-y) YES="true" ;;
    -h|--help)
      echo "Uso: scripts/install-macos.sh [--yes]"
      exit 0
      ;;
    *) echo "Argumento inválido: $arg" >&2; exit 2 ;;
  esac
done

if [[ "$(mpl_os)" != "macos" ]]; then
  echo "Este instalador é para macOS." >&2
  exit 1
fi

color_enabled() {
  [[ -t 1 ]] && command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]
}

if color_enabled; then
  C_RESET="$(tput sgr0)"
  C_OK="$(tput setaf 2)"
  C_WARN="$(tput setaf 3)"
  C_INFO="$(tput setaf 6)"
  C_BOLD="$(tput bold)"
else
  C_RESET=""
  C_OK=""
  C_WARN=""
  C_INFO=""
  C_BOLD=""
fi

banner() {
  cat <<'TXT'
 ____       _       _
|  _ \ _ __(_)_ __ | |_ ___  _ __ __ _
| |_) | '__| | '_ \| __/ _ \| '__/ _` |
|  __/| |  | | | | | || (_) | | | (_| |
|_|   |_|  |_|_| |_|\__\___/|_|  \__,_|
TXT
}

success_icon() {
  cat <<'TXT'
        ______
     .-'      '-.
    /  PRINTORA  \
   |   \  OK  /   |
    \   '----'   /
     '-.______.-'
TXT
}

say() { printf '%s\n' "${C_INFO}$*${C_RESET}"; }
ok() { printf '%s\n' "${C_OK}OK:${C_RESET} $*"; }
warn() { printf '%s\n' "${C_WARN}ATENÇÃO:${C_RESET} $*"; }

confirm() {
  local prompt="$1"
  if [[ "$YES" == "true" || "${PRINTORA_ASSUME_YES:-}" == "1" ]]; then
    return 0
  fi
  read -r -p "$prompt [s/N] " answer
  [[ "$answer" =~ ^[sS](im)?$|^[yY](es)?$ ]]
}

require_or_install_brew() {
  if command -v brew >/dev/null 2>&1; then
    ok "Homebrew encontrado: $(command -v brew)"
    return
  fi
  warn "Homebrew não encontrado."
  echo "Instalação interrompida. Instale o Homebrew pelo procedimento oficial verificado e execute novamente." >&2
  exit 1
}

install_brew_packages() {
  local packages=("$@")
  [[ "${#packages[@]}" -gt 0 ]] || return
  warn "Dependências ausentes: ${packages[*]}"
  if confirm "Posso instalar essas dependências com Homebrew?"; then
    brew install "${packages[@]}"
  else
    echo "Instalação interrompida. Dependências obrigatórias ausentes: ${packages[*]}" >&2
    exit 1
  fi
}

cd "$ROOT_DIR"
banner
say "${C_BOLD}Instalador macOS do Printora${C_RESET}"

if xcode-select -p >/dev/null 2>&1; then
  ok "Command Line Tools encontrados."
else
  warn "Command Line Tools não encontrados."
  if confirm "Posso abrir a instalação das Command Line Tools?"; then
    xcode-select --install || true
    echo "Conclua a instalação da Apple e rode este script novamente." >&2
    exit 1
  fi
  exit 1
fi

require_or_install_brew

missing=()
command -v git >/dev/null 2>&1 || missing+=(git)
command -v curl >/dev/null 2>&1 || missing+=(curl)
if [[ -z "$(mpl_python)" ]]; then
  missing+=(python)
fi
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  missing+=(node)
fi
install_brew_packages "${missing[@]}"

PYTHON_BIN="$(mpl_python)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "Python 3.11+ ainda não foi encontrado após instalar dependências." >&2
  exit 1
fi
ok "Python compatível: $("$PYTHON_BIN" --version)"
ok "Git: $(git --version)"
ok "curl: $(curl --version | head -n 1)"
if command -v node >/dev/null 2>&1; then ok "Node atual: $(node --version)"; fi
if command -v npm >/dev/null 2>&1; then ok "npm atual: $(npm --version)"; fi

say "Preparando e instalando o Printora em http://127.0.0.1:8069 ..."
if ! PRINTORA_PORT=8069 PRINTORA_HOST=0.0.0.0 ./scripts/install_printora.sh --apply --yes; then
  warn "Instalação falhou. Rodando diagnóstico."
  PRINTORA_PORT=8069 ./scripts/doctor_install.sh || true
  exit 1
fi

success_icon
ok "Printora instalado."
echo "Abra: http://127.0.0.1:8069"
