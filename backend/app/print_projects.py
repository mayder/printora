from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.database import connect_database
from app.social_catalog import clean_library_file_name, validate_public_url, _validate_library_upload
from app.social_storage import DEFAULT_USER_QUOTA_BYTES, SocialStorageRepository

ProjectVisibility = Literal["private", "unlisted", "public"]
ProjectLifecycleStatus = Literal["draft", "active", "archived"]
ProjectPublicationStatus = Literal["draft", "in_review", "approved", "rejected", "archived"]
ProjectCommercialClass = Literal["free", "curated", "premium", "sponsored"]
ProjectFileKind = Literal["stl", "3mf", "zip", "image", "documentation", "link", "gcode", "artifact"]
ProjectFileRole = Literal["primary", "printable", "optional_part", "documentation", "preview", "external_reference", "artifact"]
ProjectFileValidationStatus = Literal["metadata_only", "quarantined", "validated", "rejected", "analysis_failed"]
ProjectFileSliceStatus = Literal["eligible", "blocked", "external_no_local", "pending", "failure"]


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
    uploaded_size_bytes: int | None = None
    rejection_reason: str | None = None
    slice_status: ProjectFileSliceStatus = "blocked"


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


class PrintProjectCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(default="", max_length=1200)
    visibility: ProjectVisibility = "private"
    license: str = Field(default="", max_length=80)
    original_author_name: str = Field(default="", max_length=160)
    attribution_text: str = Field(default="", max_length=500)
    source_url: str | None = Field(default=None, max_length=500)
    tags: list[str] = Field(default_factory=list)
    material: str = Field(default="", max_length=120)
    component: str = Field(default="", max_length=120)

    @field_validator("source_url")
    @classmethod
    def clean_source_url(cls, value: str | None) -> str | None:
        return validate_public_url(value, field_name="source_url", allowed_hosts=None)


class PrintProjectUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=180)
    description: str | None = Field(default=None, max_length=1200)
    visibility: ProjectVisibility | None = None
    license: str | None = Field(default=None, max_length=80)
    original_author_name: str | None = Field(default=None, max_length=160)
    attribution_text: str | None = Field(default=None, max_length=500)
    source_url: str | None = Field(default=None, max_length=500)
    tags: list[str] | None = None
    material: str | None = Field(default=None, max_length=120)
    component: str | None = Field(default=None, max_length=120)

    @field_validator("source_url")
    @classmethod
    def clean_source_url(cls, value: str | None) -> str | None:
        return validate_public_url(value, field_name="source_url", allowed_hosts=None)


class PrintProjectExternalLinkRequest(BaseModel):
    url: str = Field(min_length=8, max_length=500)
    label: str = Field(default="Referência externa", max_length=180)
    attribution_text: str = Field(default="", max_length=500)

    @field_validator("url")
    @classmethod
    def clean_url(cls, value: str) -> str:
        cleaned = validate_public_url(value, field_name="url", allowed_hosts=None)
        if cleaned is None:
            raise ValueError("url externa obrigatória")
        return cleaned


