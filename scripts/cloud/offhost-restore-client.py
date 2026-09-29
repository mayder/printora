#!/usr/bin/env python3
"""Run the isolated restore on a dedicated SSH target, never print its secret."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess


def backend_fingerprint(root):
    files = [root / 'pyproject.toml', root / 'uv.lock']
    files += sorted(path for path in (root / 'app').rglob('*')
                    if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc'
                    and not any(part.startswith('._') for part in path.parts))
    digest = hashlib.sha256()
    for path in files:
        digest.update(str(path.relative_to(root)).encode() + b'\0')
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def main():
    config = json.loads(Path('/etc/printora-cloud/restore-target.json').read_text())
    payload = {
        'password': base64.b64encode(Path(os.environ['RESTIC_PASSWORD_FILE']).read_bytes()).decode(),
        'backend_fingerprint': backend_fingerprint(Path(os.environ.get('PRINTORA_BASE_PATH', '/var/www/print3dmaker.xyz')) / 'current/backend'),
        'wal_sync': json.loads(Path('/var/lib/printora-cloud/recovery/wal-sync.json').read_text()),
    }
    command = ['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
               '-o', 'ConnectTimeout=10', '-o', 'ServerAliveInterval=15',
               '-o', 'ServerAliveCountMax=2', '-o', 'IdentitiesOnly=yes',
               '-o', 'UserKnownHostsFile=' + config['known_hosts'],
               '-i', config['key'], '-p', str(config['port']),
               config['user'] + '@' + config['host'], 'verify']
    result = subprocess.run(command, input=json.dumps(payload), capture_output=True,
                            text=True, timeout=870, check=False)
    if result.returncode:
        raise ValueError('offhost restore failed; inspect restricted target audit log')
    state = json.loads(result.stdout)
    if (state.get('status') != 'passed' or state.get('storage') != 'disk'
            or state.get('isolated') is not True or not state.get('image')):
        raise ValueError('invalid offhost restore evidence')
    print(json.dumps(state, sort_keys=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        raise SystemExit('offhost restore failed; no successful evidence written') from None
