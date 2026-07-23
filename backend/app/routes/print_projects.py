from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.auth import AuthRepository
from app.config import get_settings
from app.print_projects import (
    PrintProjectCreateRequest,
    PrintProjectContract,
    PrintProjectDetail,
    PrintProjectExternalLinkRequest,
    PrintProjectPublicationRequest,
    PrintProjectPublicationReviewRequest,
    ProjectFileRole,
    PrintProjectSaveRequest,
    PrintProjectShareRequest,
    PrintProjectStorageReport,
    PrintProjectSummary,
    PrintProjectUpdateRequest,
    PrintProjectsRepository,
)
from app.routes.auth import CurrentUser, get_auth_repository, require_current_user
from app.routes.social_catalog import is_social_admin
from app.upload_stream import read_limited_upload

router = APIRouter(tags=["print-projects"])


def get_print_projects_repository() -> PrintProjectsRepository:
    return PrintProjectsRepository(get_settings().database_path)


def optional_current_user(
    authorization: str | None = Header(default=None),
    repository: AuthRepository = Depends(get_auth_repository),
) -> CurrentUser | None:
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        return None
    user = repository.get_user_by_session(token)
    if user is None:
        return None
    return CurrentUser(user=user, token=token)


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


@router.get("/api/print-projects/me", response_model=list[PrintProjectSummary])
async def my_print_projects(
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> list[PrintProjectSummary]:
    return repository.my_projects(current.user.id)


@router.get("/api/print-projects/me/storage", response_model=PrintProjectStorageReport)
async def my_print_project_storage(
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectStorageReport:
    return repository.storage_report(current.user.id)


@router.post("/api/print-projects", response_model=PrintProjectDetail)
async def create_print_project(
    payload: PrintProjectCreateRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    try:
        return repository.create_project(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/print-projects/{slug}", response_model=PrintProjectDetail)
async def print_project_detail(
    slug: str,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    detail = repository.detail(slug, current.user.id if current is not None else None)
    if detail is None:
        raise HTTPException(status_code=404, detail="projeto não encontrado")
    return detail


@router.patch("/api/print-projects/{project_id}", response_model=PrintProjectDetail)
async def update_print_project(
    project_id: int,
    payload: PrintProjectUpdateRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    try:
        return repository.update_project(current.user.id, project_id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/print-projects/{project_id}")
async def archive_print_project(
    project_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> dict[str, bool]:
    try:
        repository.archive_project(current.user.id, project_id)
        return {"ok": True}
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.put("/api/print-projects/{project_id}/publication", response_model=PrintProjectDetail)
async def update_print_project_publication(
    project_id: int,
    payload: PrintProjectPublicationRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    try:
        return repository.update_publication(current.user.id, project_id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/print-projects/{project_id}/publication-review", response_model=PrintProjectDetail)
async def review_print_project_publication(
    project_id: int,
    payload: PrintProjectPublicationReviewRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    if not is_social_admin(current):
        raise HTTPException(status_code=403, detail="revisão de publicação restrita ao administrador")
    try:
        return repository.review_publication(current.user.id, project_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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


@router.post(
    "/api/print-projects/{project_id}/files/upload",
    response_model=PrintProjectDetail,
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {"application/octet-stream": {"schema": {"type": "string", "format": "binary"}}},
        }
    },
)
async def upload_print_project_file(
    project_id: int,
    request: Request,
    file_name: str,
    file_role: ProjectFileRole = "printable",
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    try:
        body = await read_limited_upload(request, 25 * 1024 * 1024)
        return repository.upload_file(current.user.id, project_id, file_name, file_role, body)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/print-projects/{project_id}/external-links", response_model=PrintProjectDetail)
async def add_print_project_external_link(
    project_id: int,
    payload: PrintProjectExternalLinkRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectDetail:
    try:
        return repository.add_external_link(current.user.id, project_id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
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
