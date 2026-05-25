#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

YES="false"
for arg in "$@"; do
  case "$arg" in
    --yes|-y) YES="true" ;;
    -h|--help) echo "Uso: scripts/install-android-termux.sh [--yes]"; exit 0 ;;
    *) echo "Argumento inválido: $arg" >&2; exit 2 ;;
  esac
done

if [[ -z "${TERMUX_VERSION:-}" && "${PREFIX:-}" != *"com.termux"* ]]; then
  echo "Este instalador deve rodar dentro do Termux." >&2
  exit 1
fi

if [[ -t 1 ]]; then
  C_RESET=$'\033[0m'; C_OK=$'\033[32m'; C_WARN=$'\033[33m'; C_INFO=$'\033[36m'; C_BOLD=$'\033[1m'
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
   .----------------.
   | Printora  OK   |
   '----------------'
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
say "${C_BOLD}Instalador Android/Termux do Printora${C_RESET}"

missing=()
for command_name in python node npm git ssh tmux rustc clang make pkg-config curl termux-wake-lock; do
  command -v "$command_name" >/dev/null 2>&1 || missing+=("$command_name")
done

if [[ "${#missing[@]}" -gt 0 ]]; then
  warn "Dependências ausentes: ${missing[*]}"
  if confirm "Posso instalar dependências pelo pkg?"; then
    yes | pkg update
    yes | pkg install python nodejs git openssh tmux rust clang make pkg-config curl termux-api
  else
    echo "Instalação interrompida." >&2
    exit 1
  fi
fi

ok "Python: $(python --version)"
ok "Node: $(node --version)"
ok "Git: $(git --version)"
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true

say "Preparando e instalando o Printora em http://printora.local:8069 ..."
if ! PRINTORA_PORT=8069 PRINTORA_DATA_DIR="$HOME/.local/share/printora" ./scripts/install_printora.sh --apply --yes; then
  warn "Instalação falhou. Rodando diagnóstico."
  PRINTORA_PORT=8069 ./scripts/doctor_install.sh || true
  exit 1
fi

success_icon
ok "Printora instalado."
echo "Abra: http://printora.local:8069"
