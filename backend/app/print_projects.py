from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

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


class PrintProjectVersion(BaseModel):
    id: int
    version_label: str
    changelog: str
    project_snapshot: dict[str, Any]
    files_snapshot: list[dict[str, Any]]
    created_at: str


class PrintProjectDetail(PrintProjectSummary):
    files: list[PrintProjectFile]
    versions: list[PrintProjectVersion]
    saved_by_viewer: bool = False
    immutable_snapshot_ready: bool


class PrintProjectSaveRequest(BaseModel):
    save_kind: Literal["reference", "fork", "copy"] = "reference"
    confirmed_copy: bool = False


class PrintProjectCommunityShare(BaseModel):
    community_slug: str
    community_name: str
    shared_at: str


class PrintProjectShareRequest(BaseModel):
    community_slug: str = Field(min_length=1, max_length=180)


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

    def explore(
        self,
        query: str = "",
        file_kind: str = "",
        license: str = "",
        origin: str = "",
        community: str = "",
        limit: int = 24,
    ) -> list[PrintProjectSummary]:
        safe_limit = min(max(limit, 1), 50)
        params: list[Any] = []
        where = "WHERE p.visibility = 'public' AND p.lifecycle_status != 'archived'"
        if query.strip():
            pattern = f"%{query.strip()}%"
            where += " AND (p.title LIKE ? OR p.description LIKE ? OR p.tags_json LIKE ?)"
            params.extend([pattern, pattern, pattern])
        if file_kind.strip():
            where += " AND EXISTS (SELECT 1 FROM print_project_files fk WHERE fk.project_id = p.id AND fk.file_kind = ?)"
            params.append(file_kind.strip())
        if license.strip():
            where += " AND p.license = ?"
            params.append(license.strip())
        if origin == "hosted":
            where += " AND EXISTS (SELECT 1 FROM print_project_files hf WHERE hf.project_id = p.id AND hf.file_role != 'external_reference')"
        elif origin == "external":
            where += " AND NOT EXISTS (SELECT 1 FROM print_project_files hf WHERE hf.project_id = p.id AND hf.file_role != 'external_reference')"
        if community.strip():
            where += """
                AND EXISTS (
                    SELECT 1
                    FROM print_project_community_shares pcs_filter
                    JOIN social_communities c_filter ON c_filter.id = pcs_filter.community_id
                    WHERE pcs_filter.project_id = p.id
                      AND pcs_filter.status = 'active'
                      AND c_filter.slug = ?
                )
            """
            params.append(community.strip())
        params.append(safe_limit)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                PROJECT_SQL
                + f"""
                {where}
                GROUP BY p.id
                ORDER BY p.updated_at DESC, p.id DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [_project_from_row(row) for row in rows]

    def community_projects(self, community_slug: str) -> list[PrintProjectSummary]:
        return self.explore(community=community_slug, limit=50)

    def detail(self, slug: str, viewer_user_id: int | None = None) -> PrintProjectDetail | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                PROJECT_SQL
                + """
                WHERE p.slug = ?
                  AND p.lifecycle_status != 'archived'
                  AND (p.visibility IN ('public', 'unlisted') OR p.owner_user_id = ?)
                GROUP BY p.id
                """,
                (slug, viewer_user_id or -1),
            ).fetchone()
            if row is None:
                return None
            files = [
                _file_from_row(file_row)
                for file_row in connection.execute(
                    """
                    SELECT *
                    FROM print_project_files
                    WHERE project_id = ?
                    ORDER BY
                        CASE file_role
                            WHEN 'primary' THEN 1
                            WHEN 'printable' THEN 2
                            WHEN 'optional_part' THEN 3
                            WHEN 'preview' THEN 4
                            WHEN 'documentation' THEN 5
                            WHEN 'external_reference' THEN 6
                            ELSE 7
                        END,
                        id
                    """,
                    (row["id"],),
                ).fetchall()
            ]
            versions = [
                _version_from_row(version_row)
                for version_row in connection.execute(
                    """
                    SELECT *
                    FROM print_project_versions
                    WHERE project_id = ?
                    ORDER BY created_at DESC, id DESC
                    """,
                    (row["id"],),
                ).fetchall()
            ]
            saved_by_viewer = False
            if viewer_user_id is not None:
                saved_by_viewer = bool(
                    connection.execute(
                        """
                        SELECT 1
                        FROM print_project_saves
                        WHERE owner_user_id = ? AND project_id = ? AND status = 'active'
                        LIMIT 1
                        """,
                        (viewer_user_id, row["id"]),
                    ).fetchone()
                )
        summary = _project_from_row(row)
        return PrintProjectDetail(
            **summary.model_dump(),
            files=files,
            versions=versions,
            saved_by_viewer=saved_by_viewer,
            immutable_snapshot_ready=bool(versions),
        )

    def save_project(self, actor_user_id: int, project_id: int, payload: PrintProjectSaveRequest) -> PrintProjectDetail:
        if payload.save_kind == "copy" and not payload.confirmed_copy:
            raise ValueError("cópia de arquivo exige confirmação explícita")
        if payload.save_kind in {"fork", "copy"}:
            raise ValueError("fork e cópia serão tratados em Meus projetos; use salvar referência neste fluxo")
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT slug
                FROM print_projects
                WHERE id = ? AND lifecycle_status != 'archived' AND visibility IN ('public', 'unlisted')
                """,
                (project_id,),
            ).fetchone()
            if row is None:
                raise ValueError("projeto não encontrado")
            connection.execute(
                """
                INSERT INTO print_project_saves (owner_user_id, project_id, save_kind)
                VALUES (?, ?, ?)
                ON CONFLICT(owner_user_id, project_id, save_kind) DO UPDATE SET
                    status = 'active',
                    updated_at = CURRENT_TIMESTAMP
                """,
                (actor_user_id, project_id, payload.save_kind),
            )
            slug = str(row["slug"])
        detail = self.detail(slug, actor_user_id)
        if detail is None:
            raise ValueError("projeto não encontrado")
        return detail

    def share_with_community(self, actor_user_id: int, project_id: int, payload: PrintProjectShareRequest) -> PrintProjectDetail:
        with connect_database(self.database_path) as connection:
            project = connection.execute(
                """
                SELECT id, slug, owner_user_id
                FROM print_projects
                WHERE id = ? AND lifecycle_status != 'archived'
                """,
                (project_id,),
            ).fetchone()
            if project is None:
                raise ValueError("projeto não encontrado")
            if project["owner_user_id"] is not None and int(project["owner_user_id"]) != actor_user_id:
                raise PermissionError("somente o dono pode compartilhar o projeto")
            community = connection.execute(
                "SELECT id FROM social_communities WHERE slug = ? AND status = 'active'",
                (payload.community_slug,),
            ).fetchone()
            if community is None:
                raise ValueError("comunidade não encontrada")
            connection.execute(
                """
                INSERT INTO print_project_community_shares (project_id, community_id, shared_by_user_id)
                VALUES (?, ?, ?)
                ON CONFLICT(project_id, community_id) DO UPDATE SET
                    status = 'active',
                    shared_by_user_id = excluded.shared_by_user_id,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (project_id, community["id"], actor_user_id),
            )
            slug = str(project["slug"])
        detail = self.detail(slug, actor_user_id)
        if detail is None:
            raise ValueError("projeto não encontrado")
        return detail


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


def _file_from_row(row) -> PrintProjectFile:
    return PrintProjectFile(
        id=int(row["id"]),
        file_kind=row["file_kind"],
        file_role=row["file_role"],
        file_name=str(row["file_name"]),
        external_url=row["external_url"],
        size_bytes=row["size_bytes"],
        sha256=row["sha256"],
        validation_status=row["validation_status"],
        can_slice=bool(row["can_slice"]),
    )


def _version_from_row(row) -> PrintProjectVersion:
    return PrintProjectVersion(
        id=int(row["id"]),
        version_label=str(row["version_label"]),
        changelog=str(row["changelog"] or ""),
        project_snapshot=_loads_dict(row["project_snapshot_json"]),
        files_snapshot=_loads_dict_list(row["files_snapshot_json"]),
        created_at=str(row["created_at"]),
    )


def _loads_dict(value: str | None) -> dict[str, Any]:
    try:
        parsed = json.loads(value or "{}")
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _loads_dict_list(value: str | None) -> list[dict[str, Any]]:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [item for item in parsed if isinstance(item, dict)]
