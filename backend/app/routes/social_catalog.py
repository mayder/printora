from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import get_auth_repository, require_current_user, require_current_user_when_configured
from app.social_catalog import (
    CatalogAdminSummary,
    CatalogManufacturer,
    CatalogManufacturerCreate,
    CatalogModel,
    CatalogModelCreate,
    CatalogSummary,
    CatalogVariant,
    CatalogVariantCreate,
    CatalogVariantUpdate,
    Community,
    CommunityDetail,
    PrinterPublicUpdate,
    PublicPrinter,
    PublicProfile,
    PublicProfileUpdate,
    RelationshipRecord,
    RelationshipSummary,
    SocialCatalogRepository,
    TrustState,
)


router = APIRouter(tags=["social-catalog"])


def get_social_repository() -> SocialCatalogRepository:
    return SocialCatalogRepository(get_settings().database_path)


def require_catalog_admin(current: CurrentUser = Depends(require_current_user)) -> CurrentUser:
    if current.user.email.lower() != "breno@mayder.com.br":
        raise HTTPException(status_code=403, detail="curadoria do catálogo restrita ao administrador")
    return current


def optional_current_user(
    authorization: str | None = Header(default=None),
) -> CurrentUser | None:
    if not authorization:
        return None
    try:
        return require_current_user(authorization=authorization, repository=get_auth_repository())
    except HTTPException:
        return None


@router.get("/api/catalog", response_model=CatalogSummary)
async def list_catalog(repository: SocialCatalogRepository = Depends(get_social_repository)) -> CatalogSummary:
    return repository.list_catalog(include_blocked=False, include_obsolete=True)


@router.get("/api/catalog/admin", response_model=CatalogAdminSummary)
async def search_catalog_admin(
    manufacturer: str | None = None,
    model: str | None = None,
    variant: str | None = None,
    component: str | None = None,
    kinematics: str | None = None,
    firmware_family: str | None = None,
    trust_state: TrustState | None = None,
    _current: CurrentUser = Depends(require_catalog_admin),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> CatalogAdminSummary:
    return repository.search_catalog_admin(
        manufacturer=manufacturer,
        model=model,
        variant=variant,
        component=component,
        kinematics=kinematics,
        firmware_family=firmware_family,
        trust_state=trust_state,
    )


@router.post("/api/catalog/manufacturers", response_model=CatalogManufacturer)
async def create_catalog_manufacturer(
    payload: CatalogManufacturerCreate,
    current: CurrentUser = Depends(require_catalog_admin),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> CatalogManufacturer:
    try:
        return repository.create_manufacturer(payload, current.user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/catalog/models", response_model=CatalogModel)
async def create_catalog_model(
    payload: CatalogModelCreate,
    current: CurrentUser = Depends(require_catalog_admin),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> CatalogModel:
    try:
        return repository.create_model(payload, current.user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/catalog/variants", response_model=CatalogVariant)
async def create_catalog_variant(
    payload: CatalogVariantCreate,
    current: CurrentUser = Depends(require_catalog_admin),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> CatalogVariant:
    try:
        return repository.create_variant(payload, current.user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/api/catalog/variants/{variant_id}", response_model=CatalogVariant)
async def update_catalog_variant(
    variant_id: int,
    payload: CatalogVariantUpdate,
    current: CurrentUser = Depends(require_catalog_admin),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> CatalogVariant:
    try:
        return repository.update_variant(variant_id, payload, current.user.id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/social/me/profile", response_model=PublicProfile)
async def get_my_social_profile(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> PublicProfile:
    return repository.get_or_create_profile(current.user.id)


@router.put("/api/social/me/profile", response_model=PublicProfile)
async def update_my_social_profile(
    payload: PublicProfileUpdate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> PublicProfile:
    try:
        return repository.update_profile(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/social/profiles/{slug}", response_model=PublicProfile)
async def get_public_profile(
    slug: str,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> PublicProfile:
    profile = repository.public_profile_by_slug(slug, current.user.id if current else None)
    if profile is None:
        raise HTTPException(status_code=404, detail="perfil público não encontrado")
    if profile.viewer_blocked:
        raise HTTPException(status_code=403, detail="perfil indisponível")
    return profile


@router.get("/api/social/profiles/{slug}/printers", response_model=list[PublicPrinter])
async def list_profile_public_printers(
    slug: str,
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> list[PublicPrinter]:
    return repository.list_public_printers_for_profile(slug)


@router.put("/api/printers/{printer_id}/public-profile", response_model=PublicPrinter | None)
async def update_printer_public_profile(
    printer_id: int,
    payload: PrinterPublicUpdate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> PublicPrinter | None:
    try:
        record = repository.update_printer_public(printer_id, current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None and payload.public_profile_enabled:
        raise HTTPException(status_code=404, detail="impressora não encontrada")
    return record


@router.get("/api/social/communities", response_model=list[Community])
async def list_social_communities(
    _current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> list[Community]:
    return repository.list_communities()


@router.get("/api/social/communities/{slug}", response_model=CommunityDetail)
async def get_social_community(
    slug: str,
    _current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> CommunityDetail:
    community = repository.community_detail(slug)
    if community is None:
        raise HTTPException(status_code=404, detail="comunidade não encontrada")
    return community


@router.get("/api/social/me/relationships", response_model=RelationshipSummary)
async def my_relationships(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> RelationshipSummary:
    return repository.relationship_summary(current.user.id)


@router.post("/api/social/relationships/{target_user_id}/follow", response_model=RelationshipRecord)
async def follow_user(
    target_user_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> RelationshipRecord:
    try:
        return repository.set_relationship(current.user.id, target_user_id, "follow", "active")
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/relationships/{target_user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    target_user_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    repository.set_relationship(current.user.id, target_user_id, "follow", "ended")


@router.post("/api/social/relationships/{target_user_id}/friend-request", response_model=RelationshipRecord)
async def request_friendship(
    target_user_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> RelationshipRecord:
    try:
        return repository.set_relationship(current.user.id, target_user_id, "friend", "pending")
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/relationships/{requester_user_id}/friend-accept", response_model=RelationshipRecord)
async def accept_friendship(
    requester_user_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> RelationshipRecord:
    try:
        return repository.accept_friend(current.user.id, requester_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/social/relationships/{target_user_id}/block", response_model=RelationshipRecord)
async def block_user(
    target_user_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> RelationshipRecord:
    try:
        return repository.set_relationship(current.user.id, target_user_id, "block", "active")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/relationships/{target_user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(
    target_user_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    repository.set_relationship(current.user.id, target_user_id, "block", "ended")
