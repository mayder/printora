from fastapi import APIRouter, Depends

from app.config import get_settings
from app.print_projects import PrintProjectContract, PrintProjectSummary, PrintProjectsRepository

router = APIRouter(prefix="/api/print-projects", tags=["print-projects"])


def get_print_projects_repository() -> PrintProjectsRepository:
    return PrintProjectsRepository(get_settings().database_path)


@router.get("/contract", response_model=PrintProjectContract)
async def print_projects_contract(
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> PrintProjectContract:
    return repository.contract()


@router.get("", response_model=list[PrintProjectSummary])
async def explore_print_projects(
    q: str = "",
    limit: int = 24,
    repository: PrintProjectsRepository = Depends(get_print_projects_repository),
) -> list[PrintProjectSummary]:
    return repository.explore(q, limit)
