from app.gcode_files import build_gcode_files_response, build_gcode_files_unavailable_response


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
                    "last_print_duration": 3800,
                    "metadata_available": True,
                    "thumbnail": {"data_uri": "data:image/png;base64,abc", "width": 160, "height": 120},
                },
                {"filename": "notes.txt", "path": "folder/notes.txt", "size": 10, "modified": 30},
                {"filename": "root.gcode", "path": "root.gcode", "size": 1024, "modified": 10},
            ],
        },
        agent={"version": "0.1.32", "ready": True},
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
