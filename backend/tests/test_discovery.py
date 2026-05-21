import pytest

from app.discovery import _registered_moonraker_targets, _resolve_discovery_network
from app.printers import PrinterRecord


def test_discovery_accepts_private_24_network() -> None:
    network, warnings = _resolve_discovery_network("192.168.1.0/24")

    assert str(network) == "192.168.1.0/24"
    assert warnings == []


def test_discovery_rejects_public_network() -> None:
    with pytest.raises(ValueError, match="private"):
        _resolve_discovery_network("8.8.8.0/24")


def test_discovery_rejects_large_network() -> None:
    with pytest.raises(ValueError, match="limited"):
        _resolve_discovery_network("192.168.0.0/16")


def test_discovery_marks_registered_printer_by_resolved_ip(monkeypatch) -> None:
    def fake_getaddrinfo(*args, **kwargs):
        return [(None, None, None, None, ("192.168.15.10", 0))]

    monkeypatch.setattr("app.discovery.socket.getaddrinfo", fake_getaddrinfo)

    _, endpoints = _registered_moonraker_targets(
        [
            PrinterRecord(
                id=1,
                name="Voron",
                moonraker_url="http://voron.local:7125",
                host_audit_mode="disabled",
                host_audit_ssh_target=None,
                ssh_host=None,
                ssh_port=None,
                ssh_username=None,
                ssh_credential_configured=False,
                location=None,
                notes=None,
                is_active=True,
                created_at="2026-05-19 12:00:00",
                updated_at="2026-05-19 12:00:00",
            )
        ]
    )

    assert ("voron.local", 7125) in endpoints
    assert ("192.168.15.10", 7125) in endpoints
