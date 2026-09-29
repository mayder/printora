import asyncio
from pathlib import Path

from app.config import Settings
from app.gcode_cache import read_gcode_upload_entry, store_user_gcode_upload
from app.gcode_files import (
    GcodeFileActionRequest,
    build_gcode_file_action_response,
    build_gcode_file_action_states,
    build_gcode_files_response,
    build_gcode_files_unavailable_response,
    require_valid_gcode_file_path,
)
from app.gcode_manager import GcodeManagerRequest, manager_confirmation_phrase, manager_requires_step_up


def test_gcode_files_response_normalizes_files_directories_and_metadata() -> None:
    response = build_gcode_files_response(
        7,
        {
            "safe_mode": "read_only",
            "data_state": "live",
            "fetched_at": "2026-07-20T12:00:00Z",
            "cache_ttl_seconds": 20,
            "storage": {"total": 1000, "used": 400, "free": 600},
            "files": [
                {
                    "filename": "folder/deck.gcode",
                    "path": "folder/deck.gcode",
                    "size": 2048,
                    "modified": 20,
                    "estimated_time": 3600,
                    "slicer": "OrcaSlicer",
                    "slicer_version": "2.4.0",
                    "object_height": 66.89,
                    "layer_height": 0.18,
                    "first_layer_height": 0.3,
                    "layer_count": 370,
                    "nozzle_diameter": 0.6,
                    "filament_total": 23145.18,
                    "filament_weight_total": 67.4,
                    "filament_type": ["PLA", "PLA"],
                    "first_layer_bed_temp": 75,
                    "first_layer_extr_temp": 220,
                    "print_end_time": 1784492400,
                    "last_print_duration": 3800,
                    "metadata_available": True,
                    "thumbnail": {"data_uri": "data:image/png;base64,abc", "width": 160, "height": 120},
                },
                {"filename": "notes.txt", "path": "folder/notes.txt", "size": 10, "modified": 30},
                {"filename": "root.gcode", "path": "root.gcode", "size": 1024, "modified": 10},
            ],
        },
        agent={"version": "0.1.33", "ready": True},
    )

    assert response.printer_id == 7
    assert response.data_state == "live"
    assert response.storage and response.storage.free == 600
    assert [item.path for item in response.files] == ["folder/deck.gcode", "root.gcode"]
    first = response.files[0]
    assert first.name == "deck.gcode"
    assert first.directory == "folder"
    assert first.layer_count == 370
    assert first.filament_type == "PLA, PLA"
    assert first.print_end_time == 1784492400
    assert first.thumbnail and first.thumbnail.width == 160
    assert response.directories[0].path == "folder"
    assert response.directories[0].file_count == 1
    assert "2 arquivo(s)" in response.summary


def test_gcode_files_unavailable_response_keeps_error_state_and_agent_context() -> None:
    response = build_gcode_files_unavailable_response(
        5,
        "timeout aguardando resposta do agente",
        agent={"version": "0.1.30", "ready": False},
        data_state="offline",
    )

    assert response.printer_id == 5
    assert response.data_state == "offline"
    assert response.files == []
    assert response.error == "timeout aguardando resposta do agente"
    assert response.agent and response.agent["version"] == "0.1.30"


def test_gcode_file_action_matrix_blocks_mutations_while_printing() -> None:
    file = build_gcode_files_response(
        1,
        {"files": [{"filename": "folder/deck.gcode", "path": "folder/deck.gcode", "modified": 10}]},
        agent={"ready": True},
    ).files[0]

    actions = {
        item.action: item
        for item in build_gcode_file_action_states(
            file,
            {"connected": True, "printing": True, "print_state": "printing", "filename": "folder/other.gcode"},
            agent={"ready": True},
        )
    }

    assert actions["preview"].enabled is True
    assert actions["download"].read_only is True
    assert actions["print"].enabled is False
    assert "impressão em andamento" in actions["delete"].block_reason.lower()
    assert actions["delete"].requires_confirmation is True
    assert actions["delete"].requires_step_up is True


def test_gcode_file_action_response_requires_exact_target_confirmation() -> None:
    request = GcodeFileActionRequest(
        action="rename",
        filename="folder/deck.gcode",
        target_filename="folder/deck-v2.gcode",
        confirmation_phrase="RENOMEAR errado",
    )

    response = build_gcode_file_action_response(
        7,
        request,
        status="blocked",
        summary="Confirmação textual obrigatória.",
        blockers=["frase inválida"],
    )

    assert response.status == "blocked"
    assert response.confirmation_phrase == "RENOMEAR folder/deck.gcode -> folder/deck-v2.gcode"
    assert response.confirmation_matched is False
    assert response.blockers == ["frase inválida"]


def test_gcode_file_path_rejects_traversal() -> None:
    try:
        require_valid_gcode_file_path("folder/../secret.gcode")
    except ValueError as exc:
        assert "inválido" in str(exc)
    else:
        raise AssertionError("path traversal deveria ser recusado")


def test_gcode_manager_confirmation_phrases_are_exact_and_critical_actions_require_step_up() -> None:
    move = GcodeManagerRequest(
        action="batch_move",
        filenames=["one.gcode", "two.gcode"],
        target_directory="archive",
    )
    preheat = GcodeManagerRequest(
        action="preheat",
        hotend_temperature=220,
        bed_temperature=60,
    )

    assert manager_confirmation_phrase(move) == "MOVER 2 ARQUIVOS -> archive"
    assert manager_requires_step_up(move.action) is True
    assert manager_confirmation_phrase(preheat) == "PRE-AQUECER 220C / 60C"
    assert manager_requires_step_up(preheat.action) is True


def test_user_gcode_upload_is_staged_with_digest_and_printer_scope(tmp_path: Path) -> None:
    class UploadRequest:
        async def stream(self):
            yield b"; generated by test\n"
            yield b"G28\n"

    settings = Settings(data_dir=tmp_path)
    entry = asyncio.run(store_user_gcode_upload(settings, 9, "jobs/cube test.gcode", UploadRequest()))

    assert entry.printer_id == 9
    assert entry.filename == "jobs/cube test.gcode"
    assert entry.size_bytes == 24
    assert len(entry.sha256) == 64
    assert read_gcode_upload_entry(settings, 9, entry.upload_key) == entry
    assert read_gcode_upload_entry(settings, 10, entry.upload_key) is None
from pathlib import Path
