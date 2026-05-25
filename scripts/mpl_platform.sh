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
  local candidate
  for candidate in \
    "${PRINTORA_PYTHON_BIN:-}" \
    python3.14 \
    python3.13 \
    python3.12 \
    python3.11 \
    /opt/homebrew/opt/python@3.14/bin/python3 \
    /opt/homebrew/opt/python@3.13/bin/python3 \
    /opt/homebrew/opt/python@3.12/bin/python3 \
    /opt/homebrew/opt/python@3.11/bin/python3 \
    /usr/local/opt/python@3.14/bin/python3 \
    /usr/local/opt/python@3.13/bin/python3 \
    /usr/local/opt/python@3.12/bin/python3 \
    /usr/local/opt/python@3.11/bin/python3 \
    python3 \
    python; do
    [[ -n "${candidate}" ]] || continue
    if command -v "${candidate}" >/dev/null 2>&1 && mpl_python_supported "${candidate}"; then
      command -v "${candidate}"
      return
    fi
  done
  echo ""
}

mpl_python_supported() {
  local python_bin="$1"
  "${python_bin}" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 11) else 1)
PY
}

mpl_require_command() {
  local command_name="$1"
  if ! command -v "${command_name}" >/dev/null 2>&1; then
    echo "Comando obrigatório não encontrado: ${command_name}" >&2
    return 1
  fi
}
