from app.updates import build_update_status, risky_update_components, update_route_for_target


def test_build_update_status_detects_available_updates() -> None:
    result = build_update_status(
        {
            "version_info": {
                "klipper": {
                    "configured_type": "git_repo",
                    "version": "v0.13.0-438",
                    "remote_version": "v0.13.0-658",
                    "commits_behind_count": 220,
                    "is_dirty": False,
                    "is_valid": True,
                },
                "mainsail-config": {
                    "configured_type": "git_repo",
                    "version": "v1.2.1-1",
                    "remote_version": "v1.2.1-1",
                    "commits_behind_count": 0,
                    "is_dirty": False,
                    "is_valid": True,
                },
            }
        }
    )

    assert result.summary == "1 componente(s) com update disponível"
    assert result.counts["update_available"] == 1
    assert result.components[0].name == "klipper"
    assert result.components[0].status == "update_available"
    assert result.components[0].can_update is True
    assert result.components[0].risk_level == "high"
    assert result.components[0].requires_confirmation is True
    assert result.components[1].status == "up_to_date"
    assert result.components[1].can_update is False


def test_build_update_status_warns_on_dirty_or_invalid_component() -> None:
    result = build_update_status(
        {
            "version_info": {
                "custom": {
                    "configured_type": "git_repo",
                    "version": "v1",
                    "remote_version": "v1",
                    "is_dirty": True,
                    "warnings": ["repo dirty"],
                }
            }
        }
    )

    assert result.summary == "Há componentes com alerta"
    assert result.counts["warning"] == 1
    assert result.components[0].status == "warning"
    assert result.components[0].can_update is True


def test_update_route_for_target_uses_safe_moonraker_routes() -> None:
    assert update_route_for_target("all") == ("/machine/update/full", "all")
    assert update_route_for_target("system") == ("/machine/update/system", "system")
    assert update_route_for_target("klipper") == ("/machine/update/klipper", "klipper")
    assert update_route_for_target("mainsail") == ("/machine/update/client", "mainsail")


def test_build_update_status_exposes_rollback_when_moonraker_reports_previous_version() -> None:
    result = build_update_status(
        {
            "version_info": {
                "klipper": {
                    "configured_type": "git_repo",
                    "version": "v0.13.0-686",
                    "remote_version": "v0.13.0-686",
                    "rollback_version": "v0.13.0-662",
                    "commits_behind_count": 0,
                    "is_dirty": False,
                    "is_valid": True,
                }
            }
        }
    )

    assert result.components[0].status == "up_to_date"
    assert result.components[0].rollback_version == "v0.13.0-662"
    assert result.components[0].can_rollback is True


def test_risky_update_components_finds_high_risk_target_and_all_updates() -> None:
    result = build_update_status(
        {
            "version_info": {
                "klipper": {
                    "configured_type": "git_repo",
                    "version": "v0.13.0-662",
                    "remote_version": "v0.13.0-686",
                    "commits_behind_count": 24,
                    "is_dirty": False,
                    "is_valid": True,
                },
                "klipper-toolchanger-easy": {
                    "configured_type": "git_repo",
                    "version": "v0.0.0-250",
                    "remote_version": "v0.0.0-252",
                    "commits_behind_count": 2,
                    "is_dirty": False,
                    "is_valid": True,
                },
                "mainsail": {
                    "configured_type": "web",
                    "version": "v2.17.0",
                    "remote_version": "v2.17.1",
                    "commits_behind_count": 1,
                    "is_dirty": False,
                    "is_valid": True,
                },
            }
        }
    )

    assert [item.name for item in risky_update_components(result, "all")] == ["klipper", "klipper-toolchanger-easy"]
    assert [item.name for item in risky_update_components(result, "klipper")] == ["klipper"]
    assert risky_update_components(result, "mainsail") == []
