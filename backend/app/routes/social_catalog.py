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
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> PublicProfile:
    profile = repository.public_profile_by_slug(slug, current.user.id if current else None)
    if profile is None:
        raise HTTPException(status_code=404, detail="perfil público não encontrado")
    if profile.viewer_blocked:
        raise HTTPException(status_code=403, detail="perfil indisponível")
    return profile


@router.get("/api/social/profiles", response_model=list[PublicProfile])
async def search_public_profiles(
    q: str | None = None,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> list[PublicProfile]:
    try:
        return repository.search_profiles(q, current.user.id if current else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/social/profiles/{slug}/printers", response_model=list[PublicPrinter])
async def list_profile_public_printers(
    slug: str,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> list[PublicPrinter]:
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
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> PublicPrinter:
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
    _current: CurrentUser | None = Depends(require_current_user_when_configured),
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
    _current: CurrentUser | None = Depends(require_current_user_when_configured),
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
    _current: CurrentUser | None = Depends(require_current_user_when_configured),
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


@router.post("/api/social/communities/{slug}/posts", response_model=CommunityFeedSummary)
async def create_community_post(
    slug: str,
    payload: CommunityPostCreate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> CommunityFeedSummary:
    try:
        repository.create_community_post(slug, current.user.id, payload)
        feed = repository.list_community_feed(slug, order="recommended", page=1, page_size=20)
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
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> DiscussionComment:
    try:
        return repository.create_comment(post_id, current.user.id, payload)
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
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    try:
        repository.set_reaction("post", post_id, current.user.id, payload.reaction_type, True)
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
    comment_id: int | None = None,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> DiscussionDetail:
    try:
        repository.mark_solution(post_id, comment_id, current.user.id, is_social_admin(current))
        discussion = repository.discussion_detail(post_id)
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
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/api/social/relationships/{target_user_id}/friend-request", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_friendship_request(
    target_user_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    try:
        repository.cancel_friend_request(current.user.id, target_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/api/social/relationships/{requester_user_id}/friend-reject", status_code=status.HTTP_204_NO_CONTENT)
async def reject_friendship(
    requester_user_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    try:
        repository.reject_friend(current.user.id, requester_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/relationships/{target_user_id}/friend", status_code=status.HTTP_204_NO_CONTENT)
async def unfriend_user(
    target_user_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialCatalogRepository = Depends(get_social_repository),
) -> None:
    try:
        repository.unfriend(current.user.id, target_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


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
