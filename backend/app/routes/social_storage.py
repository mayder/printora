from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth import CurrentUser
from app.config import get_settings
from app.routes.auth import require_current_user
from app.social_storage import SocialStorageRepository, StorageReport, StorageRetentionPlan


router = APIRouter(tags=["social-storage"])


def get_storage_repository() -> SocialStorageRepository:
    return SocialStorageRepository(get_settings().database_path)


@router.get("/api/social/me/library/storage", response_model=StorageReport)
async def library_storage_report(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialStorageRepository = Depends(get_storage_repository),
) -> StorageReport:
    return repository.report_for_user(current.user.id)


@router.post("/api/social/me/library/storage/retention-reviews", response_model=StorageRetentionPlan)
async def create_library_retention_review(
    current: CurrentUser = Depends(require_current_user),
    repository: SocialStorageRepository = Depends(get_storage_repository),
) -> StorageRetentionPlan:
    return repository.create_retention_review(current.user.id, current.user.id)
