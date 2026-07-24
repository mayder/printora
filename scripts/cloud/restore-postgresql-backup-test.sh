#!/usr/bin/env bash
set -euo pipefail

[[ "$(id -u)" -eq 0 ]] || { echo "ERRO: execute como root" >&2; exit 1; }
base_path="${PRINTORA_BASE_PATH:-/var/www/print3dmaker.xyz}"
config="$base_path/shared/backup-target.conf"
[[ -s "$config" ]] || { echo "configuração de backup externo ausente" >&2; exit 1; }
command -v restic >/dev/null || { echo "restic ausente" >&2; exit 1; }
command -v pg_config >/dev/null || { echo "pg_config ausente" >&2; exit 1; }

set -a
source "$config"
set +a

restore_root="$(mktemp -d /var/lib/postgresql/printora-restore-test.XXXXXX)"
cluster="$restore_root/cluster"
socket_dir="$restore_root/socket"
restored="$restore_root/restored"
export RESTIC_CACHE_DIR="$restore_root/restic-cache"
started=0
cleanup() {
  if [[ "$started" -eq 1 ]]; then
    runuser -u postgres -- "$pg_bin/pg_ctl" -D "$cluster" -m immediate -w stop >/dev/null || true
  fi
  case "$restore_root" in
    /var/lib/postgresql/printora-restore-test.*) rm -rf -- "$restore_root" ;;
    *) echo "diretório temporário inesperado; limpeza recusada" >&2 ;;
  esac
}
trap cleanup EXIT

restic restore latest --tag printora-cloud-postgresql --target "$restored" \
  --include '/tmp/**/base/base.tar.zst' \
  --include '/tmp/**/base/pg_wal.tar*' \
  --include '/tmp/**/manifest.json' \
  --include '/tmp/**/printora-postgresql.dump' \
  --include '/tmp/**/configuration/**' \
  --include '/tmp/**/object-storage/**'
dump="$(find "$restored" -type f -name printora-postgresql.dump -print -quit)"
manifest="$(find "$restored" -type f -name manifest.json -print -quit)"
base_tar="$(find "$restored" -type f -name base.tar.zst -print -quit)"
wal_tar="$(find "$restored" -type f \( -name pg_wal.tar.zst -o -name pg_wal.tar \) -print -quit)"
object_manifest="$(find "$restored" -type f -path '*/object-storage/object-manifest.json' -print -quit)"
configuration_dir="$(find "$restored" -type d -name configuration -print -quit)"
[[ -n "$dump" && -n "$manifest" && -n "$base_tar" && -n "$wal_tar" && -n "$object_manifest" && -n "$configuration_dir" ]] || {
  echo "backup restaurado incompleto" >&2
  exit 1
}
python3 - "$manifest" "$configuration_dir" <<'PY'
import hashlib
import json
import pathlib
import sys

manifest = json.loads(pathlib.Path(sys.argv[1]).read_text())
root = pathlib.Path(sys.argv[2])
expected = manifest.get("configuration_sha256", {})
if not manifest.get("recovery_custody_id") or len(expected) != int(manifest.get("configuration_file_count", -1)):
    raise SystemExit("manifesto de configuração/custódia inválido")
for name, digest in expected.items():
    path = root / name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise SystemExit(f"configuração restaurada divergente: {name}")
print(json.dumps({"configuration_files_restored": len(expected), "configuration_checksums": "passed"}, sort_keys=True))
PY
expected_sha256="$(python3 - "$manifest" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    print(json.load(source)["dump_sha256"])
PY
)"
last_archived_wal="$(python3 - "$manifest" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as source:
    print(json.load(source)["last_archived_wal"])
PY
)"
continuous_state=/var/lib/printora-cloud/recovery/wal-sync.json
[[ -s "$continuous_state" ]] || { echo "estado do WAL contínuo ausente" >&2; exit 1; }
continuous_wal="$(python3 - "$continuous_state" <<'PY'
import json
import sys

