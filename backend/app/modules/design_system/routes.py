from __future__ import annotations

from fastapi import APIRouter, Depends

from app.modules.design_system.catalog import build_catalog
from app.modules.design_system.contracts import DesignSystemCatalogContract
from app.modules.identity.contracts import CurrentUser
from app.routes.auth import require_current_user


router = APIRouter(prefix="/api/design-system/v1", tags=["design-system"])


@router.get("/capabilities", response_model=DesignSystemCatalogContract)
async def list_capabilities(
    _current: CurrentUser = Depends(require_current_user),
) -> DesignSystemCatalogContract:
    return build_catalog()
