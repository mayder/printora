from fastapi import APIRouter, Depends

from app.config import get_settings
from app.slicing import SlicingDryRunResult, SlicingEngineBridge, SlicingEngineInfo, SlicingRepository, SlicingRequest, SlicerEngine

router = APIRouter(prefix="/api/slicing", tags=["slicing"])


def get_slicing_bridge() -> SlicingEngineBridge:
    return SlicingEngineBridge(get_settings())


def get_slicing_repository() -> SlicingRepository:
    return SlicingRepository(get_settings().database_path)


@router.get("/engine", response_model=SlicingEngineInfo)
async def get_slicing_engine(
    engine: SlicerEngine | None = None,
    bridge: SlicingEngineBridge = Depends(get_slicing_bridge),
    repository: SlicingRepository = Depends(get_slicing_repository),
) -> SlicingEngineInfo:
    info = bridge.detect(engine)
    repository.record_engine_check(info)
    return info


@router.post("/dry-run", response_model=SlicingDryRunResult)
async def create_slicing_dry_run(
    payload: SlicingRequest,
    bridge: SlicingEngineBridge = Depends(get_slicing_bridge),
    repository: SlicingRepository = Depends(get_slicing_repository),
) -> SlicingDryRunResult:
    result = bridge.dry_run(payload)
    repository.record_dry_run(result)
    return result
