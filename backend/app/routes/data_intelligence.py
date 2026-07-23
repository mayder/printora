from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config import get_settings
from app.modules.administration.intelligence import IntelligenceRepository
from app.modules.administration.intelligence_contracts import (
    GeometrySearchRequest,
    ModelControlRequest,
    ModerationAppealRequest,
    ModerationAppealReviewRequest,
    ModerationReviewRequest,
    RecommendationRequest,
    ReplayRequest,
    SanitizedEventCreate,
    SubjectAnonymizationRequest,
)
from app.modules.identity.contracts import CurrentUser
from app.platform_access import is_platform_admin
from app.routes.auth import require_current_user


router = APIRouter(prefix="/api/admin/data-intelligence", tags=["data-intelligence"])


def require_intelligence_admin(
    current: CurrentUser = Depends(require_current_user),
) -> CurrentUser:
    if not is_platform_admin(current.user.email):
        raise HTTPException(status_code=403, detail="inteligência de dados restrita ao administrador")
    return current


def repository() -> IntelligenceRepository:
    settings = get_settings()
    return IntelligenceRepository(settings.database_path)


@router.get("/dashboard")
async def dashboard(_current: CurrentUser = Depends(require_intelligence_admin)) -> dict:
    return repository().dashboard()


@router.post("/events", status_code=202)
async def ingest_event(
    payload: SanitizedEventCreate,
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    try:
        return repository().ingest(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/process")
async def process_pending(
    limit: int = Query(default=100, ge=1, le=500),
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    return repository().process_pending(limit)


@router.post("/replay")
async def replay(
    payload: ReplayRequest,
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    try:
        return repository().replay(payload.replay_key, payload.event_type)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/subjects/anonymize")
async def anonymize_subject(
    payload: SubjectAnonymizationRequest,
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    return repository().anonymize_subject(payload.subject_key, payload.purpose)


@router.get("/moderation")
async def moderation_queue(
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    items = repository().moderation_queue()
    return {"count": len(items), "items": items}


@router.post("/moderation/{case_key}/review")
async def review_case(
    case_key: str,
    payload: ModerationReviewRequest,
    current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    try:
        return repository().review_case(
            case_key, payload.decision, payload.rationale, current.user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/moderation/{case_key}/appeals")
async def create_appeal(
    case_key: str,
    payload: ModerationAppealRequest,
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    try:
        return repository().create_appeal(
            payload.appeal_key, case_key, payload.appellant_key, payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/appeals/{appeal_key}/review")
async def review_appeal(
    appeal_key: str,
    payload: ModerationAppealReviewRequest,
    current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    try:
        return repository().review_appeal(
            appeal_key, payload.decision, payload.resolution, current.user.email,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/models/{model_key}/{version}/control")
async def control_model(
    model_key: str,
    version: str,
    payload: ModelControlRequest,
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    try:
        return repository().control_model(
            model_key,
            version,
            enabled=payload.enabled,
            kill_switch=payload.kill_switch,
            canary_percent=payload.canary_percent,
            drift_score=payload.drift_score,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/recommendations")
async def recommend(
    payload: RecommendationRequest,
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    return repository().recommend(payload.decision_key, payload.candidates, payload.subject_key)


@router.post("/geometry/search")
async def geometry_search(
    payload: GeometrySearchRequest,
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    return repository().geometry_search(
        payload.decision_key, payload.entity_type, payload.features, payload.limit,
    )


@router.get("/retention/preview")
async def retention_preview(
    _current: CurrentUser = Depends(require_intelligence_admin),
) -> dict:
    return repository().retention_preview()
