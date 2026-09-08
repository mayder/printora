#!/usr/bin/env python3
"""Root-owned forced SSH executor: no shell commands and no writable custody."""
import base64
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

ROOT = Path('/var/lib/printora-cloud-offhost')
REPOSITORY = Path('/srv/printora-backup/repository')


def request(stream):
    raw = stream.read(32769)
    if len(raw) > 32768:
        raise ValueError('oversized request')
    payload = json.loads(raw)
    password = base64.b64decode(payload['password'], validate=True)
    if not 1 <= len(password) <= 4096 or payload['wal_sync'].get('status') != 'passed':
        raise ValueError('invalid request')
    return password, payload['wal_sync'], payload['backend_fingerprint']


def command(image, name, work, secret):
    if not re.fullmatch(r'sha256:[a-f0-9]{64}', image):
        raise ValueError('unconfigured image')
    return ['docker', 'run', '--rm', '--name', name, '--network=none', '--read-only',
            '--device-read-bps=/dev/sda:16mb', '--device-write-bps=/dev/sda:16mb',
            '--memory=8g', '--cpus=2', '--pids-limit=128', '--security-opt=no-new-privileges',
            '--cap-drop=ALL', '--cap-add=CHOWN', '--cap-add=SETUID', '--cap-add=SETGID',
            '--cap-add=DAC_OVERRIDE', '--cap-add=FOWNER', '--tmpfs', '/tmp:rw,nosuid,size=128m',
            '--mount', f'type=bind,src={REPOSITORY},dst=/custody,readonly',
            '--mount', f'type=bind,src={secret},dst=/run/printora/password,readonly',
            '--mount', f'type=bind,src={work / "postgresql"},dst=/var/lib/postgresql',
            '--mount', f'type=bind,src={work / "state"},dst=/var/lib/printora-cloud/recovery',
            '--mount', f'type=bind,src={ROOT / "cache"},dst=/app/shared/backup-cache', image]


def verify():
    password, sync, fingerprint = request(sys.stdin)
    if fingerprint != (ROOT / 'backend-fingerprint').read_text().strip():
        raise ValueError('restore image does not match active application')
    usage = shutil.disk_usage(ROOT)
    if usage.free < max(usage.total // 10, 20 * 1024**3):
        raise ValueError('offhost capacity insufficient')
    image = (ROOT / 'current-image').read_text().strip()
    name = 'printora-restore-' + uuid.uuid4().hex
    work = ROOT / 'work' / name
    for relative in ('postgresql', 'state'):
        (work / relative).mkdir(parents=True, mode=0o700)
    (work / 'postgresql').chmod(0o755)  # postgres must traverse the bind-mount root.
    (work / 'state/wal-sync.json').write_text(json.dumps(sync))
    log_path = ROOT / 'logs' / (name + '.log')
    try:
        with tempfile.TemporaryDirectory(prefix='printora-restore-', dir='/run') as tmp:
            secret = Path(tmp) / 'password'
            secret.write_bytes(password)
            secret.chmod(0o600)
            with log_path.open('xb') as log:
                result = subprocess.run(command(image, name, work, secret), stdout=log,
                                        stderr=subprocess.STDOUT, timeout=840, check=False)
            state = json.loads((work / 'state/restore-test.json').read_text())
            if result.returncode or state.get('status') != 'passed':
                raise ValueError('isolated restore failed')
            state.update(storage='disk', image=image, execution_host='186.196.9.58')
            (ROOT / 'last-restore.json').write_text(json.dumps(state) + '\n')
            print(json.dumps(state))
    finally:
        subprocess.run(['docker', 'rm', '-f', name], capture_output=True, timeout=30, check=False)
        private_log = work / 'state/restore-test-private.log'
        if private_log.is_file():
            with log_path.open('ab') as target, private_log.open('rb') as source:
                shutil.copyfileobj(source, target)
        shutil.rmtree(work)  # Only the UUID scratch created by this invocation.


def main():
    os.umask(0o077)
    if os.getuid() != 0 or sys.argv[1:] != ['verify']:
        raise ValueError('only verify is accepted')
    for name in ('work', 'cache', 'logs'):
        (ROOT / name).mkdir(parents=True, exist_ok=True, mode=0o700)
    with (ROOT / 'restore.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for path in (ROOT / 'logs').glob('printora-restore-*.log'):
            if path.is_file() and not path.is_symlink() and path.stat().st_mtime < time.time() - 180 * 86400:
                path.unlink()
        verify()


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('offhost restore failed; inspect root-only audit log') from None
