from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.modules.design_system.catalog import build_catalog
from app.modules.design_system.contracts import DesignSystemCatalogContract
from app.modules.identity.contracts import CurrentUser
from app.platform_access import is_platform_admin
from app.routes.auth import require_current_user


router = APIRouter(prefix="/api/design-system/v1", tags=["design-system"])


def require_design_system_admin(
    current: CurrentUser = Depends(require_current_user),
) -> CurrentUser:
    if not is_platform_admin(current.user.email):
        raise HTTPException(status_code=403, detail="design system restrito ao administrador")
    return current


@router.get("/capabilities", response_model=DesignSystemCatalogContract)
async def list_capabilities(
    _current: CurrentUser = Depends(require_design_system_admin),
) -> DesignSystemCatalogContract:
    return build_catalog()
