#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }

endpoint=http://127.0.0.1:9100
credentials=/etc/printora-object-storage/credentials.env
[[ -s "$credentials" ]] || { echo "ERRO: credenciais do storage ausentes" >&2; exit 1; }

printf 'service='
systemctl is-active minio-printora.service
printf 'enabled='
systemctl is-enabled minio-printora.service
printf 'health='
curl -fsS -o /dev/null -w '%{http_code}\n' "$endpoint/minio/health/ready"
ss -lnt | awk '$4 ~ /127.0.0.1:9100|127.0.0.1:9101/ {print "listen=" $4}'
printf 'non_loopback_bind_count='
ss -lnt | awk '$4 ~ /(^|:)9100$|(^|:)9101$/ && $4 !~ /127.0.0.1|\[::1\]/ {count++} END {print count+0}'
go version -m /usr/local/bin/minio-printora | awk '$1 == "path" || $1 == "mod" {print "minio_" $1 "=" $2 " " $3}'
go version -m /usr/local/bin/mcli-printora | awk '$1 == "path" || $1 == "mod" {print "mcli_" $1 "=" $2 " " $3}'

set -a
# shellcheck disable=SC1090
source "$credentials"
set +a

probe_dir="$(mktemp -d /tmp/pkg90-storage-proof.XXXXXX)"
trap 'rm -rf -- "$probe_dir"' EXIT
mc=(/usr/local/bin/mcli-printora --config-dir "$probe_dir/mc")
"${mc[@]}" alias set root "$endpoint" "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
"${mc[@]}" alias set app "$endpoint" "$PRINTORA_OBJECT_STORAGE_ACCESS_KEY" "$PRINTORA_OBJECT_STORAGE_SECRET_KEY" >/dev/null

for bucket in printora-quarantine printora-objects printora-artifacts; do
  printf '%s_versioning=' "$bucket"
  "${mc[@]}" version info "root/$bucket" | tr '\n' ' '
  echo
  printf '%s_quota=' "$bucket"
  "${mc[@]}" quota info "root/$bucket" | tr '\n' ' '
  echo
done

head -c 1048576 /dev/urandom > "$probe_dir/probe.bin"
sha="$(sha256sum "$probe_dir/probe.bin" | awk '{print $1}')"
key="pkg90-proof/$sha.bin"
"${mc[@]}" cp "$probe_dir/probe.bin" "app/printora-quarantine/$key" >/dev/null
"${mc[@]}" cp "app/printora-quarantine/$key" "app/printora-objects/$key" >/dev/null
"${mc[@]}" cat "app/printora-objects/$key" > "$probe_dir/restored.bin"
printf 'checksum_match='
[[ "$(sha256sum "$probe_dir/restored.bin" | awk '{print $1}')" == "$sha" ]] && echo yes
"${mc[@]}" rm "app/printora-quarantine/$key" >/dev/null
echo 'quarantine_cleanup=allowed'
if "${mc[@]}" rm "app/printora-objects/$key" >/dev/null 2>&1; then
  echo 'promoted_delete=unexpectedly_allowed'
  exit 1
fi
echo 'promoted_delete=denied'
printf 'promoted_object='
"${mc[@]}" stat "app/printora-objects/$key" --json | jq -r '(.key // .name // "present") + " size=" + (.size|tostring)'
printf 'anonymous_http='
curl -sS -o /dev/null -w '%{http_code}\n' "$endpoint/printora-objects/$key"
systemctl show minio-printora.service -p MemoryCurrent -p MemoryMax -p TasksCurrent -p TasksMax --no-pager
printf 'data_usage='
du -sh /var/www/print3dmaker.xyz/shared/object-storage | cut -f1
