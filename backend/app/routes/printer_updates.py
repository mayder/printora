from __future__ import annotations

from fastapi import Depends

from app.agent_executor import AgentCommandExecutor
from app.agent_moonraker import status_payload
from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.post("/api/printers/{printer_id}/updates/refresh")
async def refresh_printer_update_status(
    printer_id: int,
    payload: UpdateRefreshRequest,
) -> UpdateActionResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    target = payload.name or "all"
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_update_action",
            payload={"action": "refresh", "target": target},
            timeout_seconds=max(settings.request_timeout_seconds, 60.0),
        )
    except HTTPException as exc:
        if exc.status_code in {502, 504} and _looks_like_update_refresh_timeout(exc.detail):
            return UpdateActionResponse(
                safe_mode="agent_update_manager",
                action="refresh",
                target=target,
                accepted=False,
                message="Moonraker demorou para concluir a reanálise. O status será relido pelo agente sem tratar isso como falha da aplicação.",
                result={"status": "timeout", "detail": str(exc.detail)[:500]},
            )
        raise
    return UpdateActionResponse(
        safe_mode="agent_update_manager",
        action="refresh",
        target=target,
        accepted=True,
        message="Reanalise solicitada ao Moonraker pelo agente.",
        result=job.result or {},
    )


@router.post("/api/printers/{printer_id}/updates/silences")
async def silence_printer_update_alert(
    printer_id: int,
    payload: UpdateSilenceRequest,
) -> UpdateSilenceResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    component_name, component_payload = _update_silence_payload(payload)
    silence = get_update_alert_silence_repository(settings).silence_component(
        printer_id,
        component_name,
        component_payload,
        reason=payload.reason,
    )
    return UpdateSilenceResponse(
        safe_mode="moonraker_update_manager",
        target=component_name,
        silenced=True,
        message="Alerta desta versão silenciado. Ele volta automaticamente quando a versão mudar.",
        silence_id=silence.id,
    )


@router.post("/api/printers/{printer_id}/updates/silences/clear")
async def clear_printer_update_alert_silence(
    printer_id: int,
    payload: UpdateSilenceRequest,
) -> UpdateSilenceResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    component_name, component_payload = _update_silence_payload(payload)
    version_key = update_component_version_key(component_name, component_payload)
    removed = get_update_alert_silence_repository(settings).delete_matching(printer_id, component_name, version_key)
    if not removed:
        removed = get_update_alert_silence_repository(settings).delete_matching(printer_id, component_name)
    return UpdateSilenceResponse(
        safe_mode="moonraker_update_manager",
        target=component_name,
        silenced=False,
        message="Alerta reativado." if removed else "Nenhum silêncio ativo encontrado para este componente.",
        silence_id=None,
    )


def _update_silence_payload(payload: UpdateSilenceRequest) -> tuple[str, dict[str, Any]]:
    component_name = payload.target.strip()
    if component_name == "all":
        raise HTTPException(status_code=400, detail="silêncio deve ser por componente")
    return component_name, {
        "version": payload.current_version,
        "remote_version": payload.remote_version,
        "full_version_string": payload.full_version,
        "commits_behind_count": payload.commits_behind_count,
        "package_count": payload.package_count,
        "warnings": payload.warnings,
        "anomalies": payload.anomalies,
    }


def _looks_like_update_refresh_timeout(detail: Any) -> bool:
    text = str(detail).lower()
    return "timeout" in text or "deadline exceeded" in text or "awaiting headers" in text


@router.post("/api/printers/{printer_id}/updates/run")
async def run_printer_update(printer_id: int, payload: UpdateRunRequest) -> UpdateActionResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    route, target = update_route_for_target(payload.target)
    await _guard_risky_update(settings, printer, target, payload.confirmation_phrase)
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_update_action",
            payload={"action": "update", "target": target},
            timeout_seconds=max(settings.request_timeout_seconds, 60.0),
        )
    except HTTPException:
        raise
    return UpdateActionResponse(
        safe_mode="agent_update_manager",
        action="update",
        target=target,
        accepted=True,
        message=f"Update solicitado ao Moonraker via agente ({route}).",
        result=job.result or {},
    )


@router.post("/api/printers/{printer_id}/updates/rollback")
async def rollback_printer_update(printer_id: int, payload: PrinterUpdateRollbackRequest) -> UpdateActionResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    target = payload.target.strip()
    if target == "all":
        raise HTTPException(status_code=400, detail="rollback deve ser executado por componente")
    if payload.confirmation_phrase.strip() != ROLLBACK_CONFIRMATION_PHRASE:
        raise HTTPException(status_code=409, detail=f"rollback exige confirmação literal: {ROLLBACK_CONFIRMATION_PHRASE}")

    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_update_action",
            payload={"action": "rollback", "target": target},
            timeout_seconds=max(settings.request_timeout_seconds, 60.0),
        )
    except HTTPException:
        raise
    return UpdateActionResponse(
        safe_mode="agent_update_manager",
        action="rollback",
        target=target,
        accepted=True,
        message=f"Rollback de {target} solicitado ao Moonraker pelo agente.",
        result=job.result or {},
    )


async def _guard_risky_update(settings, printer, target: str, confirmation_phrase: str | None) -> None:
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_update_status",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        status = build_update_status(status_payload(job.result)[4])
    except HTTPException:
        raise
    risky_components = risky_update_components(status, target)
    if not risky_components:
        return
    if (confirmation_phrase or "").strip() == RISK_UPDATE_CONFIRMATION_PHRASE:
        return
    component_names = ", ".join(item.title for item in risky_components)
    raise HTTPException(
        status_code=409,
        detail=(
            f"Update de risco alto bloqueado para {component_names}. "
            f"Para continuar, confirme literalmente: {RISK_UPDATE_CONFIRMATION_PHRASE}"
        ),
    )
