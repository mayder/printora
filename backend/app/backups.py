import json
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from pydantic import BaseModel, ConfigDict, Field

from app.database import connect_database


DEFAULT_INCLUDE_PATTERNS = ["**/*.cfg", "**/*.conf", "**/*.md", "**/*.json"]
DEFAULT_EXCLUDE_PATTERNS = [
    "**/.git/**",
    "**/__pycache__/**",
    "**/*.log",
    "**/*.tmp",
    "**/*.bak",
    "**/*backup*",
    "**/*secret*",
    "**/*token*",
    "**/*password*",
    "moonraker.asvc",
]


class BackupPolicyCreate(BaseModel):
    name: str = Field(default="Config backup", min_length=1, max_length=80)
    source_path: str = Field(default="/home/pi/printer_data/config", min_length=1, max_length=300)
    destination_path: str = Field(
        default="/home/pi/printer_data/backups/printora",
        min_length=1,
        max_length=300,
    )
    include_patterns: list[str] = Field(default_factory=lambda: DEFAULT_INCLUDE_PATTERNS.copy())
    exclude_patterns: list[str] = Field(default_factory=lambda: DEFAULT_EXCLUDE_PATTERNS.copy())
    dry_run_only: bool = True


class BackupPolicyRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    name: str
    source_path: str
    destination_path: str
    include_patterns: list[str]
    exclude_patterns: list[str]
    dry_run_only: bool
    is_active: bool
    created_at: str
    updated_at: str


class BackupRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    policy_id: int
    created_at: str
    status: str
    dry_run: bool
    source_path: str
    destination_path: str
    include_patterns: list[str]
    exclude_patterns: list[str]
    total_files: int
    total_bytes: int
    message: str


class BackupArchiveCompareRequest(BaseModel):
    base_archive_path: str = Field(min_length=1, max_length=400)
    target_archive_path: str = Field(min_length=1, max_length=400)


class BackupArchiveCompareResponse(BaseModel):
    safe_mode: str
    base_archive_path: str
    target_archive_path: str
    added: list[str]
    removed: list[str]
    changed: list[str]
    unchanged_count: int
    summary: str


class BackupRestorePlanRequest(BaseModel):
    archive_path: str = Field(min_length=1, max_length=400)
    restore_root: str = Field(min_length=1, max_length=400)
    files: list[str] = Field(default_factory=list)


class BackupRestorePlanResponse(BaseModel):
    safe_mode: str
    archive_path: str
    restore_root: str
    selected_files: list[str]
    missing_files: list[str]
    planned_commands: list[str]
    blocked: bool
    message: str


class BackupRestoreExecuteRequest(BackupRestorePlanRequest):
    confirmation: str = Field(default="", max_length=100)


class BackupRestoreGateResponse(BaseModel):
    safe_mode: str
    accepted_confirmation: bool
    blocked: bool
    plan: BackupRestorePlanResponse
    rollback_plan: list[str]
    message: str


