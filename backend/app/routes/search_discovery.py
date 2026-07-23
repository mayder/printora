from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import require_current_user
from app.routes.social_catalog import optional_current_user
from app.search_discovery import SearchDiscoveryRepository, SearchEntityType, SearchOrder, SearchResponse, TagRecord


router = APIRouter(tags=["search-discovery"])


def get_search_repository() -> SearchDiscoveryRepository:
    return SearchDiscoveryRepository(get_settings().database_path)


def require_search_admin(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    if current.user.email.lower() != "breno@mayder.com.br":
        raise HTTPException(status_code=403, detail="curadoria de tags restrita ao administrador")
    return current


@router.get("/api/social/search", response_model=SearchResponse)
async def search_social_content(
    q: str = "",
    entity_type: SearchEntityType | None = None,
    tag: str | None = None,
    community: str | None = None,
    printer: str | None = None,
    component: str | None = None,
    material: str | None = None,
    license: str | None = None,
    file_kind: str | None = None,
    order: SearchOrder = "relevance",
    page: int = 1,
    page_size: int = 20,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SearchDiscoveryRepository = Depends(get_search_repository),
) -> SearchResponse:
    return repository.search(
        query=q,
        entity_type=entity_type,
        tag=tag,
        community=community,
        printer=printer,
        component=component,
        material=material,
        license=license,
        file_kind=file_kind,
        order=order,
        page=page,
        page_size=page_size,
        viewer_user_id=current.user.id if current else None,
    )


@router.get("/api/social/tags", response_model=list[TagRecord])
async def list_social_tags(repository: SearchDiscoveryRepository = Depends(get_search_repository)) -> list[TagRecord]:
    return repository.list_tags()


@router.put("/api/social/tags/{slug}", response_model=TagRecord)
async def curate_social_tag(
    slug: str,
    status: str,
    current: CurrentUser = Depends(require_search_admin),
    repository: SearchDiscoveryRepository = Depends(get_search_repository),
) -> TagRecord:
    try:
        return repository.curate_tag(slug, status, current.user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
