import pytest

from app.discovery import _resolve_discovery_network


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
