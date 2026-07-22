from __future__ import annotations

from pathlib import Path

from fastapi import Depends, Response

from app.install_diagnostics import InstallationDiagnosticsResponse, build_installation_diagnostics
from app.database import get_database_version_info, get_public_database_version_info
from app.operational import http_metrics, readiness
from app.routes.auth import require_current_user, require_current_user_when_configured
from app.routes.support import *

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "Printora"}


@router.get("/ready")
async def ready(response: Response) -> dict[str, object]:
    is_ready, payload = readiness(get_settings())
    if not is_ready:
        response.status_code = 503
    return payload


@router.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    return Response(content=http_metrics.render(), media_type="text/plain; version=0.0.4")




@router.get("/api/system/version")
async def system_version() -> dict[str, object]:
    settings = get_settings()
    return get_public_database_version_info(settings.database_path)


@router.get("/api/system/version/internal")
async def system_version_internal(current=Depends(require_current_user)) -> dict[str, object]:
    if current.user.email.lower() != "breno@mayder.com.br":
        raise HTTPException(status_code=403, detail="acesso restrito ao suporte")
    settings = get_settings()
    return get_database_version_info(settings.database_path, settings.data_dir)


@router.get("/api/system/install-diagnostics")
async def system_install_diagnostics() -> InstallationDiagnosticsResponse:
    settings = get_settings()
    return build_installation_diagnostics(
        settings=settings,
        project_root=Path(__file__).resolve().parents[3],
    )




@router.get("/api/system/releases")
async def system_releases() -> ReleasesResponse:
    settings = get_settings()
    if settings.release_source_mode == "disabled":
        return build_unavailable_releases_response(
            source=settings.release_source_mode,
            channel=settings.release_channel,
            status="disabled",
        )
    client = GitHubReleaseClient(
        owner=settings.release_github_owner,
        repo=settings.release_github_repo,
        api_base_url=settings.release_github_api_base_url,
        timeout_seconds=settings.release_request_timeout_seconds,
        fixture_path=settings.release_fixture_path if settings.release_source_mode == "fixture" else None,
    )
    try:
        raw_releases = await client.fetch_releases()
    except httpx.HTTPStatusError as exc:
        status = "rate_limited" if _is_github_rate_limit(exc.response) else "offline"
        return build_unavailable_releases_response(
            source=settings.release_source_mode,
            channel=settings.release_channel,
            status=status,
            error=_github_http_error_detail(exc),
        )
    except httpx.HTTPError as exc:
        return build_unavailable_releases_response(
            source=settings.release_source_mode,
            channel=settings.release_channel,
            status="offline",
            error=str(exc),
        )
    except (OSError, ValueError) as exc:
        return build_unavailable_releases_response(
            source=settings.release_source_mode,
            channel=settings.release_channel,
            status="error",
            error=str(exc),
        )
    return build_releases_response(
        raw_releases=raw_releases,
        source=settings.release_source_mode,
        channel=settings.release_channel,
    )




@router.get("/api/system/update/status")
async def system_update_status() -> dict[str, object]:
    releases = await system_releases()
    environment = detect_update_environment()
    update_supported = environment in {"android_termux", "unix", "windows"}
    return {
        "safe_mode": "read_only",
        "update_supported": update_supported,
        "environment": environment,
        "installed_version": releases.installed_version,
        "channel": releases.channel,
        "update_status": releases.update_status,
        "latest_release_available": releases.latest_release_available,
        "latest_release": releases.latest_release.model_dump() if releases.latest_release else None,
        "status": releases.status,
        "message": "Update real disponível para Android/Termux, Unix e Windows." if update_supported else "Update real não suportado neste ambiente.",
        "release_error": releases.error,
    }




@router.post("/api/system/update/plan")
async def system_update_plan(payload: UpdatePlanRequest, _current=Depends(require_current_user_when_configured)) -> UpdatePlanResponse:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    try:
        return build_update_plan(
            repository=repository,
            request=payload,
            project_root=Path(__file__).resolve().parents[3],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.get("/api/system/update/history")
async def system_update_history(limit: int = 20, _current=Depends(require_current_user_when_configured)) -> UpdateHistoryResponse:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    repository.reconcile_interrupted_updates(installed_version=installed_app_version())
    return UpdateHistoryResponse(runs=repository.list_runs(limit=limit))


@router.post("/api/system/update/reconcile")
async def system_update_reconcile(_current=Depends(require_current_user_when_configured)) -> UpdateReconcileResponse:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    reconciled = repository.reconcile_interrupted_updates(
        installed_version=installed_app_version(),
        stale_after_minutes=1,
    )
    running_updates = repository.count_running_updates()
    message = (
        "Status de update reconciliado."
        if reconciled
        else "Nenhum update órfão antigo para reconciliar."
    )
    return UpdateReconcileResponse(
        reconciled=reconciled,
        running_updates=running_updates,
        message=message,
        runs=repository.list_runs(limit=20),
    )




@router.post("/api/system/update/apply")
async def system_update_apply(payload: UpdateApplyRequest, _current=Depends(require_current_user_when_configured)) -> UpdateApplyResponse:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    repository.reconcile_interrupted_updates(installed_version=installed_app_version())
    releases = await system_releases()
    stable_tags = None
    if releases.status == "ok":
        stable_tags = {
            release.tag
            for release in releases.releases
            if not release.prerelease and not release.draft and release.channel == "stable"
        }
    try:
        return apply_self_update(
            repository=repository,
            request=payload,
            project_root=Path(__file__).resolve().parents[3],
            script_path=settings.self_update_script_path,
            android_script_path=settings.self_update_android_script_path,
            unix_script_path=settings.self_update_unix_script_path,
            windows_script_path=settings.self_update_windows_script_path,
            stable_release_tags=stable_tags,
            timeout_seconds=settings.self_update_timeout_seconds,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 409 if "Já existe update" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc




@router.post("/api/system/update/rollback")
async def system_update_rollback(payload: UpdateRollbackRequest, _current=Depends(require_current_user_when_configured)) -> UpdateRollbackResponse:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    repository.reconcile_interrupted_updates(installed_version=installed_app_version())
    try:
        return rollback_self_update(
            repository=repository,
            request=payload,
            project_root=Path(__file__).resolve().parents[3],
            script_path=settings.self_update_script_path,
            android_script_path=settings.self_update_android_script_path,
            unix_script_path=settings.self_update_unix_script_path,
            windows_script_path=settings.self_update_windows_script_path,
            timeout_seconds=settings.self_update_timeout_seconds,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = 409 if "Já existe update" in detail else 400
        raise HTTPException(status_code=status_code, detail=detail) from exc




@router.get("/api/system/update/runs/{run_id}")
async def system_update_run(run_id: int, _current=Depends(require_current_user_when_configured)) -> UpdateRunRecord:
    settings = get_settings()
    repository = get_self_update_repository(settings)
    repository.reconcile_interrupted_updates(installed_version=installed_app_version())
    run = repository.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="update run not found")
    return run
