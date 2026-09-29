from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from app.database import connect_database
from app.object_storage import build_object_storage


MAX_BUNDLE_BYTES = 250 * 1024 * 1024


@dataclass(frozen=True)
class ProjectBundle:
    path: Path
    file_name: str


class ProjectAssetExportRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.storage = build_object_storage(database_path)

    def build_bundle(self, project_id: int, actor_user_id: int) -> ProjectBundle:
        with connect_database(self.database_path) as connection:
            project = connection.execute(
                """
                SELECT id, slug, owner_user_id, visibility, lifecycle_status, publication_status, current_version_id
                FROM print_projects
                WHERE id = ? AND lifecycle_status != 'archived'
                """,
                (project_id,),
            ).fetchone()
            if project is None:
                raise ValueError("projeto não encontrado")
            owns = project["owner_user_id"] is not None and int(project["owner_user_id"]) == actor_user_id
            public = project["visibility"] == "public" and project["publication_status"] == "approved"
            if not (owns or public):
                raise PermissionError("download do projeto não autorizado")
            version = connection.execute(
                "SELECT manifest_json, manifest_sha256 FROM print_project_versions WHERE id = ? AND project_id = ?",
                (project["current_version_id"], project_id),
            ).fetchone()
            if version is None or not version["manifest_sha256"]:
                raise ValueError("o projeto ainda não possui uma versão verificável")
            files = connection.execute(
                """
                SELECT pf.id, pf.file_name, pf.sha256, pf.size_bytes, object.object_key
                FROM print_project_files pf
                JOIN cloud_object_references reference
                  ON reference.reference_type = 'print_project_file' AND reference.reference_id = pf.id
                JOIN cloud_objects object ON object.id = reference.object_id AND object.state = 'promoted'
                WHERE pf.project_id = ? AND pf.validation_status = 'validated'
                ORDER BY pf.display_order, pf.id
                """,
                (project_id,),
            ).fetchall()
        total_bytes = sum(int(row["size_bytes"] or 0) for row in files)
        if total_bytes > MAX_BUNDLE_BYTES:
            raise ValueError("o pacote excede 250 MB; baixe os arquivos individualmente")
        temporary = tempfile.NamedTemporaryFile(prefix="printora-project-", suffix=".zip", delete=False)
        temporary.close()
        path = Path(temporary.name)
        try:
            with ZipFile(path, "w", compression=ZIP_DEFLATED, compresslevel=6) as archive:
                manifest_bytes = str(version["manifest_json"]).encode("utf-8")
                archive.writestr("manifest.json", manifest_bytes)
                checksums = [f"{version['manifest_sha256']}  manifest.json"]
                used_names: set[str] = set()
                for row in files:
                    name = _unique_name(_safe_name(str(row["file_name"])), used_names)
                    reader = self.storage.open_promoted(str(row["object_key"]))
                    try:
                        with archive.open(f"files/{name}", "w") as target:
                            while chunk := reader.body.read(64 * 1024):
                                target.write(chunk)
                    finally:
                        reader.body.close()
                    checksums.append(f"{row['sha256']}  files/{name}")
                archive.writestr("SHA256SUMS.txt", "\n".join(checksums) + "\n")
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return ProjectBundle(path=path, file_name=f"{_safe_name(str(project['slug']))}.zip")


def _safe_name(value: str) -> str:
    cleaned = "".join(character if character.isalnum() or character in "._- " else "_" for character in value)
    return cleaned.strip(" .")[:180] or "arquivo"


def _unique_name(name: str, used: set[str]) -> str:
    candidate = name
    stem, suffix = Path(name).stem, Path(name).suffix
    index = 2
    while candidate.lower() in used:
        candidate = f"{stem}-{index}{suffix}"
        index += 1
    used.add(candidate.lower())
    return candidate
