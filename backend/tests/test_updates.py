from app.updates import build_update_status, update_route_for_target


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
