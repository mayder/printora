from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.modules.community.validation import (
    normalize_slug,
    clean_optional_text,
    clean_library_file_name,
    clean_text_list,
    clean_public_image_urls,
    clean_discussion_text,
    clean_discussion_attachments,
    validate_public_url,
    _is_private_or_local_host,
    _clean_social_links,
)

LibraryVisibility = Literal["private", "friends", "community", "public"]


LibraryFileKind = Literal["stl", "3mf", "bundle"]


LibraryLicense = Literal["cc-by", "cc-by-sa", "cc0", "mit", "custom", "all-rights-reserved"]


LibraryCollectionVisibility = Literal["private", "community", "public"]


PrintListItemStatus = Literal["want_to_print", "printed", "problem"]


LibraryContentClass = Literal["community", "curated", "premium", "sponsored"]


LibraryCommercialStatus = Literal["none", "pending_review", "approved", "rejected"]


class LibraryFileMetadata(BaseModel):
    id: int | None = None
    file_kind: LibraryFileKind
    file_name: str = Field(min_length=1, max_length=180)
    original_url: str | None = Field(default=None, max_length=500)
    size_bytes: int | None = Field(default=None, ge=1, le=500_000_000)
    sha256: str | None = Field(default=None, min_length=64, max_length=64)
    validation_status: str = "metadata_only"
    storage_key: str | None = None
    quarantine_key: str | None = None
    uploaded_size_bytes: int | None = None
    rejection_reason: str | None = None
    deduplicated_from_file_id: int | None = None
    analysis: dict[str, object] = Field(default_factory=dict)
    thumbnail_svg: str | None = None
    analyzed_at: str | None = None

    @field_validator("file_name")
    @classmethod
    def clean_file_name(cls, value: str) -> str:
        return clean_library_file_name(value)

    @field_validator("original_url")
    @classmethod
    def clean_original_url(cls, value: str | None) -> str | None:
        return validate_public_url(value, field_name="original_url", allowed_hosts=None)

    @field_validator("sha256")
    @classmethod
    def clean_sha256(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{64}", cleaned):
            raise ValueError("sha256 inválido")
        return cleaned


class LibraryItemBase(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=1200)
    visibility: LibraryVisibility = "private"
    community_slug: str | None = Field(default=None, max_length=160)
    catalog_variant_id: int | None = Field(default=None, ge=1)
    component: str | None = Field(default=None, max_length=80)
    version_label: str = Field(default="v1", min_length=1, max_length=40)
    material_suggestion: str | None = Field(default=None, max_length=80)
    supports_required: bool = False
    orientation_notes: str | None = Field(default=None, max_length=500)
    license: LibraryLicense = "all-rights-reserved"
    original_author_name: str | None = Field(default=None, max_length=160)
    source_url: str | None = Field(default=None, max_length=500)
    attribution_text: str | None = Field(default=None, max_length=500)
    remix_source_item_id: int | None = Field(default=None, ge=1)
    publication_terms_accepted: bool = False
    content_class: LibraryContentClass = "community"
    commercial_metadata: dict[str, object] = Field(default_factory=dict)
    promotion_disclosure: str | None = Field(default=None, max_length=300)
    files: list[LibraryFileMetadata] = Field(min_length=1, max_length=12)

    @field_validator("title", "description", "orientation_notes")
    @classmethod
    def reject_markup(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None

    @field_validator("component", "version_label", "material_suggestion")
    @classmethod
    def clean_short_text(cls, value: str | None) -> str | None:
        return clean_optional_text(value)

    @field_validator("original_author_name", "attribution_text", "promotion_disclosure")
    @classmethod
    def clean_credit_text(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None

    @field_validator("source_url")
    @classmethod
    def clean_source_url(cls, value: str | None) -> str | None:
        return validate_public_url(value, field_name="source_url", allowed_hosts=None)

    @field_validator("community_slug")
    @classmethod
    def clean_community_slug(cls, value: str | None) -> str | None:
        return normalize_slug(value) if value else None


class LibraryItemCreate(LibraryItemBase):
    pass


class LibraryItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1200)
    visibility: LibraryVisibility | None = None
    community_slug: str | None = Field(default=None, max_length=160)
    catalog_variant_id: int | None = Field(default=None, ge=1)
    component: str | None = Field(default=None, max_length=80)
    version_label: str | None = Field(default=None, min_length=1, max_length=40)
    material_suggestion: str | None = Field(default=None, max_length=80)
    supports_required: bool | None = None
    orientation_notes: str | None = Field(default=None, max_length=500)
    license: LibraryLicense | None = None
    original_author_name: str | None = Field(default=None, max_length=160)
    source_url: str | None = Field(default=None, max_length=500)
    attribution_text: str | None = Field(default=None, max_length=500)
    remix_source_item_id: int | None = Field(default=None, ge=1)
    publication_terms_accepted: bool | None = None
    content_class: LibraryContentClass | None = None
    commercial_metadata: dict[str, object] | None = None
    promotion_disclosure: str | None = Field(default=None, max_length=300)
    files: list[LibraryFileMetadata] | None = Field(default=None, min_length=1, max_length=12)

    @field_validator("title", "description", "orientation_notes")
    @classmethod
    def reject_markup(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None

    @field_validator("component", "version_label", "material_suggestion")
    @classmethod
    def clean_short_text(cls, value: str | None) -> str | None:
        return clean_optional_text(value)

    @field_validator("original_author_name", "attribution_text", "promotion_disclosure")
    @classmethod
    def clean_credit_text(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None

    @field_validator("source_url")
    @classmethod
    def clean_source_url(cls, value: str | None) -> str | None:
        return validate_public_url(value, field_name="source_url", allowed_hosts=None)

    @field_validator("community_slug")
    @classmethod
    def clean_community_slug(cls, value: str | None) -> str | None:
        return normalize_slug(value) if value else None


class LibraryVersionCreate(BaseModel):
    version_label: str = Field(min_length=1, max_length=40)
    changelog: str = Field(default="", max_length=1000)
    files: list[LibraryFileMetadata] = Field(min_length=1, max_length=12)

    @field_validator("version_label")
    @classmethod
    def clean_version_label(cls, value: str) -> str:
        cleaned = clean_optional_text(value)
        if not cleaned:
            raise ValueError("versão inválida")
        return cleaned

    @field_validator("changelog")
    @classmethod
    def clean_changelog(cls, value: str) -> str:
        return clean_discussion_text(value)


class LibraryVersion(BaseModel):
    id: int
    item_id: int
    version_label: str
    changelog: str
    files: list[LibraryFileMetadata] = Field(default_factory=list)
    metadata_snapshot: dict[str, object] = Field(default_factory=dict)
    is_current: bool
    created_by_user_id: int
    created_at: str
    download_count: int = 0


class LibraryCollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    visibility: LibraryCollectionVisibility = "private"
    community_slug: str | None = Field(default=None, max_length=160)

    @field_validator("name", "description")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return clean_discussion_text(value)

    @field_validator("community_slug")
    @classmethod
    def clean_community_slug(cls, value: str | None) -> str | None:
        return normalize_slug(value) if value else None


class LibraryCollectionItemCreate(BaseModel):
    item_id: int = Field(ge=1)
    version_id: int | None = Field(default=None, ge=1)
    notes: str | None = Field(default=None, max_length=300)

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None


class LibraryCollection(BaseModel):
    id: int
    owner_user_id: int
    community_id: int | None = None
    community_slug: str | None = None
    community_name: str | None = None
    name: str
    description: str
    visibility: LibraryCollectionVisibility
    item_count: int = 0
    created_at: str
    updated_at: str


class PrintListCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    printer_id: int | None = Field(default=None, ge=1)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        return clean_discussion_text(value)


class PrintListItemCreate(BaseModel):
    item_id: int = Field(ge=1)
    version_id: int = Field(ge=1)
    status: PrintListItemStatus = "want_to_print"
    notes: str | None = Field(default=None, max_length=300)

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None


class PrintListItemUpdate(BaseModel):
    status: PrintListItemStatus
    notes: str | None = Field(default=None, max_length=300)

    @field_validator("notes")
    @classmethod
    def clean_notes(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None


class PrintListItem(BaseModel):
    id: int
    item_id: int
    version_id: int
    item_title: str
    version_label: str
    status: PrintListItemStatus
    notes: str | None = None
    created_at: str
    updated_at: str


class PrintList(BaseModel):
    id: int
    owner_user_id: int
    printer_id: int | None = None
    printer_name: str | None = None
    name: str
    status: Literal["active", "archived"]
    items: list[PrintListItem] = Field(default_factory=list)
    created_at: str
    updated_at: str


class LibraryDownloadHistoryItem(BaseModel):
    id: int
    item_id: int
    version_id: int | None = None
    title: str
    version_label: str | None = None
    created_at: str


class LibraryOrganizerSummary(BaseModel):
    favorites: list[LibraryItem] = Field(default_factory=list)
    collections: list[LibraryCollection] = Field(default_factory=list)
    print_lists: list[PrintList] = Field(default_factory=list)
    downloads: list[LibraryDownloadHistoryItem] = Field(default_factory=list)


class LibraryItem(BaseModel):
    id: int
    owner_user_id: int
    owner_slug: str | None = None
    owner_display_name: str | None = None
    community_id: int | None = None
    community_slug: str | None = None
    community_name: str | None = None
    catalog_variant_id: int | None = None
    manufacturer_name: str | None = None
    model_name: str | None = None
    variant_name: str | None = None
    title: str
    description: str
    visibility: LibraryVisibility
    component: str | None = None
    version_label: str
    material_suggestion: str | None = None
    supports_required: bool
    orientation_notes: str | None = None
    license: LibraryLicense
    original_author_name: str | None = None
    source_url: str | None = None
    attribution_text: str | None = None
    remix_source_item_id: int | None = None
    remix_source_title: str | None = None
    publication_terms_accepted_at: str | None = None
    content_class: LibraryContentClass = "community"
    commercial_status: LibraryCommercialStatus = "none"
    commercial_metadata: dict[str, object] = Field(default_factory=dict)
    promotion_disclosure: str = ""
    status: Literal["active", "archived"]
    files: list[LibraryFileMetadata] = Field(default_factory=list)
    versions: list[LibraryVersion] = Field(default_factory=list)
    current_version_id: int | None = None
    favorite_count: int = 0
    viewer_favorite: bool = False
    collection_count: int = 0
    print_list_count: int = 0
    download_count: int = 0
    created_at: str
    updated_at: str


class LibraryCommercialReviewCreate(BaseModel):
    status: LibraryCommercialStatus
    note: str = Field(default="", max_length=500)

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str) -> str:
        return clean_discussion_text(value)
