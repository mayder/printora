#!/usr/bin/env bash
set -euo pipefail

mpl_os() {
  local uname_s
  uname_s="$(uname -s)"
  case "${uname_s}" in
    Darwin) echo "macos" ;;
    Linux) echo "linux" ;;
    MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
    *) echo "unknown" ;;
  esac
}

mpl_has_systemd() {
  [[ -d /run/systemd/system ]] && command -v systemctl >/dev/null 2>&1
}

mpl_data_dir() {
  local os_name
  os_name="$(mpl_os)"
  case "${os_name}" in
    macos) echo "${HOME}/Library/Application Support/Printora" ;;
    windows) echo "${LOCALAPPDATA:-${HOME}/AppData/Local}/Printora" ;;
    *) echo "${HOME}/.local/share/printora" ;;
  esac
}

mpl_python() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi
  echo ""
}

mpl_require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Comando obrigatório não encontrado: ${command_name}" >&2
    return 1
  fi
}
