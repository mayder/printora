from app.host_audit import build_host_findings, parse_can_summary, split_sections, summarize_sections


def test_split_sections_extracts_named_blocks() -> None:
    sections = split_sections("before\nSECTION can0\ncan state ERROR-ACTIVE\nSECTION config_git\n## main\n")

    assert sections["preamble"] == "before"
    assert sections["can0"] == "can state ERROR-ACTIVE"
    assert sections["config_git"] == "## main"


def test_parse_can_summary_reads_error_counters() -> None:
    can_output = """can state ERROR-ACTIVE restart-ms 0
re-started bus-errors arbit-lost error-warn error-pass bus-off
0          0          0          0          0          0
RX: bytes  packets  errors  dropped missed  mcast
62352      8173     0       0       0       0
TX: bytes  packets  errors  dropped carrier collsns
13655      2165     0       0       0       0
"""

    assert parse_can_summary(can_output) == {
        "state": "ERROR-ACTIVE",
        "rx_errors": 0,
        "tx_errors": 0,
        "bus_errors": 0,
    }


def test_host_findings_are_clean_for_healthy_snapshot() -> None:
    sections = {
        "systemctl_failed": "0 loaded units listed.",
        "can0": "can state ERROR-ACTIVE\nRX: bytes packets errors\n1 2 0\nTX: bytes packets errors\n1 2 0",
        "active_legacy_refs": "",
        "active_broken_symlinks": "",
        "config_git": "## main",
        "repos": "REPO /home/pi/klipper\n## master...origin/master\nv0.13.0",
        "recent_klippy_log": "",
        "recent_moonraker_log": "",
    }

    findings = build_host_findings(0, sections)

    assert len(findings) == 1
    assert findings[0].id == "host_audit_no_findings"


def test_host_findings_flag_dirty_config_and_legacy_path() -> None:
    sections = {
        "systemctl_failed": "0 loaded units listed.",
        "can0": "can state ERROR-ACTIVE\nRX: bytes packets errors\n1 2 0\nTX: bytes packets errors\n1 2 0",
        "active_legacy_refs": "",
        "active_broken_symlinks": "",
        "config_git": "## main\n M printer.cfg",
        "repos": "LEGACY_PATH /home/pi/timelapse",
        "recent_klippy_log": "",
        "recent_moonraker_log": "",
    }

    findings = build_host_findings(0, sections)

    assert [finding.id for finding in findings] == ["config_repo_dirty", "legacy_paths_present"]


def test_section_summary_counts_paths() -> None:
    summary = summarize_sections(
        {
            "systemctl_failed": "0 loaded units listed.",
            "can0": "can state ERROR-ACTIVE",
            "active_legacy_refs": "a\nb\n",
            "active_broken_symlinks": "x\n",
            "config_git": "## main\n M printer.cfg",
            "repos": "REPO /home/pi/klipper\nLEGACY_PATH /home/pi/timelapse\n",
        }
    )

    assert summary["legacy_refs_count"] == 2
    assert summary["broken_symlink_count"] == 1
    assert summary["repo_count"] == 1
    assert summary["legacy_path_count"] == 1