@dataclass(frozen=True)
class BackupRepository:
    database_path: Path

    def list_policies(self, printer_id: int) -> list[BackupPolicyRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, name, source_path, destination_path,
                       include_patterns_json, exclude_patterns_json, dry_run_only,
                       is_active, created_at, updated_at
                FROM backup_policies
                WHERE printer_id = ?
                ORDER BY is_active DESC, name ASC
                """,
                (printer_id,),
            ).fetchall()
        return [_policy_from_row(row) for row in rows]

    def get_policy(self, policy_id: int) -> BackupPolicyRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, name, source_path, destination_path,
                       include_patterns_json, exclude_patterns_json, dry_run_only,
                       is_active, created_at, updated_at
                FROM backup_policies
                WHERE id = ?
                """,
                (policy_id,),
            ).fetchone()
        return _policy_from_row(row) if row else None

    def create_policy(self, printer_id: int, payload: BackupPolicyCreate) -> BackupPolicyRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO backup_policies (
                    printer_id, name, source_path, destination_path,
                    include_patterns_json, exclude_patterns_json, dry_run_only
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    payload.name.strip(),
                    payload.source_path.strip(),
                    payload.destination_path.strip(),
                    json.dumps(_clean_patterns(payload.include_patterns), ensure_ascii=False),
                    json.dumps(_clean_patterns(payload.exclude_patterns), ensure_ascii=False),
                    1 if payload.dry_run_only else 0,
                ),
            )
            policy_id = int(cursor.lastrowid)
        policy = self.get_policy(policy_id)
        if policy is None:
            raise RuntimeError("backup policy was not persisted")
        return policy

    def create_dry_run(self, policy_id: int) -> BackupRunRecord | None:
        policy = self.get_policy(policy_id)
        if policy is None:
            return None

        message = (
            "Dry-run registrado. Nenhum arquivo foi lido, copiado, apagado ou restaurado. "
            "A execução real só deve ser habilitada quando o app estiver instalado no host da impressora."
        )
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO backup_runs (
                    printer_id, policy_id, status, dry_run, source_path, destination_path,
                    include_patterns_json, exclude_patterns_json, total_files, total_bytes, message
                )
                VALUES (?, ?, ?, 1, ?, ?, ?, ?, 0, 0, ?)
                """,
                (
                    policy.printer_id,
                    policy.id,
                    "dry_run_planned",
                    policy.source_path,
                    policy.destination_path,
                    json.dumps(policy.include_patterns, ensure_ascii=False),
                    json.dumps(policy.exclude_patterns, ensure_ascii=False),
                    message,
                ),
            )
            run_id = int(cursor.lastrowid)
        return self.get_run(run_id)

    def execute_local_backup(self, policy_id: int) -> BackupRunRecord | None:
        policy = self.get_policy(policy_id)
        if policy is None:
            return None

        if policy.dry_run_only:
            return self._record_run(
                policy=policy,
                status="blocked",
                dry_run=True,
                total_files=0,
                total_bytes=0,
                message="Execução bloqueada: a política está marcada como dry_run_only.",
            )

        source = Path(policy.source_path).expanduser()
        destination = Path(policy.destination_path).expanduser()
        if not source.exists() or not source.is_dir():
            return self._record_run(
                policy=policy,
                status="failed",
                dry_run=False,
                total_files=0,
                total_bytes=0,
                message=f"Origem inválida ou inexistente: {source}",
            )

        source_resolved = source.resolve()
        destination.mkdir(parents=True, exist_ok=True)
        destination_resolved = destination.resolve()
        if destination_resolved == source_resolved or source_resolved in destination_resolved.parents:
            return self._record_run(
                policy=policy,
                status="failed",
                dry_run=False,
                total_files=0,
                total_bytes=0,
                message="Destino não pode ficar dentro da origem do backup.",
            )

        files = _select_files(source_resolved, policy.include_patterns, policy.exclude_patterns)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        archive_path = destination_resolved / f"printora-backup-{policy.printer_id}-{policy.id}-{timestamp}.zip"
        total_bytes = 0
        with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for file_path in files:
                relative_path = file_path.relative_to(source_resolved)
                archive.write(file_path, relative_path.as_posix())
                total_bytes += file_path.stat().st_size

        return self._record_run(
            policy=policy,
            status="completed",
            dry_run=False,
            total_files=len(files),
            total_bytes=total_bytes,
            message=f"Backup criado em {archive_path}",
        )

    def list_runs(self, printer_id: int, limit: int = 20) -> list[BackupRunRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, policy_id, created_at, status, dry_run, source_path,
                       destination_path, include_patterns_json, exclude_patterns_json,
                       total_files, total_bytes, message
                FROM backup_runs
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, limit),
            ).fetchall()
        return [_run_from_row(row) for row in rows]

    def get_run(self, run_id: int) -> BackupRunRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, policy_id, created_at, status, dry_run, source_path,
                       destination_path, include_patterns_json, exclude_patterns_json,
                       total_files, total_bytes, message
                FROM backup_runs
                WHERE id = ?
                """,
                (run_id,),
            ).fetchone()
        return _run_from_row(row) if row else None

    def _record_run(
        self,
        policy: BackupPolicyRecord,
        status: str,
        dry_run: bool,
        total_files: int,
        total_bytes: int,
        message: str,
    ) -> BackupRunRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO backup_runs (
                    printer_id, policy_id, status, dry_run, source_path, destination_path,
                    include_patterns_json, exclude_patterns_json, total_files, total_bytes, message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    policy.printer_id,
                    policy.id,
                    status,
                    1 if dry_run else 0,
                    policy.source_path,
                    policy.destination_path,
                    json.dumps(policy.include_patterns, ensure_ascii=False),
                    json.dumps(policy.exclude_patterns, ensure_ascii=False),
                    total_files,
                    total_bytes,
                    message,
                ),
            )
            run_id = int(cursor.lastrowid)
        run = self.get_run(run_id)
        if run is None:
            raise RuntimeError("backup run was not persisted")
        return run


def _clean_patterns(patterns: list[str]) -> list[str]:
    return [pattern.strip() for pattern in patterns if pattern.strip()]


def _select_files(source: Path, include_patterns: list[str], exclude_patterns: list[str]) -> list[Path]:
    selected: list[Path] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        if not _matches_any(relative, include_patterns):
            continue
        if _matches_any(relative, exclude_patterns):
            continue
        selected.append(path)
    return selected


def _matches_any(relative_path: Path, patterns: list[str]) -> bool:
    value = relative_path.as_posix()
    for pattern in patterns:
        root_pattern = pattern[3:] if pattern.startswith("**/") else pattern
        if relative_path.match(pattern) or relative_path.match(root_pattern) or Path(value).match(pattern):
            return True
    return False


