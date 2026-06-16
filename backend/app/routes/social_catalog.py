from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

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
    CommunityFeedSummary,
    CommunityPostCreate,
    CommunityPostUpdate,
    DiscussionComment,
    DiscussionCommentCreate,
    DiscussionCommentUpdate,
    DiscussionDetail,
    DiscussionReactionPayload,
    FeedContentType,
    FeedOrder,
    LibraryCollectionCreate,
    LibraryCollectionItemCreate,
    LibraryItem,
    LibraryItemCreate,
    LibraryItemUpdate,
    LibraryOrganizerSummary,
    LibraryVersionCreate,
    PrintListCreate,
    PrintListItemCreate,
    PrintListItemUpdate,
    PrinterPublicUpdate,
    PublicPrinter,
    PublicProfile,
    PublicProfileUpdate,
    RelationshipRecord,
    RelationshipSummary,
    SocialCatalogRepository,
    TrustState,
)
from app.social_notifications import SocialNotificationsRepository
from app.social_safety import SocialSafetyRepository


router = APIRouter(tags=["social-catalog"])


def get_social_repository() -> SocialCatalogRepository:
    return SocialCatalogRepository(get_settings().database_path)


def get_notification_repository() -> SocialNotificationsRepository:
    return SocialNotificationsRepository(get_settings().database_path)


def get_safety_repository() -> SocialSafetyRepository:
    return SocialSafetyRepository(get_settings().database_path)


def require_catalog_admin(
    authorization: str | None = Header(default=None),
) -> CurrentUser:
    current = require_current_user(authorization=authorization, repository=get_auth_repository())
    if current.user.email.lower() != "breno@mayder.com.br":
        raise HTTPException(status_code=403, detail="curadoria do catálogo restrita ao administrador")
    return current


def optional_current_user(
    authorization: str | None = Header(default=None),
    repository=Depends(get_auth_repository),
) -> CurrentUser | None:
    if not authorization:
        return None
    try:
        return require_current_user(authorization=authorization, repository=repository)
    except HTTPException:
        return None


def is_social_admin(current: CurrentUser) -> bool:
    return current.user.email.lower() == "breno@mayder.com.br"


def _request_subject(request: Request, current: CurrentUser | None) -> str:
    if current is not None:
        return f"user:{current.user.id}"
    host = request.client.host if request.client else "unknown"
    agent = request.headers.get("user-agent", "")[:120]
    return f"anon:{host}:{agent}"


def _enforce_social_limit(
    repository: SocialSafetyRepository,
    request: Request,
    current: CurrentUser | None,
    action: str,
    *,
    target_user_id: int | None = None,
    subject_suffix: str = "",
) -> None:
    subject = _request_subject(request, current)
    if current is not None and subject_suffix:
        subject = f"{subject}:{subject_suffix}"
    result = repository.check_rate_limit(
        actor_user_id=current.user.id if current else None,
        action=action,
        subject=subject,
        target_user_id=target_user_id,
    )
    if not result.allowed:
        raise HTTPException(status_code=429, detail=result.reason, headers={"Retry-After": str(result.retry_after_seconds)})


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
    _current: CurrentUser = Depends(require_current_user),
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
    request: Request,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> PublicProfile:
    _enforce_social_limit(safety, request, current, "profile_lookup", subject_suffix=slug)
    profile = repository.public_profile_by_slug(slug, current.user.id if current else None)
    if profile is None:
        raise HTTPException(status_code=404, detail="perfil público não encontrado")
    if profile.viewer_blocked:
        raise HTTPException(status_code=403, detail="perfil indisponível")
    return profile


