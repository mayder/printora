from __future__ import annotations

import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.database import connect_database
from app.object_storage import build_object_storage


MAX_EXPORT_BYTES = 500 * 1024 * 1024


@dataclass(frozen=True)
class PhotoCaptureExport:
    path: Path
    file_name: str


class PhotoCaptureExportRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.storage = build_object_storage(database_path)

    def build(self, owner_user_id: int, session_id: int) -> PhotoCaptureExport:
        with connect_database(self.database_path) as connection:
            session = connection.execute(
                "SELECT * FROM photo_capture_sessions WHERE id = ? AND owner_user_id = ?",
                (session_id, owner_user_id),
            ).fetchone()
            if session is None:
                raise PermissionError("captura não encontrada")
            photos = connection.execute(
                "SELECT * FROM photo_capture_photos WHERE session_id = ? AND is_current = 1 ORDER BY capture_index, id",
                (session_id,),
            ).fetchall()
        if sum(int(photo["size_bytes"]) for photo in photos) > MAX_EXPORT_BYTES:
            raise ValueError("a captura excede 500 MB; reduza o conjunto antes de exportar")
        temporary = tempfile.NamedTemporaryFile(prefix="printora-capture-", suffix=".zip", delete=False)
        temporary.close()
        path = Path(temporary.name)
        try:
            with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
                manifest = {
                    "schema": "printora.photo-capture/v1",
                    "session_id": int(session["id"]),
                    "project_id": int(session["project_id"]),
                    "status": session["status"],
                    "scale": {
                        "method": session["scale_method"],
                        "value_mm": session["scale_value_mm"],
                        "uncertainty_mm": session["scale_uncertainty_mm"],
                    },
                    "photos": [
                        {
                            "capture_index": int(photo["capture_index"]),
                            "height_band": photo["height_band"],
                            "file_name": photo["file_name"],
                            "sha256": photo["sha256"],
                            "width": int(photo["width"]),
                            "height": int(photo["height"]),
                            "quality_status": photo["quality_status"],
                        }
                        for photo in photos
                    ],
                }
                archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
                checksums: list[str] = []
                for photo in photos:
                    suffix = Path(str(photo["file_name"])).suffix.lower()
                    name = f"{int(photo['capture_index']):03d}-{photo['height_band']}{suffix}"
                    reader = self.storage.open_promoted(str(photo["storage_key"]))
                    try:
                        with archive.open(f"photos/{name}", "w") as target:
                            while chunk := reader.body.read(64 * 1024):
                                target.write(chunk)
                    finally:
                        reader.body.close()
                    checksums.append(f"{photo['sha256']}  photos/{name}")
                archive.writestr("SHA256SUMS.txt", "\n".join(checksums) + ("\n" if checksums else ""))
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return PhotoCaptureExport(path=path, file_name=f"captura-{session_id}.zip")
