from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth import AuthRepository, UserRegisterRequest
from app.config import get_settings
from app.database import connect_database, initialize_database
from app.main import app
from app.modules.operations.materials.contracts import (
    CompatibilityRequest,
    ConsumptionPayload,
    QualitySamplePayload,
    SpoolPayload,
    SpoolUpdatePayload,
)
from app.modules.operations.materials.repository import (
    MaterialConflictError,
    MaterialInventoryRepository,
    MaterialNotFoundError,
)
from app.modules.operations.materials.service import MaterialInventoryService
from app.print_profiles import MaterialProfilePayload, PrintProfilesRepository
from app.printers import PrinterCreate, PrinterRepository


def test_local_spool_crud_quality_and_actionable_alerts(tmp_path: Path) -> None:
    service, user_id, printer_id, profile_id = _seed(tmp_path)
    spool = service.create_spool(
        user_id,
        SpoolPayload(
            material_profile_id=profile_id,
            name="ABS Preto",
            material_type="ABS",
            brand="KVP",
            initial_weight_g=1000,
            remaining_weight_g=800,
            location="Caixa seca",
            storage_state="open",
        ),
    )

    assert spool.source == "local"
    assert {alert.code for alert in spool.alerts} == {"ventilation"}
    updated = service.update_spool(
        spool.id,
        user_id,
        SpoolUpdatePayload(
            revision=spool.revision,
            material_profile_id=profile_id,
            name="ABS Preto lote 2",
            material_type="ABS",
            initial_weight_g=1000,
            remaining_weight_g=790,
            storage_state="dry",
        ),
    )
    sample = service.create_quality_sample(
        user_id,
        QualitySamplePayload(
            spool_id=spool.id,
            sample_type="dimensional",
            metric_name="Cubo eixo X",
            nominal_value_mm=20,
            measured_value_mm=20.08,
            tolerance_mm=0.1,
        ),
    )

    assert updated.revision == spool.revision + 1
    assert sample.result == "passed"
    assert sample.deviation_mm == pytest.approx(0.08)
    assert service.compatibility(
        user_id,
        CompatibilityRequest(
            spool_id=spool.id,
            printer_id=printer_id,
            material_profile_id=profile_id,
            required_weight_g=100,
            ventilation_confirmed=True,
        ),
    ).status == "compatible"


def test_consumption_is_idempotent_and_never_decrements_twice(tmp_path: Path) -> None:
    service, user_id, _printer_id, _profile_id = _seed(tmp_path)
    spool = service.create_spool(
        user_id,
        SpoolPayload(name="PLA Azul", material_type="PLA", initial_weight_g=1000, remaining_weight_g=500),
    )
    payload = ConsumptionPayload(
        spool_id=spool.id,
        idempotency_key="print-job-42-confirm",
        actual_weight_g=125,
        status="confirmed",
    )

    first = service.record_consumption(user_id, payload)
    repeated = service.record_consumption(user_id, payload)

    assert first.id == repeated.id
    assert service.spool(spool.id, user_id).remaining_weight_g == pytest.approx(375)
    with pytest.raises(MaterialConflictError, match="outra consumo|outro consumo"):
        service.record_consumption(
            user_id,
            ConsumptionPayload(
                spool_id=spool.id,
                idempotency_key=payload.idempotency_key,
                actual_weight_g=126,
                status="confirmed",
            ),
        )
    with pytest.raises(MaterialConflictError, match="insuficiente"):
        service.record_consumption(
            user_id,
            ConsumptionPayload(
                spool_id=spool.id,
                idempotency_key="print-job-43-confirm",
                actual_weight_g=500,
                status="confirmed",
            ),
        )


