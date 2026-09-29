FROM restic/restic@sha256:39d9072fb5651c80d75c7a811612eb60b4c06b32ffe87c2e9f3c7222e1797e76 AS restic
FROM postgres@sha256:bb3e1a57e5407e0a5280b4211980a5e537f4abd234a87014ac979849a78dd825
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-venv zstd && rm -rf /var/lib/apt/lists/*
COPY --from=restic /usr/bin/restic /usr/local/bin/restic-real
COPY packaging/recovery/restic-readonly.sh /usr/local/bin/restic
RUN chmod 0755 /usr/local/bin/restic && python3 -m venv /opt/tools && /opt/tools/bin/pip install --no-cache-dir uv==0.11.0
COPY backend/pyproject.toml backend/uv.lock /app/current/backend/
RUN VIRTUAL_ENV=/app/current/venv /opt/tools/bin/uv sync --active --frozen --no-dev --no-install-project --project /app/current/backend
COPY backend/app /app/current/backend/app
COPY scripts/cloud/restore-postgresql-backup-test.sh scripts/cloud/run-restore-test.sh scripts/cloud/wal_custody.py scripts/cloud/capacity_guard.py scripts/cloud/search-rebuild.py /usr/local/libexec/printora-cloud/
RUN chmod 0755 /usr/local/libexec/printora-cloud/* && mkdir -p /app/shared/backup-cache && printf '%s\n' 'RESTIC_REPOSITORY=/custody' 'RESTIC_PASSWORD_FILE=/run/printora/password' > /app/shared/backup-target.conf
ENV PRINTORA_BASE_PATH=/app
ENTRYPOINT ["/usr/local/libexec/printora-cloud/run-restore-test.sh"]
