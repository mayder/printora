from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from app.agent_executor import AgentCommandExecutor
from app.auth import current_auth_scope
from app.config import get_settings
from app.printers import PrinterRepository, PrinterRecord


async def run_host_script_via_agent(
    target: Any,
    script: str,
    *,
    timeout_seconds: float,
    env: dict[str, str] | None = None,
    kind: str = "host_script",
) -> dict[str, object]:
    settings = get_settings()
    printer = _resolve_printer_for_target(target)
    if printer is None:
        return {
            "stdout": "",
            "stderr": "",
            "exit_code": None,
            "error": "Nenhuma impressora com agente online corresponde a este alvo. Cadastre a impressora e pareie o agente antes deste fluxo cloud.",
        }
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_host_script",
            payload={
                "kind": kind,
                "script": script,
                "env": env or {},
                "timeout_seconds": timeout_seconds,
            },
            timeout_seconds=max(timeout_seconds, 10.0),
        )
    except Exception as exc:
        return {"stdout": "", "stderr": "", "exit_code": None, "error": str(exc)}
    result = job.result if isinstance(job.result, dict) else {}
    return {
        "stdout": str(result.get("stdout") or ""),
        "stderr": str(result.get("stderr") or ""),
        "exit_code": result.get("exit_code") if isinstance(result.get("exit_code"), int) else None,
        "error": str(result.get("error")) if result.get("error") else None,
    }


def _resolve_printer_for_target(target: Any) -> PrinterRecord | None:
    settings = get_settings()
    user_id, organization_ids = current_auth_scope()
    repository = PrinterRepository(settings.database_path, user_id=user_id, organization_ids=organization_ids)
    target_host = _clean(getattr(target, "host", None))
    if not target_host:
        return None
    for printer in repository.list_printers():
        if _matches_printer(repository, printer, target_host):
            return printer
    return None


def _matches_printer(repository: PrinterRepository, printer: PrinterRecord, target_host: str) -> bool:
    candidates = {
        _clean(printer.name),
        _clean(_url_host(printer.moonraker_url)),
        _clean(printer.moonraker_url),
    }
    ssh_access = repository.get_ssh_access(printer.id)
    if ssh_access is not None:
        candidates.add(_clean(ssh_access.host))
    return _clean(target_host) in {candidate for candidate in candidates if candidate}


def _url_host(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return urlparse(value).hostname
    except Exception:
        return None


def _clean(value: object) -> str:
    return str(value or "").strip().lower()
