#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=scripts/mpl_platform.sh
source "${ROOT_DIR}/scripts/mpl_platform.sh"

YES="false"
for arg in "$@"; do
  case "$arg" in
    --yes|-y) YES="true" ;;
    -h|--help) echo "Uso: scripts/install-linux.sh [--yes]"; exit 0 ;;
    *) echo "Argumento inválido: $arg" >&2; exit 2 ;;
  esac
done

if [[ "$(mpl_os)" != "linux" ]] || [[ -n "${TERMUX_VERSION:-}" || "${PREFIX:-}" == *"com.termux"* ]]; then
  echo "Este instalador é para Linux com systemd. Use scripts/install-android-termux.sh no Termux." >&2
  exit 1
fi

if [[ -t 1 ]] && command -v tput >/dev/null 2>&1 && [[ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]]; then
  C_RESET="$(tput sgr0)"; C_OK="$(tput setaf 2)"; C_WARN="$(tput setaf 3)"; C_INFO="$(tput setaf 6)"; C_BOLD="$(tput bold)"
else
  C_RESET=""; C_OK=""; C_WARN=""; C_INFO=""; C_BOLD=""
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
     [ Printora ]
       \  |  /
        \ | /
       -- OK --
TXT
}
ok() { printf '%s\n' "${C_OK}OK:${C_RESET} $*"; }
warn() { printf '%s\n' "${C_WARN}ATENÇÃO:${C_RESET} $*"; }
say() { printf '%s\n' "${C_INFO}$*${C_RESET}"; }
confirm() {
  [[ "$YES" == "true" || "${PRINTORA_ASSUME_YES:-}" == "1" ]] && return 0
  read -r -p "$1 [s/N] " answer
  [[ "$answer" =~ ^[sS](im)?$|^[yY](es)?$ ]]
}

cd "$ROOT_DIR"
banner
say "${C_BOLD}Instalador Linux/Raspberry do Printora${C_RESET}"

if ! mpl_has_systemd; then
  echo "systemd não detectado. Este instalador precisa de systemd para autostart." >&2
  exit 1
fi
ok "systemd encontrado."

missing=()
[[ -n "$(mpl_python)" ]] || missing+=(python3 python3-venv python3-pip)
command -v git >/dev/null 2>&1 || missing+=(git)
command -v curl >/dev/null 2>&1 || missing+=(curl)
command -v rsync >/dev/null 2>&1 || missing+=(rsync)
command -v pkg-config >/dev/null 2>&1 || missing+=(pkg-config)
command -v make >/dev/null 2>&1 || missing+=(build-essential)
if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
  missing+=(nodejs npm)
fi

if [[ "${#missing[@]}" -gt 0 ]]; then
  warn "Dependências ausentes: ${missing[*]}"
  if command -v apt-get >/dev/null 2>&1; then
    if confirm "Posso instalar essas dependências com apt?"; then
      sudo apt-get update
      sudo apt-get install -y "${missing[@]}"
    else
      echo "Instalação interrompida." >&2
      exit 1
    fi
  else
    echo "Gerenciador apt não encontrado. Instale manualmente: ${missing[*]}" >&2
    exit 1
  fi
fi

PYTHON_BIN="$(mpl_python)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "Python 3.11+ ainda não foi encontrado após instalar dependências." >&2
  exit 1
fi
ok "Python compatível: $("$PYTHON_BIN" --version)"
ok "Git: $(git --version)"
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
echo "Abra: http://$(hostname):8069 ou http://127.0.0.1:8069"