def _policy_from_row(row) -> BackupPolicyRecord:
    return BackupPolicyRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        name=str(row["name"]),
        source_path=str(row["source_path"]),
        destination_path=str(row["destination_path"]),
        include_patterns=json.loads(row["include_patterns_json"]),
        exclude_patterns=json.loads(row["exclude_patterns_json"]),
        dry_run_only=bool(row["dry_run_only"]),
        is_active=bool(row["is_active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _run_from_row(row) -> BackupRunRecord:
    return BackupRunRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        policy_id=int(row["policy_id"]),
        created_at=str(row["created_at"]),
        status=str(row["status"]),
        dry_run=bool(row["dry_run"]),
        source_path=str(row["source_path"]),
        destination_path=str(row["destination_path"]),
        include_patterns=json.loads(row["include_patterns_json"]),
        exclude_patterns=json.loads(row["exclude_patterns_json"]),
        total_files=int(row["total_files"]),
        total_bytes=int(row["total_bytes"]),
        message=str(row["message"]),
    )


def compare_backup_archives(payload: BackupArchiveCompareRequest) -> BackupArchiveCompareResponse:
    base_path = Path(payload.base_archive_path).expanduser()
    target_path = Path(payload.target_archive_path).expanduser()
    if not base_path.is_file():
        raise ValueError(f"arquivo base não encontrado: {base_path}")
    if not target_path.is_file():
        raise ValueError(f"arquivo alvo não encontrado: {target_path}")
    base = _zip_manifest(base_path)
    target = _zip_manifest(target_path)
    base_names = set(base)
    target_names = set(target)
    added = sorted(target_names - base_names)
    removed = sorted(base_names - target_names)
    common = base_names & target_names
    changed = sorted(name for name in common if base[name] != target[name])
    unchanged_count = len(common) - len(changed)
    summary = (
        f"{len(added)} adicionados, {len(removed)} removidos, "
        f"{len(changed)} alterados, {unchanged_count} inalterados."
    )
    return BackupArchiveCompareResponse(
        safe_mode="local_zip_read_only",
        base_archive_path=str(base_path),
        target_archive_path=str(target_path),
        added=added,
        removed=removed,
        changed=changed,
        unchanged_count=unchanged_count,
        summary=summary,
    )


def build_backup_restore_plan(payload: BackupRestorePlanRequest) -> BackupRestorePlanResponse:
    archive_path = Path(payload.archive_path).expanduser()
    restore_root = Path(payload.restore_root).expanduser()
    if not archive_path.is_file():
        raise ValueError(f"arquivo de backup não encontrado: {archive_path}")
    manifest = _zip_manifest(archive_path)
    requested = _clean_patterns(payload.files)
    selected = requested or sorted(manifest)
    missing = sorted(file for file in selected if file not in manifest)
    existing = [file for file in selected if file in manifest]
    planned_commands = [
        f"# revisar backup antes de restaurar: {archive_path}",
        f"mkdir -p {restore_root}",
    ]
    planned_commands.extend(
        f"unzip -p {archive_path} {file} > {restore_root / file}"
        for file in existing
    )
    return BackupRestorePlanResponse(
        safe_mode="restore_dry_run_only",
        archive_path=str(archive_path),
        restore_root=str(restore_root),
        selected_files=existing,
        missing_files=missing,
        planned_commands=planned_commands,
        blocked=True,
        message="Plano de restore gerado. Nenhum arquivo foi extraído, sobrescrito ou removido.",
    )


def build_backup_restore_gate(payload: BackupRestoreExecuteRequest) -> BackupRestoreGateResponse:
    plan = build_backup_restore_plan(payload)
    accepted_confirmation = payload.confirmation == "BLOCK_REAL_RESTORE"
    return BackupRestoreGateResponse(
        safe_mode="restore_execution_gate_blocked",
        accepted_confirmation=accepted_confirmation,
        blocked=True,
        plan=plan,
        rollback_plan=[
            "Nenhum arquivo foi extraído, sobrescrito ou removido pelo Printora.",
            "Restore real futuro deve criar backup automático do destino antes de sobrescrever qualquer arquivo.",
            "Restore real futuro deve validar Klipper depois da cópia e exigir restart confirmado separadamente.",
        ],
        message=(
            "Gate validado e restore real bloqueado. Nenhuma alteração foi aplicada."
            if accepted_confirmation
            else "Confirmação inválida. Restore real permanece bloqueado e nenhuma alteração foi aplicada."
        ),
    )


def _zip_manifest(path: Path) -> dict[str, tuple[int, int]]:
    with ZipFile(path) as archive:
        return {
            item.filename: (item.file_size, item.CRC)
            for item in archive.infolist()
            if not item.is_dir()
        }
