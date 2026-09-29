#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MINIO_TAG=RELEASE.2025-10-15T17-29-55Z
MC_TAG=RELEASE.2025-08-13T08-35-41Z
CONFIG_DIR=/etc/printora-object-storage
DATA_DIR=/var/www/print3dmaker.xyz/shared/object-storage

if ! command -v go >/dev/null 2>&1; then
  apt-get update
  DEBIAN_FRONTEND=noninteractive apt-get install -y golang-go git
fi
build_dir="$(mktemp -d /tmp/printora-minio-build.XXXXXX)"
trap 'rm -rf -- "$build_dir"' EXIT
if [[ ! -x /usr/local/bin/minio-printora ]]; then
  GOBIN="$build_dir" GOTOOLCHAIN=go1.24.8+auto go install "github.com/minio/minio@$MINIO_TAG"
  install -o root -g root -m 0755 "$build_dir/minio" /usr/local/bin/minio-printora
fi
if [[ ! -x /usr/local/bin/mcli-printora ]]; then
  GOBIN="$build_dir" GOTOOLCHAIN=go1.23.10+auto go install "github.com/minio/mc@$MC_TAG"
  install -o root -g root -m 0755 "$build_dir/mc" /usr/local/bin/mcli-printora
fi

id minio-printora >/dev/null 2>&1 || useradd --system --home-dir /var/lib/minio-printora --create-home --shell /usr/sbin/nologin minio-printora
install -d -o root -g minio-printora -m 0750 "$CONFIG_DIR"
install -d -o minio-printora -g minio-printora -m 0750 "$DATA_DIR"
install -o root -g root -m 0644 "$ROOT_DIR/packaging/systemd/minio-printora.service" /etc/systemd/system/minio-printora.service

credentials="$CONFIG_DIR/credentials.env"
if [[ ! -s "$credentials" ]]; then
  umask 0077
  printf 'MINIO_ROOT_USER=PR%s\n' "$(openssl rand -hex 12)" > "$credentials"
  printf 'MINIO_ROOT_PASSWORD=%s\n' "$(openssl rand -hex 32)" >> "$credentials"
  printf 'PRINTORA_OBJECT_STORAGE_ACCESS_KEY=PA%s\n' "$(openssl rand -hex 12)" >> "$credentials"
  printf 'PRINTORA_OBJECT_STORAGE_SECRET_KEY=%s\n' "$(openssl rand -hex 32)" >> "$credentials"
fi
set -a
source "$credentials"
set +a
install -o root -g minio-printora -m 0640 /dev/null "$CONFIG_DIR/minio.env"
{
  printf 'MINIO_ROOT_USER=%s\n' "$MINIO_ROOT_USER"
  printf 'MINIO_ROOT_PASSWORD=%s\n' "$MINIO_ROOT_PASSWORD"
  printf 'MINIO_BROWSER=off\n'
  printf 'MINIO_API_OBJECT_MAX_VERSIONS=100\n'
} > "$CONFIG_DIR/minio.env"
chown root:minio-printora "$CONFIG_DIR/minio.env"
chmod 0640 "$CONFIG_DIR/minio.env"
install -o root -g deploy -m 0640 /dev/null /etc/printora-cloud/object-storage.env
{
  printf 'PRINTORA_OBJECT_STORAGE_MODE=s3\n'
  printf 'PRINTORA_OBJECT_STORAGE_ENDPOINT_URL=http://127.0.0.1:9100\n'
  printf 'PRINTORA_OBJECT_STORAGE_REGION=us-east-1\n'
  printf 'PRINTORA_OBJECT_STORAGE_ACCESS_KEY=%s\n' "$PRINTORA_OBJECT_STORAGE_ACCESS_KEY"
  printf 'PRINTORA_OBJECT_STORAGE_SECRET_KEY=%s\n' "$PRINTORA_OBJECT_STORAGE_SECRET_KEY"
} > /etc/printora-cloud/object-storage.env
chown root:deploy /etc/printora-cloud/object-storage.env
chmod 0640 /etc/printora-cloud/object-storage.env

systemctl daemon-reload
systemctl enable --now minio-printora.service
for _attempt in $(seq 1 60); do
  curl -fsS --max-time 2 http://127.0.0.1:9100/minio/health/ready >/dev/null && break
  sleep 1
done
curl -fsS --max-time 2 http://127.0.0.1:9100/minio/health/ready >/dev/null

mc_dir="$(mktemp -d /tmp/printora-mcli.XXXXXX)"
trap 'rm -rf -- "$build_dir" "$mc_dir"' EXIT
mc=(/usr/local/bin/mcli-printora --config-dir "$mc_dir")
"${mc[@]}" alias set printora http://127.0.0.1:9100 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" >/dev/null
for bucket in printora-quarantine printora-objects printora-artifacts; do
  "${mc[@]}" mb --ignore-existing "printora/$bucket" >/dev/null
  "${mc[@]}" version enable "printora/$bucket" >/dev/null
  "${mc[@]}" quota set --size 30GiB "printora/$bucket" >/dev/null
done
if ! "${mc[@]}" admin user info printora "$PRINTORA_OBJECT_STORAGE_ACCESS_KEY" >/dev/null 2>&1; then
  "${mc[@]}" admin user add printora "$PRINTORA_OBJECT_STORAGE_ACCESS_KEY" "$PRINTORA_OBJECT_STORAGE_SECRET_KEY" >/dev/null
fi
if ! "${mc[@]}" admin policy info printora printora-app >/dev/null 2>&1; then
  "${mc[@]}" admin policy create printora printora-app "$ROOT_DIR/packaging/minio/printora-app-policy.json" >/dev/null
fi
"${mc[@]}" admin policy attach printora printora-app --user "$PRINTORA_OBJECT_STORAGE_ACCESS_KEY" >/dev/null
"${mc[@]}" anonymous set none printora/printora-quarantine >/dev/null
"${mc[@]}" anonymous set none printora/printora-objects >/dev/null
"${mc[@]}" anonymous set none printora/printora-artifacts >/dev/null

echo "MinIO privado, versionado e com chave de aplicação mínima ativo em loopback."
