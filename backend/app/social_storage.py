from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field

from app.database import connect_database
from app.object_storage import LocalObjectStorage, StoredObject, build_object_storage

DEFAULT_USER_QUOTA_BYTES = 1024 * 1024 * 1024
DEFAULT_RETENTION_DAYS = 180


class StoragePolicy(BaseModel):
    scope_type: str
    scope_id: int | None = None
    quota_bytes: int
    retention_days: int
    cost_per_gb_month_cents: int


class StorageUsageSummary(BaseModel):
    quota_bytes: int
    used_bytes: int
    remaining_bytes: int
    projected_monthly_cost_cents: int
    file_count: int
    deduplicated_file_count: int
    active_item_count: int
    archived_item_count: int


class StorageRetentionCandidate(BaseModel):
    file_id: int
    item_id: int
    file_name: str
    size_bytes: int
    status: str
    referenced_by_current_version: bool
    eligible: bool
    reason: str


class StorageRetentionPlan(BaseModel):
    mode: str = "dry_run"
    retention_days: int
    candidate_count: int
    blocked_count: int
    reclaimable_bytes: int
    candidates: list[StorageRetentionCandidate] = Field(default_factory=list)
    review_id: int | None = None


class StorageReport(BaseModel):
    policy: StoragePolicy
    usage: StorageUsageSummary
    retention: StorageRetentionPlan
    object_storage_plan: list[str]


LocalLibraryStorage = LocalObjectStorage


class SocialStorageRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.storage = build_object_storage(database_path)

    def register_object(
        self,
        connection,
        stored: StoredObject,
        *,
        owner_user_id: int,
        reference_type: str,
        reference_id: int,
        state: str = "quarantined",
    ) -> int:
        row = connection.execute(
            """
            INSERT INTO cloud_objects (
                bucket_name, object_key, sha256, size_bytes, content_type, state,
                version_id, etag, owner_user_id, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT (bucket_name, object_key) DO UPDATE SET
                sha256 = excluded.sha256,
                size_bytes = excluded.size_bytes,
                content_type = excluded.content_type,
                state = excluded.state,
                version_id = excluded.version_id,
                etag = excluded.etag,
                owner_user_id = excluded.owner_user_id,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id
            """,
            (
                stored.bucket,
                stored.key,
                stored.sha256,
                stored.size_bytes,
                stored.content_type,
                state,
                stored.version_id,
                stored.etag,
                owner_user_id,
            ),
        ).fetchone()
        object_id = int(row["id"])
        connection.execute(
            """
            INSERT INTO cloud_object_references (object_id, reference_type, reference_id)
            VALUES (?, ?, ?)
            ON CONFLICT (reference_type, reference_id) DO UPDATE SET object_id = excluded.object_id
            """,
            (object_id, reference_type, reference_id),
        )
        return object_id

    def report_for_user(self, user_id: int, *, persist_review: bool = False) -> StorageReport:
        with connect_database(self.database_path) as connection:
            policy = self._policy_for_user(connection, user_id)
            usage = self._usage_for_user(connection, user_id, policy)
            retention = self._retention_plan(connection, user_id, user_id, policy, persist_review=persist_review)
            return StorageReport(
                policy=policy,
                usage=usage,
                retention=retention,
                object_storage_plan=[
                    "Manter a chave lógica do arquivo desacoplada do caminho local.",
                    "Migrar o adapter para bucket externo preservando checksum, tamanho e dono.",
                    "Executar backfill supervisionado antes de trocar leitura/download para object storage.",
                ],
            )

    def ensure_upload_allowed(self, connection, owner_user_id: int, incoming_bytes: int) -> StorageUsageSummary:
        if incoming_bytes <= 0:
            raise ValueError("arquivo vazio")
        policy = self._policy_for_user(connection, owner_user_id)
        usage = self._usage_for_user(connection, owner_user_id, policy)
        if incoming_bytes > usage.remaining_bytes:
            raise ValueError("cota de armazenamento insuficiente para este arquivo")
        return usage

    def create_retention_review(self, user_id: int, requested_by_user_id: int) -> StorageRetentionPlan:
        with connect_database(self.database_path) as connection:
            policy = self._policy_for_user(connection, user_id)
            return self._retention_plan(connection, user_id, requested_by_user_id, policy, persist_review=True)

    def _policy_for_user(self, connection, user_id: int) -> StoragePolicy:
        row = connection.execute(
            """
            SELECT scope_type, scope_id, quota_bytes, retention_days, cost_per_gb_month_cents
            FROM social_file_storage_policies
            WHERE status = 'active'
              AND ((scope_type = 'user' AND scope_id = ?) OR scope_type = 'global')
            ORDER BY CASE scope_type WHEN 'user' THEN 0 ELSE 1 END
            LIMIT 1
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            return StoragePolicy(
                scope_type="default",
                quota_bytes=DEFAULT_USER_QUOTA_BYTES,
                retention_days=DEFAULT_RETENTION_DAYS,
                cost_per_gb_month_cents=0,
            )
        return StoragePolicy(
            scope_type=str(row["scope_type"]),
            scope_id=row["scope_id"],
            quota_bytes=int(row["quota_bytes"]),
            retention_days=int(row["retention_days"]),
            cost_per_gb_month_cents=int(row["cost_per_gb_month_cents"]),
        )

    def _usage_for_user(self, connection, user_id: int, policy: StoragePolicy) -> StorageUsageSummary:
        row = connection.execute(
            """
            SELECT
                COALESCE(SUM(COALESCE(lf.uploaded_size_bytes, lf.size_bytes, 0)), 0) AS used_bytes,
                COUNT(lf.id) AS file_count,
                COALESCE(SUM(CASE WHEN lf.deduplicated_from_file_id IS NOT NULL THEN 1 ELSE 0 END), 0) AS deduplicated_file_count,
                COUNT(DISTINCT CASE WHEN li.status = 'active' THEN li.id END) AS active_item_count,
                COUNT(DISTINCT CASE WHEN li.status = 'archived' THEN li.id END) AS archived_item_count
            FROM social_library_items li
            LEFT JOIN social_library_files lf ON lf.item_id = li.id
            WHERE li.owner_user_id = ?
            """,
            (user_id,),
        ).fetchone()
        used_bytes = int(row["used_bytes"] or 0)
        gb_month = used_bytes / (1024 * 1024 * 1024)
        projected_cost = int(round(gb_month * policy.cost_per_gb_month_cents))
        return StorageUsageSummary(
            quota_bytes=policy.quota_bytes,
            used_bytes=used_bytes,
            remaining_bytes=max(policy.quota_bytes - used_bytes, 0),
            projected_monthly_cost_cents=projected_cost,
            file_count=int(row["file_count"] or 0),
            deduplicated_file_count=int(row["deduplicated_file_count"] or 0),
            active_item_count=int(row["active_item_count"] or 0),
            archived_item_count=int(row["archived_item_count"] or 0),
        )

    def _retention_plan(self, connection, user_id: int, requested_by_user_id: int, policy: StoragePolicy, *, persist_review: bool) -> StorageRetentionPlan:
        rows = connection.execute(
            """
            SELECT lf.id, lf.item_id, lf.file_name, lf.validation_status, COALESCE(lf.uploaded_size_bytes, lf.size_bytes, 0) AS size_bytes,
                   lf.sha256, lf.quarantine_key, li.status AS item_status, li.updated_at
            FROM social_library_files lf
            JOIN social_library_items li ON li.id = lf.item_id
            WHERE li.owner_user_id = ?
              AND (li.status = 'archived' OR lf.validation_status IN ('rejected', 'analysis_failed'))
            ORDER BY li.updated_at, lf.id
            LIMIT 100
            """,
            (user_id,),
        ).fetchall()
        current_signatures = self._current_version_signatures(connection, user_id)
        candidates: list[StorageRetentionCandidate] = []
        for row in rows:
            signature = self._file_signature(row)
            referenced = signature in current_signatures
            eligible = policy.retention_days > 0 and not referenced and row["validation_status"] in {"rejected", "analysis_failed"}
            if policy.retention_days <= 0:
                reason = "retenção não definida"
            elif referenced:
                reason = "referenciado por versão ativa"
            elif row["validation_status"] in {"rejected", "analysis_failed"}:
                reason = "falha de validação em quarentena"
            else:
                reason = "item arquivado exige revisão manual"
            candidates.append(
                StorageRetentionCandidate(
                    file_id=int(row["id"]),
                    item_id=int(row["item_id"]),
                    file_name=str(row["file_name"]),
                    size_bytes=int(row["size_bytes"] or 0),
                    status=str(row["validation_status"]),
                    referenced_by_current_version=referenced,
                    eligible=eligible,
                    reason=reason,
                )
            )
        reclaimable_bytes = sum(candidate.size_bytes for candidate in candidates if candidate.eligible)
        blocked_count = len([candidate for candidate in candidates if not candidate.eligible])
        review_id = None
        if persist_review:
            cursor = connection.execute(
                """
                INSERT INTO social_file_retention_reviews (
                    owner_user_id, requested_by_user_id, mode, candidate_count,
                    blocked_count, reclaimable_bytes, result_json
                )
                VALUES (?, ?, 'dry_run', ?, ?, ?, ?)
                """,
                (
                    user_id,
                    requested_by_user_id,
                    len(candidates),
                    blocked_count,
                    reclaimable_bytes,
                    json.dumps([candidate.model_dump() for candidate in candidates], ensure_ascii=False, sort_keys=True),
                ),
            )
            review_id = int(cursor.lastrowid)
        return StorageRetentionPlan(
            retention_days=policy.retention_days,
            candidate_count=len(candidates),
            blocked_count=blocked_count,
            reclaimable_bytes=reclaimable_bytes,
            candidates=candidates,
            review_id=review_id,
        )

    def _current_version_signatures(self, connection, user_id: int) -> set[tuple[str | None, str | None]]:
        rows = connection.execute(
            """
            SELECT v.files_snapshot_json
            FROM social_library_versions v
            JOIN social_library_items li ON li.id = v.item_id
            WHERE li.owner_user_id = ? AND v.is_current = 1
            """,
            (user_id,),
        ).fetchall()
        signatures: set[tuple[str | None, str | None]] = set()
        for row in rows:
            try:
                files = json.loads(row["files_snapshot_json"] or "[]")
            except json.JSONDecodeError:
                continue
            if not isinstance(files, list):
                continue
            for file in files:
                if isinstance(file, dict):
                    signatures.add((file.get("sha256"), file.get("quarantine_key") or file.get("storage_key")))
        return signatures

    def _file_signature(self, row) -> tuple[str | None, str | None]:
        return (row["sha256"], row["quarantine_key"])
