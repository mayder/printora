from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.config import get_settings
from app.auth import CurrentUser
from app.routes.social_catalog import optional_current_user
from app.search_discovery import SearchEntityType
from app.social_ranking import RecommendationResponse, ReputationRecord, ReputationResponse, SocialRankingRepository


router = APIRouter(tags=["social-ranking"])


def get_ranking_repository() -> SocialRankingRepository:
    return SocialRankingRepository(get_settings().database_path)


@router.get("/api/social/recommendations", response_model=RecommendationResponse)
async def social_recommendations(
    q: str = "",
    community: str | None = None,
    material: str | None = None,
    component: str | None = None,
    entity_type: SearchEntityType | None = None,
    page_size: int = 12,
    current: CurrentUser | None = Depends(optional_current_user),
    repository: SocialRankingRepository = Depends(get_ranking_repository),
) -> RecommendationResponse:
    return repository.recommendations(
        query=q,
        community=community,
        material=material,
        component=component,
        entity_type=entity_type,
        page_size=page_size,
        viewer_user_id=current.user.id if current else None,
    )


@router.get("/api/social/reputation", response_model=ReputationResponse)
async def social_reputation_leaderboard(
    limit: int = 20,
    repository: SocialRankingRepository = Depends(get_ranking_repository),
) -> ReputationResponse:
    return repository.leaderboard(limit=limit)


@router.get("/api/social/profiles/{slug}/reputation", response_model=ReputationRecord)
async def social_profile_reputation(
    slug: str,
    repository: SocialRankingRepository = Depends(get_ranking_repository),
) -> ReputationRecord:
    try:
        return repository.profile_reputation(slug)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
