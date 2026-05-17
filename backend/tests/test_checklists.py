from app.checklists import build_post_update_checklist


def test_post_update_checklist_allows_ready_printer() -> None:
    result = build_post_update_checklist(
        printer_info={"state": "ready", "state_message": "Printer is ready"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
    )

    assert result["can_print"] is True
    assert result["summary"] == "OK para imprimir"


def test_post_update_checklist_blocks_when_klipper_is_not_ready() -> None:
    result = build_post_update_checklist(
        printer_info={"state": "error", "state_message": "config error"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {}},
    )

    assert result["can_print"] is False
    assert result["summary"] == "Não imprima ainda"