class PrintProjectStorageReport(BaseModel):
    quota_bytes: int
    used_bytes: int
    remaining_bytes: int
    file_count: int
    hosted_project_count: int
    external_reference_count: int


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

    def my_projects(self, actor_user_id: int) -> list[PrintProjectSummary]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                PROJECT_SQL
                + """
                WHERE p.owner_user_id = ?
                   OR EXISTS (
                        SELECT 1
                        FROM print_project_saves ps
                        WHERE ps.project_id = p.id
                          AND ps.owner_user_id = ?
                          AND ps.status = 'active'
                   )
                GROUP BY p.id
                ORDER BY p.updated_at DESC, p.id DESC
                """,
                (actor_user_id, actor_user_id),
            ).fetchall()
        return [_project_from_row(row) for row in rows]

    def storage_report(self, actor_user_id: int) -> PrintProjectStorageReport:
        with connect_database(self.database_path) as connection:
            quota = _quota_for_user(connection, actor_user_id)
            row = connection.execute(
                """
                SELECT
                    COALESCE(SUM(COALESCE(f.uploaded_size_bytes, f.size_bytes, 0)), 0) AS used_bytes,
                    COUNT(f.id) AS file_count,
                    COUNT(DISTINCT CASE WHEN f.file_role != 'external_reference' THEN p.id END) AS hosted_project_count,
                    COALESCE(SUM(CASE WHEN f.file_role = 'external_reference' THEN 1 ELSE 0 END), 0) AS external_reference_count
                FROM print_projects p
                LEFT JOIN print_project_files f ON f.project_id = p.id
                WHERE p.owner_user_id = ?
                  AND p.lifecycle_status != 'archived'
                """,
                (actor_user_id,),
            ).fetchone()
        used = int(row["used_bytes"] or 0)
        return PrintProjectStorageReport(
            quota_bytes=quota,
            used_bytes=used,
            remaining_bytes=max(quota - used, 0),
            file_count=int(row["file_count"] or 0),
            hosted_project_count=int(row["hosted_project_count"] or 0),
            external_reference_count=int(row["external_reference_count"] or 0),
        )

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

    def create_project(self, actor_user_id: int, payload: PrintProjectCreateRequest) -> PrintProjectDetail:
        metadata = _project_metadata(payload.material, payload.component)
        with connect_database(self.database_path) as connection:
            slug = _unique_slug(connection, payload.title)
            cursor = connection.execute(
                """
                INSERT INTO print_projects (
                    owner_user_id, slug, title, description, visibility, lifecycle_status,
                    publication_status, commercial_class, license, original_author_name,
                    attribution_text, source_url, tags_json, metadata_json
                )
                VALUES (?, ?, ?, ?, ?, 'active', 'draft', 'free', ?, ?, ?, ?, ?, ?)
                """,
                (
                    actor_user_id,
                    slug,
                    payload.title.strip(),
                    payload.description.strip(),
                    payload.visibility,
                    payload.license.strip(),
                    payload.original_author_name.strip(),
                    payload.attribution_text.strip(),
                    payload.source_url,
                    _tags_json(payload.tags),
                    json.dumps(metadata, ensure_ascii=False),
                ),
            )
            project_id = int(cursor.lastrowid)
            self._create_snapshot(connection, project_id, actor_user_id, "v1", "Projeto criado")
        detail = self.detail(slug, actor_user_id)
        if detail is None:
            raise ValueError("projeto não encontrado")
        return detail

    def update_project(self, actor_user_id: int, project_id: int, payload: PrintProjectUpdateRequest) -> PrintProjectDetail:
        with connect_database(self.database_path) as connection:
            project = self._owned_project(connection, actor_user_id, project_id)
            metadata = _loads_dict(project["metadata_json"])
            updates: list[str] = []
            params: list[Any] = []
            for field_name in ("title", "description", "visibility", "license", "original_author_name", "attribution_text", "source_url"):
                value = getattr(payload, field_name)
                if value is not None:
                    updates.append(f"{field_name} = ?")
                    params.append(value.strip() if isinstance(value, str) else value)
            if payload.tags is not None:
                updates.append("tags_json = ?")
                params.append(_tags_json(payload.tags))
            if payload.material is not None:
                metadata["material"] = payload.material.strip()
            if payload.component is not None:
                metadata["component"] = payload.component.strip()
            if payload.material is not None or payload.component is not None:
                updates.append("metadata_json = ?")
                params.append(json.dumps(metadata, ensure_ascii=False))
            if not updates:
                return self.detail(str(project["slug"]), actor_user_id)  # type: ignore[return-value]
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(project_id)
            connection.execute(f"UPDATE print_projects SET {', '.join(updates)} WHERE id = ?", tuple(params))
            self._create_snapshot(connection, project_id, actor_user_id, "edição", "Metadados atualizados")
            slug = str(project["slug"])
        detail = self.detail(slug, actor_user_id)
        if detail is None:
            raise ValueError("projeto não encontrado")
        return detail

    def archive_project(self, actor_user_id: int, project_id: int) -> None:
        with connect_database(self.database_path) as connection:
            project = self._owned_project(connection, actor_user_id, project_id)
            connection.execute(
                """
                UPDATE print_projects
                SET lifecycle_status = 'archived', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (project_id,),
            )

    def add_external_link(self, actor_user_id: int, project_id: int, payload: PrintProjectExternalLinkRequest) -> PrintProjectDetail:
        with connect_database(self.database_path) as connection:
            project = self._owned_project(connection, actor_user_id, project_id)
            cursor = connection.execute(
                """
                INSERT INTO print_project_files (
                    project_id, file_kind, file_role, file_name, external_url,
                    validation_status, can_slice, rejection_reason
                )
                VALUES (?, 'link', 'external_reference', ?, ?, 'metadata_only', 0, 'referência externa sem arquivo local validado')
                """,
                (project_id, payload.label.strip() or "Referência externa", payload.url),
            )
            if project["primary_file_id"] is None:
                connection.execute("UPDATE print_projects SET primary_file_id = ? WHERE id = ?", (cursor.lastrowid, project_id))
            if payload.attribution_text.strip():
                connection.execute(
                    "UPDATE print_projects SET attribution_text = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (payload.attribution_text.strip(), project_id),
                )
            else:
                connection.execute("UPDATE print_projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))
            self._create_snapshot(connection, project_id, actor_user_id, "link externo", "Referência externa adicionada")
            slug = str(project["slug"])
        detail = self.detail(slug, actor_user_id)
        if detail is None:
            raise ValueError("projeto não encontrado")
        return detail

    def upload_file(self, actor_user_id: int, project_id: int, file_name: str, file_role: ProjectFileRole, body: bytes) -> PrintProjectDetail:
        if file_role == "external_reference":
            raise ValueError("use link externo para referência sem arquivo local")
        clean_name = clean_library_file_name(file_name)
        if len(body) > 25 * 1024 * 1024:
            raise ValueError("arquivo excede limite de 25 MB")
        file_kind = _project_file_kind_from_name(clean_name)
        checksum = hashlib.sha256(body).hexdigest()
        validation_status: ProjectFileValidationStatus = "quarantined"
        rejection_reason = None
        can_slice = file_role in {"primary", "printable", "optional_part"} and file_kind in {"stl", "3mf", "zip"}
        try:
            _validate_library_upload(clean_name, _library_kind_for_project(file_kind), body)
        except ValueError as exc:
            validation_status = "rejected"
            rejection_reason = str(exc)
            can_slice = False
        storage = SocialStorageRepository(self.database_path)
        with connect_database(self.database_path) as connection:
            project = self._owned_project(connection, actor_user_id, project_id)
            storage.ensure_upload_allowed(connection, actor_user_id, len(body))
            stored = storage.storage.write_quarantine(checksum, Path(clean_name).suffix.lower(), body)
            cursor = connection.execute(
                """
                INSERT INTO print_project_files (
                    project_id, file_kind, file_role, file_name, storage_path, size_bytes,
                    sha256, validation_status, can_slice, quarantine_key, uploaded_size_bytes,
                    uploaded_at, rejection_reason, is_primary_preview
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                """,
                (
                    project_id,
                    file_kind,
                    file_role,
                    clean_name,
                    stored.key,
                    len(body),
                    checksum,
                    validation_status,
                    1 if can_slice else 0,
                    stored.key,
                    len(body),
                    rejection_reason,
                    1 if file_role in {"primary", "preview"} else 0,
                ),
            )
            if file_role == "primary" or project["primary_file_id"] is None:
                connection.execute("UPDATE print_projects SET primary_file_id = ? WHERE id = ?", (cursor.lastrowid, project_id))
            connection.execute("UPDATE print_projects SET updated_at = CURRENT_TIMESTAMP WHERE id = ?", (project_id,))
            self._create_snapshot(connection, project_id, actor_user_id, "arquivo", f"Arquivo {clean_name} adicionado")
            slug = str(project["slug"])
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

    def _owned_project(self, connection, actor_user_id: int, project_id: int):
        row = connection.execute(
            """
            SELECT *
            FROM print_projects
            WHERE id = ? AND owner_user_id = ? AND lifecycle_status != 'archived'
            """,
            (project_id, actor_user_id),
        ).fetchone()
        if row is None:
            raise PermissionError("projeto não encontrado ou sem permissão")
        return row

    def _create_snapshot(self, connection, project_id: int, actor_user_id: int, label: str, changelog: str) -> None:
        project = connection.execute("SELECT * FROM print_projects WHERE id = ?", (project_id,)).fetchone()
        files = connection.execute(
            """
            SELECT id, file_kind, file_role, file_name, external_url, size_bytes, sha256,
                   validation_status, can_slice, rejection_reason
            FROM print_project_files
            WHERE project_id = ?
            ORDER BY id
            """,
            (project_id,),
        ).fetchall()
        project_snapshot = {
            "id": project["id"],
            "slug": project["slug"],
            "title": project["title"],
            "description": project["description"],
            "visibility": project["visibility"],
            "publication_status": project["publication_status"],
            "commercial_class": project["commercial_class"],
            "license": project["license"],
            "tags": _loads_list(project["tags_json"]),
            "metadata": _loads_dict(project["metadata_json"]),
        }
        files_snapshot = [dict(file_row) for file_row in files]
        cursor = connection.execute(
            """
            INSERT INTO print_project_versions (
                project_id, version_label, changelog, project_snapshot_json,
                files_snapshot_json, created_by_user_id
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                project_id,
                label,
                changelog,
                json.dumps(project_snapshot, ensure_ascii=False),
                json.dumps(files_snapshot, ensure_ascii=False),
                actor_user_id,
            ),
        )
        connection.execute(
            "UPDATE print_projects SET current_version_id = ? WHERE id = ?",
            (cursor.lastrowid, project_id),
        )


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
    pf.uploaded_size_bytes AS primary_file_uploaded_size_bytes,
    pf.rejection_reason AS primary_file_rejection_reason,
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
            uploaded_size_bytes=row["primary_file_uploaded_size_bytes"],
            rejection_reason=row["primary_file_rejection_reason"],
            slice_status=_slice_status(row["primary_file_role"], row["primary_file_validation_status"], bool(row["primary_file_can_slice"])),
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
        uploaded_size_bytes=row["uploaded_size_bytes"] if "uploaded_size_bytes" in row.keys() else None,
        rejection_reason=row["rejection_reason"] if "rejection_reason" in row.keys() else None,
        slice_status=_slice_status(row["file_role"], row["validation_status"], bool(row["can_slice"])),
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


def _project_file_kind_from_name(file_name: str) -> ProjectFileKind:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".stl":
        return "stl"
    if suffix == ".3mf":
        return "3mf"
    if suffix == ".zip":
        return "zip"
    raise ValueError("projeto aceita STL, 3MF ou ZIP")


def _library_kind_for_project(file_kind: ProjectFileKind) -> Literal["stl", "3mf", "bundle"]:
    if file_kind == "stl":
        return "stl"
    if file_kind == "3mf":
        return "3mf"
    return "bundle"


def _slice_status(file_role: str, validation_status: str, can_slice: bool) -> ProjectFileSliceStatus:
    if file_role == "external_reference":
        return "external_no_local"
    if validation_status in {"quarantined", "metadata_only"}:
        return "pending"
    if validation_status in {"rejected", "analysis_failed"}:
        return "failure"
    return "eligible" if can_slice else "blocked"


def _project_metadata(material: str, component: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    if material.strip():
        metadata["material"] = material.strip()
    if component.strip():
        metadata["component"] = component.strip()
    return metadata


def _tags_json(tags: list[str]) -> str:
    cleaned = []
    for tag in tags:
        value = str(tag).strip().lower()
        if value and value not in cleaned:
            cleaned.append(value[:40])
    return json.dumps(cleaned[:12], ensure_ascii=False)


def _unique_slug(connection, title: str) -> str:
    base = "".join(char.lower() if char.isalnum() else "-" for char in title.strip())
    base = "-".join(part for part in base.split("-") if part)[:80] or "projeto"
    candidate = base
    suffix = 2
    while connection.execute("SELECT 1 FROM print_projects WHERE slug = ?", (candidate,)).fetchone():
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def _quota_for_user(connection, actor_user_id: int) -> int:
    row = connection.execute(
        """
        SELECT quota_bytes
        FROM social_file_storage_policies
        WHERE status = 'active'
          AND ((scope_type = 'user' AND scope_id = ?) OR scope_type = 'global')
        ORDER BY CASE scope_type WHEN 'user' THEN 0 ELSE 1 END
        LIMIT 1
        """,
        (actor_user_id,),
    ).fetchone()
    return int(row["quota_bytes"]) if row is not None else DEFAULT_USER_QUOTA_BYTES
