from __future__ import annotations

from pathlib import Path
from typing import Any

from app.database import connect_database

from .contracts import ConsumptionPayload, QualitySamplePayload, SpoolPayload, SpoolUpdatePayload


class MaterialConflictError(ValueError):
    pass


class MaterialNotFoundError(ValueError):
    pass


class MaterialInventoryRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def list_spools(self, owner_user_id: int, *, include_archived: bool = False) -> list[dict[str, Any]]:
        status_clause = "" if include_archived else "AND ms.status = 'active'"
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT ms.*
                FROM material_spools ms
                WHERE ms.owner_user_id = ? {status_clause}
                ORDER BY ms.updated_at DESC, ms.id DESC
                """,
                (owner_user_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def spool(self, spool_id: int, owner_user_id: int, *, active_only: bool = True) -> dict[str, Any]:
        status_clause = "AND status = 'active'" if active_only else ""
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                f"SELECT * FROM material_spools WHERE id = ? AND owner_user_id = ? {status_clause}",
                (spool_id, owner_user_id),
            ).fetchone()
        if row is None:
            raise MaterialNotFoundError("spool não encontrado")
        return dict(row)

    def create_spool(self, owner_user_id: int, payload: SpoolPayload) -> dict[str, Any]:
        self._validate_profile(payload.material_profile_id, owner_user_id, payload.material_type)
        remaining_weight = payload.remaining_weight_g
        if remaining_weight is None:
            remaining_weight = payload.initial_weight_g
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO material_spools (
                    owner_user_id, material_profile_id, source, name, material_type, brand,
                    color_name, color_hex, lot_code, initial_weight_g, remaining_weight_g,
                    location, storage_state, opened_at, dried_at, expires_at
                ) VALUES (?, ?, 'local', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    owner_user_id,
                    payload.material_profile_id,
                    payload.name,
                    payload.material_type.upper(),
                    payload.brand,
                    payload.color_name,
                    payload.color_hex,
                    payload.lot_code,
                    payload.initial_weight_g,
                    remaining_weight,
                    payload.location,
                    payload.storage_state,
                    payload.opened_at,
                    payload.dried_at,
                    payload.expires_at,
                ),
            )
            spool_id = int(cursor.lastrowid)
        return self.spool(spool_id, owner_user_id)

    def update_spool(self, spool_id: int, owner_user_id: int, payload: SpoolUpdatePayload) -> dict[str, Any]:
        current = self.spool(spool_id, owner_user_id)
        if current["source"] != "local":
            raise MaterialConflictError("spool do Spoolman deve ser alterado no Spoolman e sincronizado novamente")
        self._validate_profile(payload.material_profile_id, owner_user_id, payload.material_type)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE material_spools
                SET material_profile_id = ?, name = ?, material_type = ?, brand = ?, color_name = ?,
                    color_hex = ?, lot_code = ?, initial_weight_g = ?, remaining_weight_g = ?,
                    location = ?, storage_state = ?, opened_at = ?, dried_at = ?, expires_at = ?,
                    revision = revision + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_user_id = ? AND status = 'active' AND revision = ?
                """,
                (
                    payload.material_profile_id,
                    payload.name,
                    payload.material_type.upper(),
                    payload.brand,
                    payload.color_name,
                    payload.color_hex,
                    payload.lot_code,
                    payload.initial_weight_g,
                    payload.remaining_weight_g,
                    payload.location,
                    payload.storage_state,
                    payload.opened_at,
                    payload.dried_at,
                    payload.expires_at,
                    spool_id,
                    owner_user_id,
                    payload.revision,
                ),
            )
            if cursor.rowcount == 0:
                raise MaterialConflictError("o spool foi alterado em outra tela; atualize os dados e tente novamente")
        return self.spool(spool_id, owner_user_id)

    def archive_spool(self, spool_id: int, owner_user_id: int) -> None:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE material_spools
                SET status = 'archived', revision = revision + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND owner_user_id = ? AND status = 'active'
                """,
                (spool_id, owner_user_id),
            )
            if cursor.rowcount == 0:
                raise MaterialNotFoundError("spool não encontrado")

    def upsert_spoolman(self, owner_user_id: int, payload: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        external_id = str(payload["external_id"])
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                """
                SELECT id FROM material_spools
                WHERE owner_user_id = ? AND source = 'spoolman' AND external_id = ?
                """,
                (owner_user_id, external_id),
            ).fetchone()
            connection.execute(
                """
                INSERT INTO material_spools (
                    owner_user_id, source, external_id, name, material_type, brand, color_name,
                    color_hex, lot_code, initial_weight_g, remaining_weight_g, location,
                    storage_state, status, last_synced_at
                ) VALUES (?, 'spoolman', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
                ON CONFLICT(owner_user_id, source, external_id) DO UPDATE SET
                    name = excluded.name,
                    material_type = excluded.material_type,
                    brand = excluded.brand,
                    color_name = excluded.color_name,
                    color_hex = excluded.color_hex,
                    lot_code = excluded.lot_code,
                    initial_weight_g = excluded.initial_weight_g,
                    remaining_weight_g = excluded.remaining_weight_g,
                    location = excluded.location,
                    storage_state = excluded.storage_state,
                    revision = material_spools.revision + 1,
                    last_synced_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    owner_user_id,
                    external_id,
                    payload["name"],
                    payload["material_type"],
                    payload["brand"],
                    payload["color_name"],
                    payload["color_hex"],
                    payload["lot_code"],
                    payload["initial_weight_g"],
                    payload["remaining_weight_g"],
                    payload["location"],
                    payload["storage_state"],
                ),
            )
            row = connection.execute(
                """
                SELECT * FROM material_spools
                WHERE owner_user_id = ? AND source = 'spoolman' AND external_id = ?
                """,
                (owner_user_id, external_id),
            ).fetchone()
        if row is None:
            raise MaterialNotFoundError("spool sincronizado não encontrado")
        return dict(row), existing is None

    def record_consumption(self, owner_user_id: int, payload: ConsumptionPayload) -> dict[str, Any]:
        spool = self.spool(payload.spool_id, owner_user_id)
        self._validate_job_ownership(payload.slicing_job_id, payload.print_history_id, owner_user_id)
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                """
                SELECT * FROM material_consumptions
                WHERE owner_user_id = ? AND idempotency_key = ?
                """,
                (owner_user_id, payload.idempotency_key),
            ).fetchone()
            if existing is not None:
                self._assert_same_consumption(dict(existing), payload)
                return dict(existing)

            remaining_after = spool["remaining_weight_g"]
            if payload.status == "confirmed" and spool["source"] == "local":
                actual = float(payload.actual_weight_g or 0)
                if remaining_after is None:
                    raise MaterialConflictError("informe o peso disponível antes de confirmar consumo")
                updated = connection.execute(
                    """
                    UPDATE material_spools
                    SET remaining_weight_g = remaining_weight_g - ?, revision = revision + 1,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND owner_user_id = ? AND status = 'active'
                      AND remaining_weight_g >= ?
                    RETURNING remaining_weight_g
                    """,
                    (actual, payload.spool_id, owner_user_id, actual),
                ).fetchone()
                if updated is None:
                    raise MaterialConflictError("material insuficiente para confirmar este consumo")
                remaining_after = float(updated["remaining_weight_g"])

            cursor = connection.execute(
                """
                INSERT INTO material_consumptions (
                    owner_user_id, spool_id, slicing_job_id, print_history_id, idempotency_key,
                    predicted_weight_g, actual_weight_g, status, remaining_weight_after_g, note,
                    confirmed_at, released_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    CASE WHEN ? = 'confirmed' THEN CURRENT_TIMESTAMP END,
                    CASE WHEN ? = 'released' THEN CURRENT_TIMESTAMP END)
                """,
                (
                    owner_user_id,
                    payload.spool_id,
                    payload.slicing_job_id,
                    payload.print_history_id,
                    payload.idempotency_key,
                    payload.predicted_weight_g,
                    payload.actual_weight_g,
                    payload.status,
                    remaining_after,
                    payload.note,
                    payload.status,
                    payload.status,
                ),
            )
            consumption_id = int(cursor.lastrowid)
            row = connection.execute("SELECT * FROM material_consumptions WHERE id = ?", (consumption_id,)).fetchone()
        if row is None:
            raise MaterialNotFoundError("consumo não encontrado")
        return dict(row)

    def consumptions(self, spool_id: int, owner_user_id: int) -> list[dict[str, Any]]:
        self.spool(spool_id, owner_user_id, active_only=False)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM material_consumptions
                WHERE spool_id = ? AND owner_user_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (spool_id, owner_user_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def create_quality_sample(self, owner_user_id: int, payload: QualitySamplePayload) -> dict[str, Any]:
        self.spool(payload.spool_id, owner_user_id)
        self._validate_job_ownership(None, payload.print_history_id, owner_user_id)
        if payload.photo_object_id is not None:
            self._validate_photo(payload.photo_object_id, owner_user_id)
        deviation = abs(payload.measured_value_mm - payload.nominal_value_mm)
        result = "passed" if deviation <= payload.tolerance_mm else "failed"
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO material_quality_samples (
                    owner_user_id, spool_id, print_history_id, sample_type, metric_name,
                    nominal_value_mm, measured_value_mm, tolerance_mm, result, photo_object_id, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    owner_user_id,
                    payload.spool_id,
                    payload.print_history_id,
                    payload.sample_type,
                    payload.metric_name,
                    payload.nominal_value_mm,
                    payload.measured_value_mm,
                    payload.tolerance_mm,
                    result,
                    payload.photo_object_id,
                    payload.note,
                ),
            )
            sample_id = int(cursor.lastrowid)
            row = connection.execute("SELECT * FROM material_quality_samples WHERE id = ?", (sample_id,)).fetchone()
        if row is None:
            raise MaterialNotFoundError("amostra não encontrada")
        return dict(row)

    def quality_samples(self, spool_id: int, owner_user_id: int) -> list[dict[str, Any]]:
        self.spool(spool_id, owner_user_id, active_only=False)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT * FROM material_quality_samples
                WHERE spool_id = ? AND owner_user_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (spool_id, owner_user_id),
            ).fetchall()
        return [dict(row) for row in rows]

    def profile_for_compatibility(self, profile_id: int, owner_user_id: int) -> dict[str, Any]:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, owner_user_id, printer_id, material_type, nozzle_diameter_mm, compatibility_json
                FROM social_material_profiles
                WHERE id = ? AND owner_user_id = ? AND status = 'active'
                """,
                (profile_id, owner_user_id),
            ).fetchone()
        if row is None:
            raise MaterialNotFoundError("perfil de material não encontrado")
        return dict(row)

    def printer_for_owner(self, printer_id: int, owner_user_id: int) -> dict[str, Any]:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT id, name, catalog_variant_id FROM printers WHERE id = ? AND owner_user_id = ?",
                (printer_id, owner_user_id),
            ).fetchone()
        if row is None:
            raise MaterialNotFoundError("impressora não encontrada")
        return dict(row)

    def _validate_profile(self, profile_id: int | None, owner_user_id: int, material_type: str) -> None:
        if profile_id is None:
            return
        profile = self.profile_for_compatibility(profile_id, owner_user_id)
        if str(profile["material_type"]).upper() != material_type.upper():
            raise MaterialConflictError("o material do spool diverge do perfil selecionado")

    def _validate_job_ownership(
        self,
        slicing_job_id: int | None,
        print_history_id: int | None,
        owner_user_id: int,
    ) -> None:
        with connect_database(self.database_path) as connection:
            if slicing_job_id is not None:
                row = connection.execute(
                    "SELECT id FROM slicing_jobs WHERE id = ? AND owner_user_id = ?",
                    (slicing_job_id, owner_user_id),
                ).fetchone()
                if row is None:
                    raise MaterialNotFoundError("job de fatiamento não encontrado")
            if print_history_id is not None:
                row = connection.execute(
                    "SELECT id FROM print_job_history WHERE id = ? AND owner_user_id = ?",
                    (print_history_id, owner_user_id),
                ).fetchone()
                if row is None:
                    raise MaterialNotFoundError("histórico de impressão não encontrado")

    def _validate_photo(self, object_id: int, owner_user_id: int) -> None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id FROM cloud_objects
                WHERE id = ? AND owner_user_id = ? AND state IN ('analyzed', 'promoted')
                  AND content_type LIKE 'image/%'
                """,
                (object_id, owner_user_id),
            ).fetchone()
        if row is None:
            raise MaterialNotFoundError("foto confirmada não encontrada")

    @staticmethod
    def _assert_same_consumption(existing: dict[str, Any], payload: ConsumptionPayload) -> None:
        expected = (
            payload.spool_id,
            payload.slicing_job_id,
            payload.print_history_id,
            payload.predicted_weight_g,
            payload.actual_weight_g,
            payload.status,
        )
        received = (
            existing["spool_id"],
            existing["slicing_job_id"],
            existing["print_history_id"],
            existing["predicted_weight_g"],
            existing["actual_weight_g"],
            existing["status"],
        )
        if expected != received:
            raise MaterialConflictError("a chave de repetição já foi usada com outro consumo")