def test_spoolman_import_is_canonical_idempotent_and_normalized(tmp_path: Path) -> None:
    service, user_id, _printer_id, _profile_id = _seed(tmp_path)
    raw = {
        "result": {
            "response": [
                {
                    "id": 17,
                    "remaining_weight": 620,
                    "used_weight": 380,
                    "lot_nr": "ASA-2026-01",
                    "location": {"name": "Armário"},
                    "filament": {
                        "name": "ASA Galaxy",
                        "material": "ASA",
                        "color_hex": "112233",
                        "vendor": {"name": "Prusament"},
                    },
                }
            ]
        }
    }

    imported, updated, total = service.import_spoolman(user_id, raw)
    imported_again, updated_again, total_again = service.import_spoolman(user_id, raw)
    spool = service.list_spools(user_id)[0]

    assert (imported, updated, total) == (1, 0, 1)
    assert (imported_again, updated_again, total_again) == (0, 1, 1)
    assert spool.source == "spoolman"
    assert spool.external_id == "17"
    assert spool.initial_weight_g == pytest.approx(1000)
    assert spool.color_hex == "#112233"
    with pytest.raises(MaterialConflictError, match="Spoolman"):
        service.update_spool(
            spool.id,
            user_id,
            SpoolUpdatePayload(
                revision=spool.revision,
                name=spool.name,
                material_type=spool.material_type,
                initial_weight_g=spool.initial_weight_g,
                remaining_weight_g=spool.remaining_weight_g,
            ),
        )


def test_spoolman_ignores_items_without_a_stable_identifier(tmp_path: Path) -> None:
    service, user_id, _printer_id, _profile_id = _seed(tmp_path)

    assert service.import_spoolman(user_id, {"result": [{"id": None}, {"name": "sem id"}]}) == (0, 0, 0)
    assert service.list_spools(user_id) == []


def test_quality_sample_only_accepts_confirmed_images_owned_by_user(tmp_path: Path) -> None:
    service, user_id, _printer_id, _profile_id = _seed(tmp_path)
    spool = service.create_spool(
        user_id,
        SpoolPayload(name="PLA Branco", material_type="PLA", initial_weight_g=1000),
    )
    with connect_database(tmp_path / "printora.db") as connection:
        cursor = connection.execute(
            """
            INSERT INTO cloud_objects (
                bucket_name, object_key, sha256, size_bytes, content_type, state, owner_user_id
            ) VALUES ('tests', 'quality/report.pdf', ?, 10, 'application/pdf', 'promoted', ?)
            """,
            ("a" * 64, user_id),
        )
        document_id = int(cursor.lastrowid)

    with pytest.raises(MaterialNotFoundError, match="foto confirmada não encontrada"):
        service.create_quality_sample(
            user_id,
            QualitySamplePayload(
                spool_id=spool.id,
                sample_type="dimensional",
                metric_name="Superfície",
                nominal_value_mm=0,
                measured_value_mm=0,
                tolerance_mm=0,
                photo_object_id=document_id,
            ),
        )


def test_material_api_is_owner_scoped_and_uses_human_language(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    try:
        initialize_database(tmp_path / "printora.db")
        with TestClient(app) as client:
            first = client.post("/api/auth/register", json={"email": "materials-owner@example.com", "password": "correct-horse"}).json()
            second = client.post("/api/auth/register", json={"email": "materials-other@example.com", "password": "correct-horse"}).json()
            auth = {"Authorization": f"Bearer {first['access_token']}"}
            other_auth = {"Authorization": f"Bearer {second['access_token']}"}
            created = client.post(
                "/api/materials/spools",
                headers=auth,
                json={"name": "PLA Branco", "material_type": "PLA", "initial_weight_g": 1000},
            )
            spool_id = created.json()["id"]

            own_list = client.get("/api/materials/spools", headers=auth)
            other_list = client.get("/api/materials/spools", headers=other_auth)
            forbidden = client.get(f"/api/materials/spools/{spool_id}", headers=other_auth)

            assert created.status_code == 201
            assert own_list.status_code == 200 and len(own_list.json()) == 1
            assert other_list.json() == []
            assert forbidden.status_code == 404
            assert "PKG-" not in created.text
    finally:
        get_settings.cache_clear()


def _seed(tmp_path: Path) -> tuple[MaterialInventoryService, int, int, int]:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="materials@example.com", password="correct-horse")
    )
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron Materials", moonraker_url="http://127.0.0.1:7125", host_audit_mode="disabled")
    )
    profile = PrintProfilesRepository(database_path).create_profile(
        user.id,
        MaterialProfilePayload(
            printer_id=printer.id,
            title="ABS padrão",
            material_type="ABS",
            visibility="private",
        ),
    )
    repository = MaterialInventoryRepository(database_path)
    return MaterialInventoryService(repository), user.id, printer.id, profile.id
