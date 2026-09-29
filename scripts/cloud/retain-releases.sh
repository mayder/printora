#!/usr/bin/env bash
set -euo pipefail

base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
release_root="$base_path/releases"
mode="${1:---dry-run}"

case "$mode" in
  --dry-run|--apply) ;;
  *) echo "[printora-cloud] ERRO: use --dry-run ou --apply" >&2; exit 2 ;;
esac

[[ "$base_path" == /* && "$base_path" != "/" ]] \
  || { echo "[printora-cloud] ERRO: base path inseguro" >&2; exit 1; }
[[ -d "$release_root" && ! -L "$release_root" ]] \
  || { echo "[printora-cloud] ERRO: diretório de releases inválido" >&2; exit 1; }
if [[ "$mode" == "--apply" && "$(id -u)" -ne 0 ]]; then
  echo "[printora-cloud] ERRO: aplicação exige root via sudo controlado" >&2
  exit 1
fi

protected_targets=()
protect_link() {
  local link="$1"
  local target
  [[ -L "$link" ]] || return 0
  target="$(readlink -f "$link")"
  [[ "$target" == "$release_root/"* && -d "$target" ]] \
    || { echo "[printora-cloud] ERRO: link fora de releases: $link" >&2; exit 1; }
  local existing
  for existing in "${protected_targets[@]:-}"; do
    [[ "$existing" == "$target" ]] && return 0
  done
  protected_targets+=("$target")
}

protect_link "$base_path/current"
for slot in blue green replica; do
  protect_link "$base_path/slots/$slot"
done

[[ -L "$base_path/current" && "${#protected_targets[@]}" -ge 2 ]] || {
  echo "[printora-cloud] ERRO: topologia ativa/rollback incompleta; retenção recusada" >&2
  exit 1
}

before_kb="$(du -sk "$release_root" | awk '{print $1}')"
removed=0
skipped=0
while IFS= read -r -d '' candidate; do
  candidate="$(readlink -f "$candidate")"
  [[ "$candidate" == "$release_root/"* ]] \
    || { echo "[printora-cloud] ERRO: candidato fora de releases" >&2; exit 1; }
  for protected_target in "${protected_targets[@]}"; do
    if [[ "$protected_target" == "$candidate" ]]; then
      echo "[printora-cloud] release=$(basename "$candidate") action=preserve reason=linked"
      continue 2
    fi
  done
  if [[ ! "$(basename "$candidate")" =~ ^[0-9a-f]{7,64}$ ]]; then
    echo "[printora-cloud] release=$(basename "$candidate") action=skip reason=invalid_name"
    skipped=$((skipped + 1))
    continue
  fi
  if [[ "$mode" == "--apply" ]]; then
    rm -rf -- "$candidate"
    echo "[printora-cloud] release=$(basename "$candidate") action=removed reason=unlinked"
  else
    echo "[printora-cloud] release=$(basename "$candidate") action=would_remove reason=unlinked"
  fi
  removed=$((removed + 1))
done < <(find -P "$release_root" -mindepth 1 -maxdepth 1 -type d -print0)

after_kb="$(du -sk "$release_root" | awk '{print $1}')"
echo "[printora-cloud] mode=${mode#--} protected=${#protected_targets[@]} candidates=$removed skipped=$skipped before_kb=$before_kb after_kb=$after_kb status=ok"
