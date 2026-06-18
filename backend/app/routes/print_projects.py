from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.print_projects import (
    PrintProjectContract,
    PrintProjectDetail,
    PrintProjectSaveRequest,
    PrintProjectShareRequest,
    PrintProjectSummary,
    PrintProjectsRepository,
)
from app.routes.auth import CurrentUser, require_current_user

router = APIRouter(tags=["print-projects"])


def get_print_projects_repository() -> PrintProjectsRepository:
    return PrintProjectsRepository(get_settings().database_path)


@router.get("/api/print-projects/contract", response_model=PrintProjectContract)
async def print_projects_contract(
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectContract:
    return repository.contract()


@router.get("/api/print-projects", response_model=list[PrintProjectSummary])
async def explore_print_projects(
    q: str = "",
    file_kind: str = "",
    license: str = "",
    origin: str = "",
    community: str = "",
    limit: int = 24,
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> list[PrintProjectSummary]:
    return repository.explore(q, file_kind, license, origin, community, limit)


@router.get("/api/print-projects/{slug}", response_model=PrintProjectDetail)
async def print_project_detail(
    slug: str,
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    detail = repository.detail(slug)
    if detail is None:
        raise HTTPException(status_code=404, detail="projeto não encontrado")
    return detail


@router.post("/api/print-projects/{project_id}/save", response_model=PrintProjectDetail)
async def save_print_project(
    project_id: int,
    payload: PrintProjectSaveRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    try:
        return repository.save_project(current.user.id, project_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/print-projects/{project_id}/communities", response_model=PrintProjectDetail)
async def share_print_project_with_community(
    project_id: int,
    payload: PrintProjectShareRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    try:
        return repository.share_with_community(current.user.id, project_id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/social/communities/{slug}/projects", response_model=list[PrintProjectSummary])
async def community_print_projects(
    slug: str,
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> list[PrintProjectSummary]:
    return repository.community_projects(slug)