print(json.load(open(sys.argv[1]))["uploaded_wal"])
PY
)"
[[ "$continuous_wal" =~ ^[0-9A-F]{24}$ ]] || { echo "WAL contínuo inválido" >&2; exit 1; }
mapfile -t wal_paths < <(
  restic ls latest --tag printora-cloud-wal --json \
    | python3 -c '
import json
import pathlib
import re
import sys

first, last = sys.argv[1:3]
pattern = re.compile(r"^[0-9A-F]{24}$")
paths = []
for line in sys.stdin:
    payload = json.loads(line)
    path = payload.get("path", "")
    name = pathlib.PurePosixPath(path).name
    if pattern.fullmatch(name) and first <= name <= last:
        paths.append(path)
for path in sorted(set(paths)):
    print(path)
' "$last_archived_wal" "$continuous_wal"
)
[[ "${#wal_paths[@]}" -gt 0 ]] || { echo "faixa WAL externa ausente" >&2; exit 1; }
wal_includes=()
for wal_path in "${wal_paths[@]}"; do
  wal_includes+=(--include "$wal_path")
done
restic restore latest --tag printora-cloud-wal --target "$restored" \
  "${wal_includes[@]}"
last_archived_wal="$continuous_wal"
[[ "$last_archived_wal" =~ ^[0-9A-F]{24}$ ]] || { echo "WAL final inválido" >&2; exit 1; }
archive_dir="$(find "$restored" -type d -name printora-wal-archive -print -quit)"
[[ -s "$archive_dir/$last_archived_wal" ]] || { echo "WAL final ausente" >&2; exit 1; }
"$(pg_config --bindir)/pg_waldump" -n 1 "$archive_dir/$last_archived_wal" >/dev/null
actual_sha256="$(sha256sum "$dump" | awk '{print $1}')"
[[ "$actual_sha256" == "$expected_sha256" ]] || { echo "checksum do dump divergente" >&2; exit 1; }
expected_object_manifest_sha256="$(python3 - "$manifest" <<'PY'
import json
import sys
print(json.load(open(sys.argv[1]))["object_manifest_sha256"])
PY
)"
[[ "$(sha256sum "$object_manifest" | awk '{print $1}')" == "$expected_object_manifest_sha256" ]] || {
  echo "checksum do manifesto de objetos divergente" >&2
  exit 1
}
python3 - "$object_manifest" <<'PY'
import hashlib
import json
import pathlib
import sys

manifest_path = pathlib.Path(sys.argv[1])
payload = json.loads(manifest_path.read_text())
versions = 0
for entry in payload.get("entries", []):
    if entry.get("kind") != "version":
        continue
    versions += 1
    path = manifest_path.parent / entry["relative_path"]
    if not path.is_file() or path.stat().st_size != int(entry["size_bytes"]):
        raise SystemExit("objeto restaurado ausente ou com tamanho divergente")
    hasher = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            hasher.update(chunk)
    digest = hasher.hexdigest()
    if digest != entry["sha256"]:
        raise SystemExit("checksum do objeto restaurado divergente")
if versions != int(payload.get("version_count", -1)):
    raise SystemExit("contagem de versões restauradas divergente")
print(json.dumps({"object_versions_restored": versions, "object_files_checksum": "passed"}, sort_keys=True))
PY

pg_bin="$(pg_config --bindir)"
chown postgres:postgres "$restore_root"
chmod 0700 "$restore_root"
install -d -o postgres -g postgres -m 0700 "$cluster" "$socket_dir"
chown -R postgres:postgres "$restored"
runuser -u postgres -- tar --zstd -xf "$base_tar" -C "$cluster"
install -d -o postgres -g postgres -m 0700 "$cluster/pg_wal"
case "$wal_tar" in
  *.zst) runuser -u postgres -- tar --zstd -xf "$wal_tar" -C "$cluster/pg_wal" ;;
  *.tar) runuser -u postgres -- tar -xf "$wal_tar" -C "$cluster/pg_wal" ;;
  *) echo "formato do arquivo pg_wal inesperado" >&2; exit 1 ;;
