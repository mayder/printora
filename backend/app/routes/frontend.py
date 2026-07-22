from __future__ import annotations

from app.routes.support import *

router = APIRouter()

INDEX_HEADERS = {"Cache-Control": "no-store"}


@router.get("/")
async def frontend_index() -> FileResponse:
    index_path = get_settings().frontend_dist_dir / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="frontend build not found")
    return FileResponse(index_path, headers=INDEX_HEADERS)




@router.get("/favicon.png")
async def frontend_favicon() -> FileResponse:
    favicon_path = get_settings().frontend_dist_dir / "favicon.png"
    if not favicon_path.is_file():
        raise HTTPException(status_code=404, detail="favicon not found")
    return FileResponse(favicon_path)




@router.get("/apple-touch-icon.png")
async def frontend_apple_touch_icon() -> FileResponse:
    icon_path = get_settings().frontend_dist_dir / "apple-touch-icon.png"
    if not icon_path.is_file():
        raise HTTPException(status_code=404, detail="apple touch icon not found")
    return FileResponse(icon_path)


@router.api_route(
    "/api/{api_path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    include_in_schema=False,
)
async def api_fallback(api_path: str) -> None:
    raise HTTPException(status_code=404, detail="api route not found")




@router.get("/{frontend_path:path}")
async def frontend_fallback(frontend_path: str) -> FileResponse:
    if frontend_path == "health" or frontend_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="not found")
    index_path = get_settings().frontend_dist_dir / "index.html"
    if not index_path.is_file():
        raise HTTPException(status_code=404, detail="frontend build not found")
    return FileResponse(index_path, headers=INDEX_HEADERS)
