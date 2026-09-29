from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import require_current_user
from app.social_notifications import (
    ContentFollowPayload,
    ContentFollowRecord,
    FollowEntityType,
    NotificationCenterResponse,
    NotificationPreference,
    NotificationPreferenceUpdate,
    NotificationStatus,
    SocialNotificationRecord,
    SocialNotificationsRepository,
)


router = APIRouter(tags=["social-notifications"])


def get_notifications_repository() -> SocialNotificationsRepository:
    return SocialNotificationsRepository(get_settings().database_path)


@router.get("/api/social/notifications", response_model=NotificationCenterResponse)
async def notification_center(
    status_filter: NotificationStatus | None = None,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialNotificationsRepository = Depends(get_notifications_repository),
) -> NotificationCenterResponse:
    return repository.notification_center(current.user.id, status=status_filter)


@router.put("/api/social/notifications/preferences", response_model=list[NotificationPreference])
async def update_notification_preference(
    payload: NotificationPreferenceUpdate,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialNotificationsRepository = Depends(get_notifications_repository),
) -> list[NotificationPreference]:
    return repository.update_preference(current.user.id, payload)


@router.post("/api/social/notifications/{notification_id}/read", response_model=SocialNotificationRecord)
async def mark_notification_read(
    notification_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialNotificationsRepository = Depends(get_notifications_repository),
) -> SocialNotificationRecord:
    try:
        return repository.mark_read(current.user.id, notification_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/api/social/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialNotificationsRepository = Depends(get_notifications_repository),
) -> None:
    repository.mark_all_read(current.user.id)


@router.post("/api/social/content-follows", response_model=ContentFollowRecord)
async def follow_content(
    payload: ContentFollowPayload,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialNotificationsRepository = Depends(get_notifications_repository),
) -> ContentFollowRecord:
    try:
        return repository.follow_content(current.user.id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/api/social/content-follows/{entity_type}/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_content(
    entity_type: FollowEntityType,
    entity_id: int,
    current: CurrentUser = Depends(require_current_user),
    repository: SocialNotificationsRepository = Depends(get_notifications_repository),
) -> None:
    repository.unfollow_content(current.user.id, entity_type, entity_id)
