from __future__ import annotations

from fastapi import Depends

from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.get("/api/printers/{printer_id}/backup/policies")
async def list_backup_policies(printer_id: int) -> dict[str, list[BackupPolicyRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    backup_repository = get_backup_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"policies": backup_repository.list_policies(printer_id)}




@router.post("/api/printers/{printer_id}/backup/policies")
async def create_backup_policy(printer_id: int, payload: BackupPolicyCreate) -> BackupPolicyRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    backup_repository = get_backup_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return backup_repository.create_policy(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/printers/{printer_id}/backup/runs")
async def list_backup_runs(printer_id: int, limit: int = 20) -> dict[str, list[BackupRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    backup_repository = get_backup_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": backup_repository.list_runs(printer_id, clean_limit)}




@router.post("/api/backup/policies/{policy_id}/dry-run")
async def create_backup_dry_run(policy_id: int) -> BackupRunRecord:
    settings = get_settings()
    backup_repository = get_backup_repository(settings)
    run = backup_repository.create_dry_run(policy_id)
    if run is None:
        raise HTTPException(status_code=404, detail="backup policy not found")
    return run




@router.post("/api/backup/policies/{policy_id}/execute-local")
async def execute_local_backup(policy_id: int) -> BackupRunRecord:
    import base64
    import json

    settings = get_settings()
    backup_repository = get_backup_repository(settings)
    policy = backup_repository.get_policy(policy_id)
    if policy is None:
        raise HTTPException(status_code=404, detail="backup policy not found")
    if policy.dry_run_only:
        run = backup_repository.execute_local_backup(policy_id)
        if run is None:
            raise HTTPException(status_code=404, detail="backup policy not found")
        return run
    printer_repository = get_printer_repository(settings)
    printer = printer_repository.get_printer(policy.printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    policy_payload = base64.b64encode(
        json.dumps(
            {
                "source_path": policy.source_path,
                "destination_path": policy.destination_path,
                "include_patterns": policy.include_patterns,
                "exclude_patterns": policy.exclude_patterns,
                "policy_id": policy.id,
                "printer_id": policy.printer_id,
            },
            ensure_ascii=False,
        ).encode()
    ).decode()
    script = _agent_backup_script(policy_payload)
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_host_script",
            payload={"kind": "backup_execute", "script": script, "timeout_seconds": 120},
            timeout_seconds=130,
        )
    except Exception as exc:
        return backup_repository.record_agent_backup_result(policy, status="failed", total_files=0, total_bytes=0, message=str(exc))
    result = job.result if isinstance(job.result, dict) else {}
    stdout = str(result.get("stdout") or "")
    try:
        payload = json.loads(stdout.strip().splitlines()[-1])
    except Exception:
        payload = {"status": "failed", "total_files": 0, "total_bytes": 0, "message": stdout[-500:] or str(result.get("error") or "")}
    return backup_repository.record_agent_backup_result(
        policy,
        status=str(payload.get("status") or "failed"),
        total_files=int(payload.get("total_files") or 0),
        total_bytes=int(payload.get("total_bytes") or 0),
        message=str(payload.get("message") or ""),
    )


def _agent_backup_script(policy_payload_b64: str) -> str:
    return f"""set -euo pipefail
python3 - <<'PY'
import base64, datetime, fnmatch, json, os, pathlib, zipfile
policy = json.loads(base64.b64decode({policy_payload_b64!r}).decode())
source = pathlib.Path(policy["source_path"]).expanduser()
destination = pathlib.Path(policy["destination_path"]).expanduser()
if not source.exists() or not source.is_dir():
    print(json.dumps({{"status":"failed","total_files":0,"total_bytes":0,"message":f"Origem inválida ou inexistente: {{source}}"}}))
    raise SystemExit(0)
source = source.resolve()
destination.mkdir(parents=True, exist_ok=True)
destination = destination.resolve()
if destination == source or source in destination.parents:
    print(json.dumps({{"status":"failed","total_files":0,"total_bytes":0,"message":"Destino não pode ficar dentro da origem do backup."}}))
    raise SystemExit(0)
include = policy.get("include_patterns") or ["**/*"]
exclude = policy.get("exclude_patterns") or []
def match(path, patterns):
    text = path.as_posix()
    return any(fnmatch.fnmatch(text, p) or fnmatch.fnmatch(path.name, p) for p in patterns)
files = []
for item in source.rglob("*"):
    if not item.is_file():
        continue
    rel = item.relative_to(source)
    if include and not match(rel, include):
        continue
    if exclude and match(rel, exclude):
        continue
    files.append(item)
stamp = datetime.datetime.utcnow().strftime("%Y%m%d-%H%M%S")
archive_path = destination / f"printora-backup-{{policy['printer_id']}}-{{policy['policy_id']}}-{{stamp}}.zip"
total = 0
with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
    for item in files:
        rel = item.relative_to(source)
        archive.write(item, rel.as_posix())
        total += item.stat().st_size
print(json.dumps({{"status":"completed","total_files":len(files),"total_bytes":total,"message":f"Backup criado pelo agente em {{archive_path}}"}}))
PY
"""




@router.post("/api/backup/archives/compare")
async def compare_backup_archives_endpoint(payload: BackupArchiveCompareRequest) -> BackupArchiveCompareResponse:
    try:
        return compare_backup_archives(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/backup/restore-plan")
async def backup_restore_plan(payload: BackupRestorePlanRequest) -> BackupRestorePlanResponse:
    try:
        return build_backup_restore_plan(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/backup/restore-gate")
async def backup_restore_gate(payload: BackupRestoreExecuteRequest) -> BackupRestoreGateResponse:
    try:
        return build_backup_restore_gate(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
