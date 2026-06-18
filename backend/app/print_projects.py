from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel

from app.database import connect_database

ProjectVisibility = Literal["private", "unlisted", "public"]
ProjectLifecycleStatus = Literal["draft", "active", "archived"]
ProjectPublicationStatus = Literal["draft", "in_review", "approved", "rejected", "archived"]
ProjectCommercialClass = Literal["free", "curated", "premium", "sponsored"]
ProjectFileKind = Literal["stl", "3mf", "zip", "image", "documentation", "link", "gcode", "artifact"]
ProjectFileRole = Literal["primary", "printable", "optional_part", "documentation", "preview", "external_reference", "artifact"]
ProjectFileValidationStatus = Literal["metadata_only", "quarantined", "validated", "rejected", "analysis_failed"]


class PrintProjectContract(BaseModel):
    root_entity: str
    relations: list[str]
    visibility_values: list[str]
    publication_values: list[str]
    commercial_class_values: list[str]
    file_kinds: list[str]
    file_roles: list[str]
    immutable_snapshot_required_for: list[str]
    community_ownership_rule: str
    external_link_rule: str
    public_privacy_rule: str
    legacy_surfaces: list[str]


class PrintProjectFile(BaseModel):
    id: int
    file_kind: ProjectFileKind
    file_role: ProjectFileRole
    file_name: str
    external_url: str | None
    size_bytes: int | None
    sha256: str | None
    validation_status: ProjectFileValidationStatus
    can_slice: bool


class PrintProjectSummary(BaseModel):
    id: int
    slug: str
    title: str
    description: str
    visibility: ProjectVisibility
    lifecycle_status: ProjectLifecycleStatus
    publication_status: ProjectPublicationStatus
    commercial_class: ProjectCommercialClass
    license: str
    original_author_name: str
    source_url: str | None
    primary_file: PrintProjectFile | None
    file_count: int
    printable_file_count: int
    community_shares: list[str]
    tags: list[str]
    hosted_in_printora: bool
    external_reference_only: bool
    can_slice: bool
    created_at: str
    updated_at: str


class PrintProjectsRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def contract(self) -> PrintProjectContract:
        return PrintProjectContract(
            root_entity="Projeto de impressão",
            relations=[
                "Arquivo do projeto",
                "Versão/snapshot do projeto",
                "Compartilhamento em comunidade",
                "Publicação",
                "Job de fatiamento",
                "Entrega/G-code",
                "Histórico de impressão",
            ],
            visibility_values=["private", "unlisted", "public"],
            publication_values=["draft", "in_review", "approved", "rejected", "archived"],
            commercial_class_values=["free", "curated", "premium", "sponsored"],
            file_kinds=["stl", "3mf", "zip", "image", "documentation", "link", "gcode", "artifact"],
            file_roles=["primary", "printable", "optional_part", "documentation", "preview", "external_reference", "artifact"],
            immutable_snapshot_required_for=["slicing_job", "gcode_delivery", "print_history"],
            community_ownership_rule="Comunidade compartilha e descobre projeto em relação N:N; não é dona do projeto.",
            external_link_rule="Link externo sem arquivo hospedado, importado e validado não pode ser fatiado nem enviado.",
            public_privacy_rule="Payload público não expõe impressora privada, agente, Moonraker, token, IP, path, organização ou permissão.",
            legacy_surfaces=["Social > Comunidades > Arquivos", "Administração > Pipeline de fatiamento", "/api/social/library*"],
        )

    def explore(self, query: str = "", limit: int = 24) -> list[PrintProjectSummary]:
        safe_limit = min(max(limit, 1), 50)
        pattern = f"%{query.strip()}%"
        params: tuple[Any, ...]
        where = "WHERE p.visibility = 'public' AND p.lifecycle_status != 'archived'"
        if query.strip():
            where += " AND (p.title LIKE ? OR p.description LIKE ? OR p.tags_json LIKE ?)"
            params = (pattern, pattern, pattern, safe_limit)
        else:
            params = (safe_limit,)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                PROJECT_SQL
                + f"""
                {where}
                GROUP BY p.id
                ORDER BY p.updated_at DESC, p.id DESC
                LIMIT ?
                """,
                params,
            ).fetchall()
        return [_project_from_row(row) for row in rows]


PROJECT_SQL = """
SELECT
    p.*,
    pf.id AS primary_file_id_resolved,
    pf.file_kind AS primary_file_kind,
    pf.file_role AS primary_file_role,
    pf.file_name AS primary_file_name,
    pf.external_url AS primary_file_external_url,
    pf.size_bytes AS primary_file_size_bytes,
    pf.sha256 AS primary_file_sha256,
    pf.validation_status AS primary_file_validation_status,
    pf.can_slice AS primary_file_can_slice,
    COUNT(DISTINCT f.id) AS file_count,
    SUM(CASE WHEN f.file_role IN ('primary', 'printable', 'optional_part') THEN 1 ELSE 0 END) AS printable_file_count,
    SUM(CASE WHEN f.can_slice = 1 THEN 1 ELSE 0 END) AS slicable_file_count,
    GROUP_CONCAT(DISTINCT c.name) AS community_names
FROM print_projects p
LEFT JOIN print_project_files pf ON pf.id = p.primary_file_id
LEFT JOIN print_project_files f ON f.project_id = p.id
LEFT JOIN print_project_community_shares pcs ON pcs.project_id = p.id AND pcs.status = 'active'
LEFT JOIN social_communities c ON c.id = pcs.community_id
"""


def _project_from_row(row) -> PrintProjectSummary:
    primary_file = None
    if row["primary_file_id_resolved"] is not None:
        primary_file = PrintProjectFile(
            id=int(row["primary_file_id_resolved"]),
            file_kind=row["primary_file_kind"],
            file_role=row["primary_file_role"],
            file_name=str(row["primary_file_name"]),
            external_url=row["primary_file_external_url"],
            size_bytes=row["primary_file_size_bytes"],
            sha256=row["primary_file_sha256"],
            validation_status=row["primary_file_validation_status"],
            can_slice=bool(row["primary_file_can_slice"]),
        )
    file_count = int(row["file_count"] or 0)
    slicable_file_count = int(row["slicable_file_count"] or 0)
    return PrintProjectSummary(
        id=int(row["id"]),
        slug=str(row["slug"]),
        title=str(row["title"]),
        description=str(row["description"] or ""),
        visibility=row["visibility"],
        lifecycle_status=row["lifecycle_status"],
        publication_status=row["publication_status"],
        commercial_class=row["commercial_class"],
        license=str(row["license"] or ""),
        original_author_name=str(row["original_author_name"] or ""),
        source_url=row["source_url"],
        primary_file=primary_file,
        file_count=file_count,
        printable_file_count=int(row["printable_file_count"] or 0),
        community_shares=[name for name in str(row["community_names"] or "").split(",") if name],
        tags=_loads_list(row["tags_json"]),
        hosted_in_printora=file_count > 0 and not _is_external_only(primary_file, file_count),
        external_reference_only=_is_external_only(primary_file, file_count),
        can_slice=slicable_file_count > 0,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _loads_list(value: str | None) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()]


def _is_external_only(primary_file: PrintProjectFile | None, file_count: int) -> bool:
    return file_count == 1 and primary_file is not None and primary_file.file_role == "external_reference"
