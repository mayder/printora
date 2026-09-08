import base64
import importlib.util
import io
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/cloud' / (name + '.py'))
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def test_recovery_container_cannot_write_custody_or_open_network(tmp_path):
    runner = module('offhost-restore-runner')
    command = runner.command('sha256:' + 'a' * 64, 'printora-restore-test', tmp_path, tmp_path / 'secret')
    assert '--device-read-bps=/dev/sda:16mb' in command
    assert '--device-write-bps=/dev/sda:16mb' in command
    assert '--network=none' in command and '--read-only' in command and '--cap-drop=ALL' in command
    assert f'type=bind,src={runner.REPOSITORY},dst=/custody,readonly' in command
    assert not any('pg_wal' in argument for argument in command)
    with pytest.raises(ValueError):
        runner.command('postgres:latest', 'test', tmp_path, tmp_path / 'secret')


@pytest.mark.parametrize('payload', ['x' * 32769, '{}', '{"password":"not-base64"}'])
def test_invalid_request_fails_closed(payload):
    with pytest.raises((ValueError, KeyError)):
        module('offhost-restore-runner').request(io.StringIO(payload))


def test_passed_sync_required():
    payload = {'password': base64.b64encode(b'test-fixture').decode(),
               'wal_sync': {'status': 'failed'}, 'backend_fingerprint': 'a' * 64}
    with pytest.raises(ValueError):
        module('offhost-restore-runner').request(io.StringIO(json.dumps(payload)))


def test_fingerprint_changes_with_application_but_ignores_bytecode(tmp_path):
    client = module('offhost-restore-client')
    (tmp_path / 'app').mkdir()
    for relative in ('pyproject.toml', 'uv.lock', 'app/config.py'):
        (tmp_path / relative).write_text('fixture')
    before = client.backend_fingerprint(tmp_path)
    (tmp_path / 'app/__pycache__').mkdir()
    (tmp_path / 'app/__pycache__/config.pyc').write_bytes(b'bytecode')
    (tmp_path / 'app/._config.py').write_bytes(b'AppleDouble metadata')
    assert client.backend_fingerprint(tmp_path) == before
    (tmp_path / 'app/config.py').write_text('changed')
    assert client.backend_fingerprint(tmp_path) != before


def test_failed_restore_replaces_previous_success_before_exit():
    wrapper = (ROOT / 'scripts/cloud/run-restore-test.sh').read_text()
    assert '"passed" if sys.argv[3] == "0" else "failed"' in wrapper
    assert wrapper.index('mv -f "$state_next" "$state_file"') < wrapper.index('exit "$result"')


def test_schema_comparison_ignores_only_metadata_and_rejects_sql_change(tmp_path):
    import subprocess
    before, after = tmp_path / 'before', tmp_path / 'after'
    before.mkdir()
    after.mkdir()
    for root in (before, after):
        (root / 'schema.sql').write_text('SELECT 1;')
    (before / '._schema.sql').write_bytes(b'AppleDouble')
    args = ['diff', '-qr', '--exclude=._*', str(before), str(after)]
    assert subprocess.run(args, capture_output=True).returncode == 0
    (after / 'schema.sql').write_text('SELECT 2;')
    assert subprocess.run(args, capture_output=True).returncode == 1