@router.get("/api/social/profiles", response_model=list[PublicProfile])
async def search_public_profiles(
    request: Request,
    q: str | None = None,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> list[PublicProfile]:
    try:
        _enforce_social_limit(safety, request, current, "profile_search", subject_suffix=q or "")
        return repository.search_profiles(q, current.user.id if current else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/social/profiles/{slug}/printers", response_model=list[PublicPrinter])
async def list_profile_public_printers(
    slug: str,
    request: Request,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> list[PublicPrinter]:
    _enforce_social_limit(safety, request, current, "profile_lookup", subject_suffix=f"{slug}:printers")
    profile = repository.public_profile_by_slug(slug, current.user.id if current else None)
    if profile is None:
        raise HTTPException(status_code=404, detail="perfil público não encontrado")
    if profile.viewer_blocked:
        raise HTTPException(status_code=403, detail="perfil indisponível")
    return repository.list_public_printers_for_profile(slug, current.user.id if current else None)


@router.get("/api/social/printers", response_model=list[PublicPrinter])
async def search_public_printers(
    manufacturer: str | None = None,
    model: str | None = None,
    variant: str | None = None,
    mod: str | None = None,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> list[PublicPrinter]:
    return repository.search_public_printers(
        manufacturer=manufacturer,
        model=model,
        variant=variant,
        mod=mod,
        viewer_user_id=current.user.id if current else None,
    )


@router.get("/api/public/printers/{printer_id}", response_model=PublicPrinter)
async def get_public_printer(
    printer_id: int,
    request: Request,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> PublicPrinter:
    _enforce_social_limit(safety, request, current, "profile_lookup", subject_suffix=f"printer:{printer_id}")
    printer = repository.public_printer(printer_id, current.user.id if current else None)
    if printer is None:
        raise HTTPException(status_code=404, detail="impressora pública não encontrada")
    return printer


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
    manufacturer: str | None = None,
    model: str | None = None,
    variant: str | None = None,
    component: str | None = None,
    _current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> list[Community]:
    return repository.list_communities(
        manufacturer=manufacturer,
        model=model,
        variant=variant,
        component=component,
    )


@router.get("/api/social/communities/{slug}", response_model=CommunityDetail)
async def get_social_community(
    slug: str,
    _current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> CommunityDetail:
    community = repository.community_detail(slug)
    if community is None:
        raise HTTPException(status_code=404, detail="comunidade não encontrada")
    return community


@router.get("/api/social/communities/{slug}/feed", response_model=CommunityFeedSummary)
async def get_social_community_feed(
    slug: str,
    content_type: FeedContentType | None = None,
    component: str | None = None,
    material: str | None = None,
    firmware_family: str | None = None,
    problem: str | None = None,
    order: FeedOrder = "recent",
    page: int = 1,
    page_size: int = 20,
    _current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> CommunityFeedSummary:
    feed = repository.list_community_feed(
        slug,
        content_type=content_type,
        component=component,
        material=material,
        firmware_family=firmware_family,
        problem=problem,
        order=order,
        page=page,
        page_size=page_size,
    )
    if feed is None:
        raise HTTPException(status_code=404, detail="comunidade não encontrada")
    return feed


@router.get("/api/social/communities/{slug}/library", response_model=list[LibraryItem])
async def list_community_library(
    slug: str,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> list[LibraryItem]:
    return repository.list_library_for_community(slug, current.user.id if current else None)


@router.get("/api/social/profiles/{slug}/library", response_model=list[LibraryItem])
async def list_profile_library(
    slug: str,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> list[LibraryItem]:
    return repository.list_library_for_profile(slug, current.user.id if current else None)


@router.get("/api/social/me/library/organizer", response_model=LibraryOrganizerSummary)
async def get_library_organizer(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryOrganizerSummary:
    return repository.library_organizer(current.user.id)


@router.post("/api/social/library/collections", response_model=LibraryOrganizerSummary)
async def create_library_collection(
    payload: LibraryCollectionCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryOrganizerSummary:
    try:
        return repository.create_library_collection(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/library/collections/{collection_id}/items", response_model=LibraryOrganizerSummary)
async def add_library_collection_item(
    collection_id: int,
    payload: LibraryCollectionItemCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryOrganizerSummary:
    try:
        return repository.add_library_collection_item(collection_id, current.user.id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/print-lists", response_model=LibraryOrganizerSummary)
async def create_print_list(
    payload: PrintListCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryOrganizerSummary:
    try:
        return repository.create_print_list(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/print-lists/{print_list_id}/items", response_model=LibraryOrganizerSummary)
async def add_print_list_item(
    print_list_id: int,
    payload: PrintListItemCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryOrganizerSummary:
    try:
        return repository.add_print_list_item(print_list_id, current.user.id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/api/social/print-list-items/{print_list_item_id}", response_model=LibraryOrganizerSummary)
async def update_print_list_item(
    print_list_item_id: int,
    payload: PrintListItemUpdate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryOrganizerSummary:
    try:
        return repository.update_print_list_item(print_list_item_id, current.user.id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/library", response_model=LibraryItem)
async def create_library_item(
    payload: LibraryItemCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryItem:
    try:
        return repository.create_library_item(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/social/library/{item_id}", response_model=LibraryItem)
async def get_library_item(
    item_id: int,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryItem:
    item = repository.library_item(item_id, current.user.id if current else None)
    if item is None:
        raise HTTPException(status_code=404, detail="arquivo não encontrado")
    return item


@router.post("/api/social/library/{item_id}/favorite", response_model=LibraryItem)
async def favorite_library_item(
    item_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryItem:
    try:
        return repository.set_library_favorite(item_id, current.user.id, True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/library/{item_id}/favorite", response_model=LibraryItem)
async def unfavorite_library_item(
    item_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryItem:
    try:
        return repository.set_library_favorite(item_id, current.user.id, False)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/api/social/library/{item_id}", response_model=LibraryItem)
async def update_library_item(
    item_id: int,
    payload: LibraryItemUpdate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryItem:
    try:
        return repository.update_library_item(item_id, current.user.id, is_social_admin(current), payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/library/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def archive_library_item(
    item_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    try:
        repository.archive_library_item(item_id, current.user.id, is_social_admin(current))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/library/{item_id}/downloads", response_model=LibraryItem)
async def register_library_download(
    item_id: int,
    request: Request,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> LibraryItem:
    _enforce_social_limit(safety, request, current, "library_download", subject_suffix=f"item:{item_id}")
    item = repository.register_library_download(item_id, current.user.id if current else None)
    if item is None:
        raise HTTPException(status_code=404, detail="arquivo não encontrado")
    return item


@router.post("/api/social/library/{item_id}/versions", response_model=LibraryItem)
async def create_library_version(
    item_id: int,
    payload: LibraryVersionCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryItem:
    try:
        return repository.create_library_version(item_id, current.user.id, is_social_admin(current), payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/library/{item_id}/versions/{version_id}/current", response_model=LibraryItem)
async def promote_library_version(
    item_id: int,
    version_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryItem:
    try:
        return repository.promote_library_version(item_id, version_id, current.user.id, is_social_admin(current))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/library/{item_id}/versions/{version_id}/downloads", response_model=LibraryItem)
async def register_library_version_download(
    item_id: int,
    version_id: int,
    request: Request,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> LibraryItem:
    try:
        _enforce_social_limit(safety, request, current, "library_download", subject_suffix=f"item:{item_id}:version:{version_id}")
        item = repository.register_library_download(item_id, current.user.id if current else None, version_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if item is None:
        raise HTTPException(status_code=404, detail="arquivo não encontrado")
    return item


@router.post("/api/social/library/{item_id}/files/upload", response_model=LibraryItem)
async def upload_library_file(
    item_id: int,
    request: Request,
    file_name: str,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryItem:
    try:
        return repository.upload_library_file(item_id, current.user.id, is_social_admin(current), file_name, await request.body())
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/library/files/{file_id}/analysis", response_model=LibraryItem)
async def analyze_library_file(
    file_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> LibraryItem:
    try:
        return repository.analyze_library_file(file_id, current.user.id, is_social_admin(current))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/communities/{slug}/posts", response_model=CommunityFeedSummary)
async def create_community_post(
    slug: str,
    payload: CommunityPostCreate,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> CommunityFeedSummary:
    try:
        _enforce_social_limit(safety, request, current, "content_mutation", subject_suffix=f"post:{slug}")
        post = repository.create_community_post(slug, current.user.id, payload)
        feed = repository.list_community_feed(slug, order="recommended", page=1, page_size=20)
        _notify_content_followers(
            current.user.id,
            "community",
            post.community_id,
            "community_post",
            "Nova discussão na comunidade",
            post.title,
            f"/c/{slug}",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if feed is None:
        raise HTTPException(status_code=404, detail="comunidade não encontrada")
    return feed


@router.get("/api/social/posts/{post_id}/discussion", response_model=DiscussionDetail)
async def get_discussion_detail(
    post_id: int,
    _current: CurrentUser | None = Depends(require_current_user_when_configured),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> DiscussionDetail:
    discussion = repository.discussion_detail(post_id)
    if discussion is None:
        raise HTTPException(status_code=404, detail="discussão não encontrada")
    return discussion


@router.put("/api/social/posts/{post_id}", response_model=DiscussionDetail)
async def update_post(
    post_id: int,
    payload: CommunityPostUpdate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> DiscussionDetail:
    try:
        repository.update_post(post_id, current.user.id, is_social_admin(current), payload)
        discussion = repository.discussion_detail(post_id)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if discussion is None:
        raise HTTPException(status_code=404, detail="discussão não encontrada")
    return discussion


@router.delete("/api/social/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    try:
        repository.delete_post(post_id, current.user.id, is_social_admin(current))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/posts/{post_id}/comments", response_model=DiscussionComment)
async def create_post_comment(
    post_id: int,
    payload: DiscussionCommentCreate,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> DiscussionComment:
    try:
        _enforce_social_limit(safety, request, current, "content_mutation", subject_suffix=f"comment:{post_id}")
        comment = repository.create_comment(post_id, current.user.id, payload)
        discussion = repository.discussion_detail(post_id)
        if discussion is not None:
            recipients = {discussion.post.author_user_id} if discussion.post.author_user_id else set()
            _notify_content_followers(
                current.user.id,
                "post",
                post_id,
                "comment",
                "Nova resposta em discussão",
                discussion.post.title,
                "/?section=social",
                recipients,
            )
        return comment
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/api/social/comments/{comment_id}", response_model=DiscussionComment)
async def update_comment(
    comment_id: int,
    payload: DiscussionCommentUpdate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> DiscussionComment:
    try:
        return repository.update_comment(comment_id, current.user.id, is_social_admin(current), payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    try:
        repository.delete_comment(comment_id, current.user.id, is_social_admin(current))
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/posts/{post_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def react_to_post(
    post_id: int,
    payload: DiscussionReactionPayload,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> None:
    try:
        _enforce_social_limit(safety, request, current, "content_mutation", subject_suffix=f"reaction:post:{post_id}")
        repository.set_reaction("post", post_id, current.user.id, payload.reaction_type, True)
        discussion = repository.discussion_detail(post_id)
        if discussion is not None and discussion.post.author_user_id:
            _notify_user(
                discussion.post.author_user_id,
                current.user.id,
                "reaction",
                "post",
                post_id,
                "Nova reação na sua discussão",
                discussion.post.title,
                "/?section=social",
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/posts/{post_id}/reactions/{reaction_type}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_post_reaction(
    post_id: int,
    reaction_type: str,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    if reaction_type not in {"like", "useful", "thanks"}:
        raise HTTPException(status_code=400, detail="reação inválida")
    repository.set_reaction("post", post_id, current.user.id, reaction_type, False)


@router.post("/api/social/comments/{comment_id}/reactions", status_code=status.HTTP_204_NO_CONTENT)
async def react_to_comment(
    comment_id: int,
    payload: DiscussionReactionPayload,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    try:
        repository.set_reaction("comment", comment_id, current.user.id, payload.reaction_type, True)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/posts/{post_id}/solution", response_model=DiscussionDetail)
async def mark_post_solution(
    post_id: int,
    request: Request,
    comment_id: int | None = None,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> DiscussionDetail:
    try:
        _enforce_social_limit(safety, request, current, "content_mutation", subject_suffix=f"solution:{post_id}")
        repository.mark_solution(post_id, comment_id, current.user.id, is_social_admin(current))
        discussion = repository.discussion_detail(post_id)
        if discussion is not None and comment_id is not None:
            recipients = {discussion.post.author_user_id} if discussion.post.author_user_id else set()
            _notify_content_followers(
                current.user.id,
                "post",
                post_id,
                "solution",
                "Solução marcada em discussão",
                discussion.post.title,
                "/?section=social",
                recipients,
            )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if discussion is None:
        raise HTTPException(status_code=404, detail="discussão não encontrada")
    return discussion


@router.get("/api/social/me/relationships", response_model=RelationshipSummary)
async def my_relationships(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> RelationshipSummary:
    return repository.relationship_summary(current.user.id)


@router.post("/api/social/relationships/{target_user_id}/follow", response_model=RelationshipRecord)
async def follow_user(
    target_user_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> RelationshipRecord:
    try:
        _enforce_social_limit(safety, request, current, "relationship_action", target_user_id=target_user_id, subject_suffix=f"follow:{target_user_id}")
        relationship = repository.set_relationship(current.user.id, target_user_id, "follow", "active")
        _notify_user(target_user_id, current.user.id, "follow", "relationship", current.user.id, "Novo seguidor", "Alguém começou a seguir seu perfil.", "/?section=social")
        return relationship
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/relationships/{target_user_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_user(
    target_user_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> None:
    _enforce_social_limit(safety, request, current, "relationship_action", target_user_id=target_user_id, subject_suffix=f"unfollow:{target_user_id}")
    repository.set_relationship(current.user.id, target_user_id, "follow", "ended")


@router.post("/api/social/relationships/{target_user_id}/friend-request", response_model=RelationshipRecord)
async def request_friendship(
    target_user_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> RelationshipRecord:
    try:
        _enforce_social_limit(safety, request, current, "relationship_action", target_user_id=target_user_id, subject_suffix=f"friend:{target_user_id}")
        relationship = repository.set_relationship(current.user.id, target_user_id, "friend", "pending")
        _notify_user(target_user_id, current.user.id, "friend_request", "relationship", current.user.id, "Nova solicitação de amizade", "Revise a solicitação em Relações.", "/?section=social")
        return relationship
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/relationships/{requester_user_id}/friend-accept", response_model=RelationshipRecord)
async def accept_friendship(
    requester_user_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> RelationshipRecord:
    try:
        _enforce_social_limit(safety, request, current, "relationship_action", target_user_id=requester_user_id, subject_suffix=f"accept:{requester_user_id}")
        relationship = repository.accept_friend(current.user.id, requester_user_id)
        _notify_user(requester_user_id, current.user.id, "friend_accept", "relationship", current.user.id, "Solicitação aceita", "A conexão social foi aceita.", "/?section=social")
        return relationship
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/social/relationships/{target_user_id}/friend-request", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_friendship_request(
    target_user_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> None:
    try:
        _enforce_social_limit(safety, request, current, "relationship_action", target_user_id=target_user_id, subject_suffix=f"cancel:{target_user_id}")
        repository.cancel_friend_request(current.user.id, target_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/relationships/{requester_user_id}/friend-reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_friendship(
    requester_user_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> None:
    try:
        _enforce_social_limit(safety, request, current, "relationship_action", target_user_id=requester_user_id, subject_suffix=f"reject:{requester_user_id}")
        repository.reject_friend(current.user.id, requester_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/relationships/{target_user_id}/friend", status_code=status.HTTP_204_NO_CONTENT)
async def unfriend_user(
    target_user_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> None:
    try:
        _enforce_social_limit(safety, request, current, "relationship_action", target_user_id=target_user_id, subject_suffix=f"unfriend:{target_user_id}")
        repository.unfriend(current.user.id, target_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/relationships/{target_user_id}/block", response_model=RelationshipRecord)
async def block_user(
    target_user_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> RelationshipRecord:
    try:
        _enforce_social_limit(safety, request, current, "relationship_action", target_user_id=target_user_id, subject_suffix=f"block:{target_user_id}")
        return repository.set_relationship(current.user.id, target_user_id, "block", "active")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/relationships/{target_user_id}/block", status_code=status.HTTP_204_NO_CONTENT)
async def unblock_user(
    target_user_id: int,
    request: Request,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
    safety: SocialSafetyRepository = Depends(get_safety_repository),
) -> None:
    _enforce_social_limit(safety, request, current, "relationship_action", target_user_id=target_user_id, subject_suffix=f"unblock:{target_user_id}")
    repository.set_relationship(current.user.id, target_user_id, "block", "ended")


def _notify_user(
    recipient_user_id: int,
    actor_user_id: int,
    notification_type: str,
    entity_type: str,
    entity_id: int,
    title: str,
    body: str,
    action_url: str | None,
) -> None:
    try:
        get_notification_repository().create_notification(
            recipient_user_id,
            actor_user_id=actor_user_id,
            notification_type=notification_type,
            entity_type=entity_type,
            entity_id=entity_id,
            title=title,
            body=body,
            action_url=action_url,
        )
    except Exception:
        return


def _notify_content_followers(
    actor_user_id: int,
    entity_type: str,
    entity_id: int,
    notification_type: str,
    title: str,
    body: str,
    action_url: str | None,
    extra_recipient_user_ids: set[int] | None = None,
) -> None:
    try:
        get_notification_repository().notify_content_followers(
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            notification_type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
            extra_recipient_user_ids=extra_recipient_user_ids,
        )
    except Exception:
        return