esac
cat > "$cluster/postgresql.conf" <<EOF
listen_addresses = ''
port = 5432
unix_socket_directories = '$socket_dir'
archive_mode = off
fsync = off
full_page_writes = off
synchronous_commit = off
restore_command = 'cp $archive_dir/%f %p'
recovery_target_action = 'promote'
EOF
cat > "$cluster/pg_hba.conf" <<'EOF'
local all all trust
EOF
touch "$cluster/recovery.signal"
chown -R postgres:postgres "$cluster"
started=1
runuser -u postgres -- "$pg_bin/pg_ctl" -D "$cluster" -t 300 -w start >/dev/null
export PGHOST="$socket_dir" PGPORT=5432 PGUSER=postgres PGDATABASE=postgres
for _attempt in $(seq 1 60); do
  if [[ "$(runuser -u postgres -- "$pg_bin/psql" -X -Atqc 'SELECT pg_is_in_recovery()')" == "f" ]]; then
    break
  fi
  sleep 1
done
[[ "$(runuser -u postgres -- "$pg_bin/psql" -X -Atqc 'SELECT pg_is_in_recovery()')" == "f" ]] || {
  echo "restore físico não promoveu dentro do limite" >&2
  exit 1
}
export PGDATABASE=printora_cloud
replayed_wal="$(runuser -u postgres -- "$pg_bin/psql" -X -Atqc \
  "SELECT COALESCE(pg_walfile_name(pg_last_wal_replay_lsn()), '')")"
[[ "$replayed_wal" =~ ^[0-9A-F]{24}$ && \
   ( "$replayed_wal" == "$last_archived_wal" || "$replayed_wal" > "$last_archived_wal" ) ]] || {
  echo "WAL externo contínuo não foi reproduzido integralmente" >&2
  exit 1
}

runuser -u postgres -- "$pg_bin/psql" -X -v ON_ERROR_STOP=1 -At <<'SQL'
DO $$
DECLARE
    application_tables integer;
    schema_revisions integer;
    invalid_foreign_keys integer;
BEGIN
    SELECT COUNT(*) INTO application_tables
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    SELECT COUNT(*) INTO schema_revisions FROM schema_versions;
    SELECT COUNT(*) INTO invalid_foreign_keys
    FROM pg_constraint
    WHERE contype = 'f' AND NOT convalidated;
    IF application_tables = 0 OR schema_revisions = 0 OR invalid_foreign_keys <> 0 THEN
        RAISE EXCEPTION 'restore inválido: tables=%, revisions=%, invalid_fks=%',
            application_tables, schema_revisions, invalid_foreign_keys;
    END IF;
END
$$;
SELECT json_build_object(
    'database', current_database(),
    'in_recovery', pg_is_in_recovery(),
    'tables', (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'),
    'schema_versions', (SELECT COUNT(*) FROM schema_versions),
    'invalid_foreign_keys', (SELECT COUNT(*) FROM pg_constraint WHERE contype = 'f' AND NOT convalidated)
);
SQL
metadata_csv="$restore_root/cloud-objects.csv"
runuser -u postgres -- "$pg_bin/psql" -X --csv -c \
  'SELECT bucket_name, object_key, sha256, size_bytes FROM cloud_objects ORDER BY id' > "$metadata_csv"
python3 - "$object_manifest" "$metadata_csv" <<'PY'
import csv
import json
import pathlib
import sys

manifest = json.loads(pathlib.Path(sys.argv[1]).read_text())
versions = {
    (entry["bucket"], entry["key"], entry["sha256"], int(entry["size_bytes"]))
    for entry in manifest.get("entries", [])
    if entry.get("kind") == "version"
}
with open(sys.argv[2], newline="", encoding="utf-8") as source:
    metadata = list(csv.DictReader(source))
missing = [
    (row["bucket_name"], row["object_key"])
    for row in metadata
    if (row["bucket_name"], row["object_key"], row["sha256"], int(row["size_bytes"])) not in versions
]
if missing:
    raise SystemExit(f"metadado sem conteúdo restaurado: {len(missing)}")
print(json.dumps({"canonical_objects": len(metadata), "metadata_content_reconciliation": "passed"}, sort_keys=True))
PY

PRINTORA_RUNTIME_PROFILE=cloud \
PRINTORA_DATABASE_URL="postgresql://postgres@/printora_cloud?host=$socket_dir&port=5432" \
PRINTORA_DATA_DIR="$restore_root/app-data" \
PYTHONPATH="$base_path/current/backend" \
  "$base_path/current/venv/bin/python" /usr/local/libexec/printora-cloud/search-rebuild.py

echo "restore físico PostgreSQL/WAL, objetos e rebuild da busca validados em destino isolado; aplicação não foi iniciada"
