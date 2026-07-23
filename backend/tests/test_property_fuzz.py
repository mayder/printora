from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

from hypothesis import example, given
from hypothesis import strategies as st
import pytest

from app.gcode_files import require_valid_gcode_file_path
from app.modules.community.validation import validate_public_url
from app.modules.platform.idempotency import KEY_PATTERN, request_fingerprint
from app.payment_provider import SandboxPaymentAdapter
from app.print_preflight import parse_gcode_metadata


CORPUS_PATH = Path(__file__).resolve().parent / "fixtures" / "fuzz-corpus.json"
CORPUS = json.loads(CORPUS_PATH.read_text(encoding="utf-8"))


@given(st.sampled_from(["http", "ftp", "file", "javascript"]), st.text(max_size=200))
@example("http", "127.0.0.1/admin")
def test_public_url_rejects_non_https_schemes(scheme: str, suffix: str) -> None:
    with pytest.raises(ValueError):
        validate_public_url(
            f"{scheme}://{suffix}",
            field_name="url",
            allowed_hosts=None,
        )


@given(st.sampled_from(CORPUS["private_hosts"]))
def test_public_url_rejects_private_and_local_hosts(host: str) -> None:
    authority = f"[{host}]" if ":" in host else host
    with pytest.raises(ValueError):
        validate_public_url(
            f"https://{authority}/resource",
            field_name="url",
            allowed_hosts=None,
        )


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com:not-a-port/resource",
        "https://example.com:99999/resource",
    ],
)
def test_public_url_rejects_invalid_ports(url: str) -> None:
    with pytest.raises(ValueError):
        validate_public_url(url, field_name="url", allowed_hosts=None)


@given(
    st.from_regex(r"[a-z][a-z0-9-]{0,30}", fullmatch=True),
    st.lists(
        st.from_regex(r"[a-zA-Z0-9_.-]{1,30}", fullmatch=True),
        min_size=1,
        max_size=5,
    ),
)
def test_public_https_url_round_trips_without_credentials(
    host_label: str,
    segments: list[str],
) -> None:
    raw = f"https://{host_label}.example/" + "/".join(segments)
    cleaned = validate_public_url(raw, field_name="url", allowed_hosts=None)

    assert cleaned == raw
    parsed = urlparse(cleaned)
    assert parsed.scheme == "https"
    assert parsed.username is None
    assert parsed.password is None


@given(st.sampled_from(CORPUS["path_traversal"]))
def test_gcode_path_rejects_traversal_corpus(path: str) -> None:
    with pytest.raises(ValueError):
        require_valid_gcode_file_path(path)


@given(
    st.lists(
        st.from_regex(r"[A-Za-z0-9_-]{1,24}", fullmatch=True),
        min_size=1,
        max_size=5,
    )
)
def test_gcode_path_accepts_bounded_safe_hierarchy(parts: list[str]) -> None:
    path = "/".join(parts) + ".gcode"
    assert require_valid_gcode_file_path(path) == path


@given(
    st.lists(
        st.one_of(
            st.from_regex(r"G1 X-?\d{1,4} Y-?\d{1,4} Z-?\d{1,4}", fullmatch=True),
            st.from_regex(r"M10[49] S\d{1,4}", fullmatch=True),
            st.from_regex(r"M1[49]0 S\d{1,4}", fullmatch=True),
            st.text(max_size=80),
        ),
        max_size=200,
    )
)
def test_gcode_metadata_parser_is_bounded_and_deterministic(lines: list[str]) -> None:
    content = "\n".join(lines)
    first = parse_gcode_metadata(content)
    second = parse_gcode_metadata(content)

    assert first == second
    parsed_lines = content.splitlines()
    assert first.line_count == len(parsed_lines)
    assert 0 <= first.command_count <= len(parsed_lines)


@given(
    st.binary(max_size=4_096),
    st.text(
        alphabet=st.characters(
            whitelist_categories=("Ll", "Lu", "Nd"),
            whitelist_characters="_.:-",
        ),
        min_size=1,
        max_size=140,
    ),
)
def test_idempotency_key_and_fingerprint_are_deterministic(
    body: bytes,
    key: str,
) -> None:
    first = request_fingerprint("POST", "/api/jobs", "page=1", body, "application/json")
    second = request_fingerprint("POST", "/api/jobs", "page=1", body, "application/json")

    assert first == second
    assert len(first) == 64
    assert KEY_PATTERN.fullmatch(key) is None or 8 <= len(key) <= 128


@given(st.binary(max_size=8_192), st.binary(min_size=1, max_size=32))
def test_webhook_signature_rejects_payload_or_signature_tampering(
    body: bytes,
    tamper: bytes,
) -> None:
    adapter = SandboxPaymentAdapter("synthetic-webhook-secret")
    signature = adapter.sign(body)

    with pytest.raises((PermissionError, ValueError, UnicodeDecodeError)):
        adapter.authenticate_event(body + tamper, signature)
