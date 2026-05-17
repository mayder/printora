from app.audit import build_read_only_audit


def test_read_only_audit_returns_info_when_no_issues() -> None:
    result = build_read_only_audit(
        printer_info={"state": "ready", "software_version": "v0.13.0"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
    )

    assert result["safe_mode"] == "read_only"
    assert result["counts"]["ignorar"] == 1
    assert result["summary"] == "Ambiente sem problemas críticos nos dados disponíveis."


def test_read_only_audit_blocks_when_klipper_is_not_ready() -> None:
    result = build_read_only_audit(
        printer_info={"state": "error", "state_message": "config error"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": False, "commits_behind_count": 0}}},
    )

    assert result["counts"]["corrigir_agora"] == 1
    assert result["summary"] == "Há bloqueios. Não inicie nova impressão antes de corrigir."
    assert result["findings"][0]["id"] == "klipper_not_ready"


def test_read_only_audit_flags_dirty_repo() -> None:
    result = build_read_only_audit(
        printer_info={"state": "ready", "software_version": "v0.13.0"},
        server_info={
            "klippy_connected": True,
            "klippy_state": "ready",
            "failed_components": [],
            "warnings": [],
        },
        update_status={"version_info": {"klipper": {"is_dirty": True, "commits_behind_count": 0}}},
    )

    assert result["counts"]["monitorar"] == 1
    assert result["findings"][0]["id"] == "repo_klipper_needs_attention"
