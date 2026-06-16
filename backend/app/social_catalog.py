from __future__ import annotations

from dataclasses import dataclass
import hashlib
import ipaddress
import json
import math
import re
import struct
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.database import connect_database
from app.social_storage import SocialStorageRepository


TrustState = Literal["official", "community", "draft", "obsolete", "blocked"]
ProfileVisibility = Literal["public", "unlisted", "private"]
CommunityStatus = Literal["active", "uncurated", "obsolete", "merged"]
RelationshipType = Literal["follow", "friend", "block"]
RelationshipStatus = Literal["active", "pending", "accepted", "ended"]
FeedContentType = Literal["technical_post", "question", "mod", "print_result", "file_announcement", "curation_notice"]
FeedOrder = Literal["recent", "recommended", "pinned"]
DiscussionReactionType = Literal["like", "useful", "thanks"]
LibraryVisibility = Literal["private", "friends", "community", "public"]
LibraryFileKind = Literal["stl", "3mf", "bundle"]
LibraryLicense = Literal["cc-by", "cc-by-sa", "cc0", "mit", "custom", "all-rights-reserved"]
LibraryCollectionVisibility = Literal["private", "community", "public"]
PrintListItemStatus = Literal["want_to_print", "printed", "problem"]


class CatalogVariant(BaseModel):
    id: int
    slug: str
    name: str
    build_volume: dict[str, object]
    components: dict[str, object]
    firmware_family: str | None
    trust_state: TrustState
    source: str


class CatalogVariantDetail(CatalogVariant):
    manufacturer_id: int
    manufacturer_slug: str
    manufacturer_name: str
    model_id: int
    model_slug: str
    model_name: str
    kinematics: str


class CatalogModelAdmin(BaseModel):
    id: int
    slug: str
    name: str
    kinematics: str
    trust_state: TrustState
    manufacturer_id: int
    manufacturer_slug: str
    manufacturer_name: str
    manufacturer_website_url: str | None = None
    manufacturer_repository_url: str | None = None
    manufacturer_documentation_url: str | None = None
    manufacturer_logo_url: str | None = None
    manufacturer_discord_url: str | None = None
    manufacturer_reddit_url: str | None = None
    manufacturer_summary: str | None = None
    website_url: str | None = None
    repository_url: str | None = None
    documentation_url: str | None = None
    bom_url: str | None = None
    image_url: str | None = None
    discord_url: str | None = None
    reddit_url: str | None = None
    forum_url: str | None = None
    description: str | None = None
    curation_notes: str | None = None
    detail: dict[str, object] = Field(default_factory=dict)
    source_links: dict[str, object] = Field(default_factory=dict)
    variants: list[CatalogVariant] = Field(default_factory=list)


class CatalogModel(BaseModel):
    id: int
    slug: str
    name: str
    kinematics: str
    trust_state: TrustState
    source: str
    variants: list[CatalogVariant] = Field(default_factory=list)


class CatalogManufacturer(BaseModel):
    id: int
    slug: str
    name: str
    trust_state: TrustState
    source: str
    models: list[CatalogModel] = Field(default_factory=list)


class CatalogSummary(BaseModel):
    manufacturers: list[CatalogManufacturer]


class CatalogAdminSummary(BaseModel):
    models: list[CatalogModelAdmin]
    manufacturer_count: int
    model_count: int
    variant_count: int


class CatalogVariantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    build_volume: dict[str, object] | None = None
    components: dict[str, object] | None = None
    firmware_family: str | None = Field(default=None, max_length=80)
    trust_state: TrustState | None = None
    source: str | None = Field(default=None, max_length=120)


class CatalogManufacturerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    trust_state: TrustState = "draft"
    source: str = Field(default="admin", max_length=120)


class CatalogModelCreate(BaseModel):
    manufacturer_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    slug: str | None = Field(default=None, max_length=120)
    kinematics: str = Field(min_length=1, max_length=80)
    trust_state: TrustState = "draft"
    source: str = Field(default="admin", max_length=120)


class CatalogVariantCreate(BaseModel):
    model_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=160)
    slug: str | None = Field(default=None, max_length=120)
    build_volume: dict[str, object] = Field(default_factory=dict)
    components: dict[str, object] = Field(default_factory=dict)
    firmware_family: str | None = Field(default=None, max_length=80)
    trust_state: TrustState = "draft"
    source: str = Field(default="admin", max_length=120)


class PublicProfileUpdate(BaseModel):
    slug: str | None = Field(default=None, max_length=80)
    display_name: str = Field(min_length=1, max_length=120)
    bio: str | None = Field(default=None, max_length=280)
    avatar_url: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=120)
    social_links: dict[str, str | None] = Field(default_factory=dict)
    visibility: ProfileVisibility = "public"

    @field_validator("slug")
    @classmethod
    def clean_slug(cls, value: str | None) -> str | None:
        return normalize_slug(value) if value else None

    @field_validator("avatar_url")
    @classmethod
    def clean_avatar_url(cls, value: str | None) -> str | None:
        return validate_public_url(value, field_name="avatar_url", allowed_hosts=None)

    @field_validator("social_links")
    @classmethod
    def clean_social_links(cls, value: dict[str, str | None]) -> dict[str, str | None]:
        return _clean_social_links(value)


class PublicProfile(BaseModel):
    user_id: int
    slug: str
    display_name: str
    bio: str | None
    avatar_url: str | None
    location: str | None
    social_links: dict[str, str | None]
    visibility: ProfileVisibility
    created_at: str
    updated_at: str
    viewer_blocked: bool = False
    reserved_slugs: list[str] = Field(default_factory=list)
    public_printer_count: int = 0


class PrinterPublicUpdate(BaseModel):
    public_profile_enabled: bool = False
    catalog_variant_id: int | None = Field(default=None, ge=1)
    public_name: str | None = Field(default=None, max_length=120)
    public_description: str | None = Field(default=None, max_length=500)
    public_mods: list[str] = Field(default_factory=list, max_length=20)
    public_images: list[str] = Field(default_factory=list, max_length=6)

    @field_validator("public_images")
    @classmethod
    def clean_public_images(cls, value: list[str]) -> list[str]:
        return clean_public_image_urls(value)


class PublicPrinter(BaseModel):
    id: int
    owner_user_id: int
    owner_slug: str | None
    owner_display_name: str | None
    public_name: str
    public_description: str | None
    public_mods: list[str]
    public_images: list[str]
    catalog_variant_id: int
    manufacturer_slug: str
    manufacturer_name: str
    model_slug: str
    model_name: str
    variant_name: str
    variant_slug: str
    build_volume: dict[str, object]
    kinematics: str
    updated_at: str


class Community(BaseModel):
    id: int
    slug: str
    name: str
    scope: Literal["manufacturer", "model", "variant"]
    status: CommunityStatus
    manufacturer_id: int | None
    manufacturer_slug: str | None = None
    manufacturer_name: str | None = None
    manufacturer_logo_url: str | None = None
    model_id: int | None
    model_slug: str | None = None
    model_name: str | None = None
    variant_id: int | None
    variant_slug: str | None = None
    variant_name: str | None = None
    merged_into_id: int | None = None
    merged_into_slug: str | None = None
    merged_into_name: str | None = None
    member_count: int
    printer_count: int
    file_count: int = 0
    mod_count: int = 0


class CommunityDetail(Community):
    members: list[PublicProfile] = Field(default_factory=list)
    printers: list[PublicPrinter] = Field(default_factory=list)
    filters: CatalogSummary | None = None


class CommunityFeedItem(BaseModel):
    id: int
    community_id: int
    author_user_id: int | None
    author_slug: str | None = None
    author_display_name: str | None = None
    content_type: FeedContentType
    title: str
    body: str
    component: str | None = None
    material: str | None = None
    firmware_family: str | None = None
    problem_tag: str | None = None
    attachments: list[dict[str, str]] = Field(default_factory=list)
    pinned: bool = False
    comment_count: int = 0
    reaction_count: int = 0
    solution_comment_id: int | None = None
    edit_count: int = 0
    deleted_at: str | None = None
    source_type: str
    source_id: str | None = None
    created_at: str
    updated_at: str


class CommunityFeedSummary(BaseModel):
    community: Community
    items: list[CommunityFeedItem]
    page: int
    page_size: int
    has_more: bool
    order: FeedOrder
    filters: dict[str, list[str]] = Field(default_factory=dict)


class CommunityFeedCreate(BaseModel):
    community_id: int = Field(ge=1)
    author_user_id: int | None = Field(default=None, ge=1)
    content_type: FeedContentType
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(default="", max_length=1200)
    component: str | None = Field(default=None, max_length=80)
    material: str | None = Field(default=None, max_length=80)
    firmware_family: str | None = Field(default=None, max_length=80)
    problem_tag: str | None = Field(default=None, max_length=80)
    attachments: list[dict[str, str]] = Field(default_factory=list, max_length=6)
    pinned: bool = False
    visibility: Literal["public", "private"] = "public"
    source_type: str = Field(default="community", max_length=60)
    source_id: str | None = Field(default=None, max_length=120)

    @field_validator("title", "body")
    @classmethod
    def reject_markup(cls, value: str) -> str:
        return clean_discussion_text(value)

    @field_validator("attachments")
    @classmethod
    def clean_attachments(cls, value: list[dict[str, str]]) -> list[dict[str, str]]:
        return clean_discussion_attachments(value)


class CommunityPostCreate(BaseModel):
    content_type: FeedContentType
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=1200)
    component: str | None = Field(default=None, max_length=80)
    material: str | None = Field(default=None, max_length=80)
    firmware_family: str | None = Field(default=None, max_length=80)
    problem_tag: str | None = Field(default=None, max_length=80)
    attachments: list[dict[str, str]] = Field(default_factory=list, max_length=6)

    @field_validator("content_type")
    @classmethod
    def reject_system_type(cls, value: FeedContentType) -> FeedContentType:
        if value == "curation_notice":
            raise ValueError("aviso de curadoria não é post de usuário")
        return value

    @field_validator("title", "body")
    @classmethod
    def reject_markup(cls, value: str) -> str:
        return clean_discussion_text(value)

    @field_validator("attachments")
    @classmethod
    def clean_attachments(cls, value: list[dict[str, str]]) -> list[dict[str, str]]:
        return clean_discussion_attachments(value)


class CommunityPostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    body: str | None = Field(default=None, min_length=1, max_length=1200)
    attachments: list[dict[str, str]] | None = Field(default=None, max_length=6)

    @field_validator("title", "body")
    @classmethod
    def reject_markup(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None

    @field_validator("attachments")
    @classmethod
    def clean_attachments(cls, value: list[dict[str, str]] | None) -> list[dict[str, str]] | None:
        return clean_discussion_attachments(value or []) if value is not None else None


class DiscussionComment(BaseModel):
    id: int
    feed_item_id: int
    author_user_id: int
    author_slug: str | None = None
    author_display_name: str | None = None
    parent_comment_id: int | None = None
    body: str
    attachments: list[dict[str, str]] = Field(default_factory=list)
    edit_count: int = 0
    deleted_at: str | None = None
    created_at: str
    updated_at: str
    replies: list["DiscussionComment"] = Field(default_factory=list)


class DiscussionCommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=1200)
    parent_comment_id: int | None = Field(default=None, ge=1)
    attachments: list[dict[str, str]] = Field(default_factory=list, max_length=6)

    @field_validator("body")
    @classmethod
    def reject_markup(cls, value: str) -> str:
        return clean_discussion_text(value)

    @field_validator("attachments")
    @classmethod
    def clean_attachments(cls, value: list[dict[str, str]]) -> list[dict[str, str]]:
        return clean_discussion_attachments(value)


class DiscussionCommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=1200)
    attachments: list[dict[str, str]] = Field(default_factory=list, max_length=6)

    @field_validator("body")
    @classmethod
    def reject_markup(cls, value: str) -> str:
        return clean_discussion_text(value)

    @field_validator("attachments")
    @classmethod
    def clean_attachments(cls, value: list[dict[str, str]]) -> list[dict[str, str]]:
        return clean_discussion_attachments(value)


class DiscussionReactionCount(BaseModel):
    reaction_type: DiscussionReactionType
    count: int


class DiscussionReactionPayload(BaseModel):
    reaction_type: DiscussionReactionType


class DiscussionDetail(BaseModel):
    post: CommunityFeedItem
    comments: list[DiscussionComment]
    reactions: list[DiscussionReactionCount] = Field(default_factory=list)


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
    files: list[LibraryFileMetadata] = Field(min_length=1, max_length=12)

    @field_validator("title", "description", "orientation_notes")
    @classmethod
    def reject_markup(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None

    @field_validator("component", "version_label", "material_suggestion")
    @classmethod
    def clean_short_text(cls, value: str | None) -> str | None:
        return clean_optional_text(value)

    @field_validator("original_author_name", "attribution_text")
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
    files: list[LibraryFileMetadata] | None = Field(default=None, min_length=1, max_length=12)

    @field_validator("title", "description", "orientation_notes")
    @classmethod
    def reject_markup(cls, value: str | None) -> str | None:
        return clean_discussion_text(value) if value is not None else None

    @field_validator("component", "version_label", "material_suggestion")
    @classmethod
    def clean_short_text(cls, value: str | None) -> str | None:
        return clean_optional_text(value)

    @field_validator("original_author_name", "attribution_text")
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


class RelationshipRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    target_user_id: int
    target_slug: str | None
    target_display_name: str | None
    relation_type: RelationshipType
    status: RelationshipStatus
    created_at: str
    updated_at: str


class RelationshipSummary(BaseModel):
    following: list[RelationshipRecord]
    followers: list[RelationshipRecord]
    friends: list[RelationshipRecord]
    blocked: list[RelationshipRecord]
    pending_friend_requests: list[RelationshipRecord]
    sent_friend_requests: list[RelationshipRecord] = Field(default_factory=list)


@dataclass(frozen=True)
class SocialCatalogRepository:
    database_path: Path

    def list_catalog(self, *, include_blocked: bool = False, include_obsolete: bool = True) -> CatalogSummary:
        state_filter = _catalog_state_filter("trust_state", include_blocked, include_obsolete)
        with connect_database(self.database_path) as connection:
            manufacturers = connection.execute(
                f"""
                SELECT id, slug, name, trust_state, source
                FROM catalog_manufacturers
                WHERE {state_filter}
                ORDER BY name
                """
            ).fetchall()
            models = connection.execute(
                f"""
                SELECT id, manufacturer_id, slug, name, kinematics, trust_state, source
                FROM catalog_printer_models
                WHERE {state_filter}
                ORDER BY name
                """
            ).fetchall()
            variants = connection.execute(
                f"""
                SELECT id, model_id, slug, name, build_volume_json, components_json,
                       firmware_family, trust_state, source
                FROM catalog_printer_variants
                WHERE {state_filter}
                ORDER BY name
                """
            ).fetchall()
        variants_by_model: dict[int, list[CatalogVariant]] = {}
        for row in variants:
            variants_by_model.setdefault(int(row["model_id"]), []).append(_variant_from_row(row))
        models_by_manufacturer: dict[int, list[CatalogModel]] = {}
        for row in models:
            model = CatalogModel(
                id=int(row["id"]),
                slug=str(row["slug"]),
                name=str(row["name"]),
                kinematics=str(row["kinematics"]),
                trust_state=row["trust_state"],
                source=str(row["source"]),
                variants=variants_by_model.get(int(row["id"]), []),
            )
            models_by_manufacturer.setdefault(int(row["manufacturer_id"]), []).append(model)
        return CatalogSummary(
            manufacturers=[
                CatalogManufacturer(
                    id=int(row["id"]),
                    slug=str(row["slug"]),
                    name=str(row["name"]),
                    trust_state=row["trust_state"],
                    source=str(row["source"]),
                    models=models_by_manufacturer.get(int(row["id"]), []),
                )
                for row in manufacturers
            ]
        )

    def search_catalog_admin(
        self,
        *,
        manufacturer: str | None = None,
        model: str | None = None,
        variant: str | None = None,
        component: str | None = None,
        kinematics: str | None = None,
        firmware_family: str | None = None,
        trust_state: TrustState | None = None,
    ) -> CatalogAdminSummary:
        clauses = ["1 = 1"]
        parameters: list[object] = []
        like_filters = [
            ("mf.name || ' ' || mf.slug", manufacturer),
            ("m.name || ' ' || m.slug", model),
            ("v.name || ' ' || v.slug", variant),
            ("v.components_json", component),
            ("m.kinematics", kinematics),
            ("COALESCE(v.firmware_family, '')", firmware_family),
        ]
        for expression, value in like_filters:
            cleaned = clean_optional_text(value)
            if cleaned:
                clauses.append(f"LOWER({expression}) LIKE ?")
                parameters.append(f"%{cleaned.lower()}%")
        if trust_state:
            clauses.append("v.trust_state = ?")
            parameters.append(trust_state)
        else:
            clauses.append("v.trust_state != 'blocked'")
            clauses.append("m.trust_state != 'blocked'")
            clauses.append("mf.trust_state != 'blocked'")
        where_sql = " AND ".join(clauses)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT v.id, v.slug, v.name, v.build_volume_json, v.components_json,
                       v.firmware_family, v.trust_state, v.source,
                       m.id AS model_id, m.slug AS model_slug, m.name AS model_name, m.kinematics,
                       m.trust_state AS model_trust_state, m.website_url AS model_website_url,
                       m.repository_url AS model_repository_url, m.documentation_url AS model_documentation_url,
                       m.bom_url AS model_bom_url, m.image_url AS model_image_url,
                       m.discord_url AS model_discord_url, m.reddit_url AS model_reddit_url,
                       m.forum_url AS model_forum_url, m.description AS model_description,
                       m.curation_notes AS model_curation_notes,
                       m.detail_json AS model_detail_json,
                       m.source_links_json AS model_source_links_json,
                       mf.id AS manufacturer_id, mf.slug AS manufacturer_slug, mf.name AS manufacturer_name,
                       mf.website_url AS manufacturer_website_url,
                       mf.repository_url AS manufacturer_repository_url,
                       mf.documentation_url AS manufacturer_documentation_url,
                       mf.logo_url AS manufacturer_logo_url,
                       mf.discord_url AS manufacturer_discord_url,
                       mf.reddit_url AS manufacturer_reddit_url,
                       mf.summary AS manufacturer_summary
                FROM catalog_printer_variants v
                JOIN catalog_printer_models m ON m.id = v.model_id
                JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
                WHERE {where_sql}
                ORDER BY mf.name, m.name, v.name
                """,
                tuple(parameters),
            ).fetchall()
        models_by_id: dict[int, CatalogModelAdmin] = {}
        manufacturers: set[int] = set()
        variant_count = 0
        for row in rows:
            model_id = int(row["model_id"])
            manufacturers.add(int(row["manufacturer_id"]))
            if model_id not in models_by_id:
                models_by_id[model_id] = CatalogModelAdmin(
                    id=model_id,
                    slug=str(row["model_slug"]),
                    name=str(row["model_name"]),
                    kinematics=str(row["kinematics"]),
                    trust_state=row["model_trust_state"],
                    manufacturer_id=int(row["manufacturer_id"]),
                    manufacturer_slug=str(row["manufacturer_slug"]),
                    manufacturer_name=str(row["manufacturer_name"]),
                    manufacturer_website_url=clean_optional_text(row["manufacturer_website_url"]),
                    manufacturer_repository_url=clean_optional_text(row["manufacturer_repository_url"]),
                    manufacturer_documentation_url=clean_optional_text(row["manufacturer_documentation_url"]),
                    manufacturer_logo_url=clean_optional_text(row["manufacturer_logo_url"]),
                    manufacturer_discord_url=clean_optional_text(row["manufacturer_discord_url"]),
                    manufacturer_reddit_url=clean_optional_text(row["manufacturer_reddit_url"]),
                    manufacturer_summary=clean_optional_text(row["manufacturer_summary"]),
                    website_url=clean_optional_text(row["model_website_url"]),
                    repository_url=clean_optional_text(row["model_repository_url"]),
                    documentation_url=clean_optional_text(row["model_documentation_url"]),
                    bom_url=clean_optional_text(row["model_bom_url"]),
                    image_url=clean_optional_text(row["model_image_url"]),
                    discord_url=clean_optional_text(row["model_discord_url"]),
                    reddit_url=clean_optional_text(row["model_reddit_url"]),
                    forum_url=clean_optional_text(row["model_forum_url"]),
                    description=clean_optional_text(row["model_description"]),
                    curation_notes=clean_optional_text(row["model_curation_notes"]),
                    detail=_json_dict(row["model_detail_json"]),
                    source_links=_json_dict(row["model_source_links_json"]),
                    variants=[],
                )
            models_by_id[model_id].variants.append(_variant_from_row(row))
            variant_count += 1
        models = list(models_by_id.values())
        return CatalogAdminSummary(
            models=models,
            manufacturer_count=len(manufacturers),
            model_count=len(models),
            variant_count=variant_count,
        )

    def create_manufacturer(self, payload: CatalogManufacturerCreate, actor_user_id: int) -> CatalogManufacturer:
        slug = normalize_slug(payload.slug or payload.name)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO catalog_manufacturers (slug, name, trust_state, source, created_by_user_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (slug, payload.name.strip(), payload.trust_state, payload.source.strip(), actor_user_id),
            )
            entity_id = int(cursor.lastrowid)
            self._audit(connection, "manufacturer", entity_id, "create", actor_user_id, payload.model_dump())
            self.sync_all_communities(connection)
            self.sync_default_feed_items(connection)
        return self._get_manufacturer(entity_id)

    def create_model(self, payload: CatalogModelCreate, actor_user_id: int) -> CatalogModel:
        slug = normalize_slug(payload.slug or payload.name)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO catalog_printer_models (
                    manufacturer_id, slug, name, kinematics, trust_state, source, created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.manufacturer_id,
                    slug,
                    payload.name.strip(),
                    payload.kinematics.strip(),
                    payload.trust_state,
                    payload.source.strip(),
                    actor_user_id,
                ),
            )
            entity_id = int(cursor.lastrowid)
            self._audit(connection, "model", entity_id, "create", actor_user_id, payload.model_dump())
            self.sync_all_communities(connection)
            self.sync_default_feed_items(connection)
        return self._get_model(entity_id)

    def create_variant(self, payload: CatalogVariantCreate, actor_user_id: int) -> CatalogVariant:
        slug = normalize_slug(payload.slug or payload.name)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO catalog_printer_variants (
                    model_id, slug, name, build_volume_json, components_json,
                    firmware_family, trust_state, source, created_by_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.model_id,
                    slug,
                    payload.name.strip(),
                    json.dumps(payload.build_volume, ensure_ascii=False, sort_keys=True),
                    json.dumps(payload.components, ensure_ascii=False, sort_keys=True),
                    clean_optional_text(payload.firmware_family),
                    payload.trust_state,
                    payload.source.strip(),
                    actor_user_id,
                ),
            )
            entity_id = int(cursor.lastrowid)
            self._audit(connection, "variant", entity_id, "create", actor_user_id, payload.model_dump())
            self.sync_all_communities(connection)
            self.sync_default_feed_items(connection)
        return self._get_variant(entity_id)

    def update_variant(self, variant_id: int, payload: CatalogVariantUpdate, actor_user_id: int) -> CatalogVariant:
        updates: list[str] = []
        parameters: list[object] = []
        payload_dump = payload.model_dump(exclude_unset=True)
        if "name" in payload_dump and payload.name is not None:
            updates.append("name = ?")
            parameters.append(payload.name.strip())
        if "build_volume" in payload_dump and payload.build_volume is not None:
            updates.append("build_volume_json = ?")
            parameters.append(json.dumps(payload.build_volume, ensure_ascii=False, sort_keys=True))
        if "components" in payload_dump and payload.components is not None:
            updates.append("components_json = ?")
            parameters.append(json.dumps(payload.components, ensure_ascii=False, sort_keys=True))
        if "firmware_family" in payload_dump:
            updates.append("firmware_family = ?")
            parameters.append(clean_optional_text(payload.firmware_family))
        if "trust_state" in payload_dump and payload.trust_state is not None:
            updates.append("trust_state = ?")
            parameters.append(payload.trust_state)
        if "source" in payload_dump and payload.source is not None:
            updates.append("source = ?")
            parameters.append(payload.source.strip())
        if not updates:
            return self._get_variant(variant_id)
        updates.append("updated_at = CURRENT_TIMESTAMP")
        with connect_database(self.database_path) as connection:
            existing = connection.execute("SELECT id FROM catalog_printer_variants WHERE id = ?", (variant_id,)).fetchone()
            if existing is None:
                raise ValueError("variante de catálogo não encontrada")
            connection.execute(
                f"UPDATE catalog_printer_variants SET {', '.join(updates)} WHERE id = ?",
                (*parameters, variant_id),
            )
            self._audit(connection, "variant", variant_id, "update", actor_user_id, payload_dump)
            self.sync_all_communities(connection)
            self.sync_default_feed_items(connection)
        return self._get_variant(variant_id)

    def get_or_create_profile(self, user_id: int) -> PublicProfile:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM social_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row is None:
                user = connection.execute(
                    "SELECT email, display_name FROM auth_users WHERE id = ?",
                    (user_id,),
                ).fetchone()
                if user is None:
                    raise ValueError("usuário não encontrado")
                display_name = clean_optional_text(user["display_name"]) or str(user["email"]).split("@")[0]
                slug = self._unique_slug(connection, display_name, user_id)
                connection.execute(
                    """
                    INSERT INTO social_profiles (user_id, slug, display_name)
                    VALUES (?, ?, ?)
                    """,
                    (user_id, slug, display_name),
                )
                row = connection.execute("SELECT * FROM social_profiles WHERE user_id = ?", (user_id,)).fetchone()
            return self._profile_with_reserved_slugs(connection, row)

    def update_profile(self, user_id: int, payload: PublicProfileUpdate) -> PublicProfile:
        with connect_database(self.database_path) as connection:
            current = connection.execute("SELECT * FROM social_profiles WHERE user_id = ?", (user_id,)).fetchone()
            if current is None:
                self.get_or_create_profile(user_id)
                current = connection.execute("SELECT * FROM social_profiles WHERE user_id = ?", (user_id,)).fetchone()
            slug = payload.slug or str(current["slug"])
            if slug != current["slug"]:
                duplicate = connection.execute(
                    "SELECT 1 FROM social_profiles WHERE slug = ? AND user_id != ?",
                    (slug, user_id),
                ).fetchone()
                if duplicate is not None:
                    raise ValueError("slug já está em uso")
                reserved = connection.execute(
                    """
                    SELECT 1 FROM social_profile_slug_history
                    WHERE slug = ? AND user_id != ?
                    """,
                    (slug, user_id),
                ).fetchone()
                if reserved is not None:
                    raise ValueError("slug já usado anteriormente")
                connection.execute(
                    "INSERT OR IGNORE INTO social_profile_slug_history (user_id, slug) VALUES (?, ?)",
                    (user_id, current["slug"]),
                )
            connection.execute(
                """
                UPDATE social_profiles
                SET slug = ?, display_name = ?, bio = ?, avatar_url = ?, location = ?,
                    social_links_json = ?, visibility = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (
                    slug,
                    payload.display_name.strip(),
                    clean_optional_text(payload.bio),
                    clean_optional_text(payload.avatar_url),
                    clean_optional_text(payload.location),
                    json.dumps(payload.social_links, ensure_ascii=False, sort_keys=True),
                    payload.visibility,
                    user_id,
                ),
            )
            row = connection.execute("SELECT * FROM social_profiles WHERE user_id = ?", (user_id,)).fetchone()
            self.sync_communities_for_user(connection, user_id)
            return self._profile_with_reserved_slugs(connection, row)

    def public_profile_by_slug(self, slug: str, viewer_user_id: int | None = None) -> PublicProfile | None:
        clean_slug = normalize_slug(slug)
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT * FROM social_profiles WHERE slug = ?", (clean_slug,)).fetchone()
            if row is None or row["visibility"] == "private":
                return None
            viewer_blocked = False
            if viewer_user_id is not None:
                viewer_blocked = self._is_blocked(connection, int(row["user_id"]), viewer_user_id)
        profile = _profile_from_row(row)
        return profile.model_copy(update={"viewer_blocked": viewer_blocked})

    def search_profiles(self, query: str | None = None, viewer_user_id: int | None = None) -> list[PublicProfile]:
        cleaned = normalize_slug(query) if clean_optional_text(query) else ""
        like = f"%{cleaned}%"
        block_clause = ""
        block_parameters: tuple[object, ...] = ()
        if viewer_user_id is not None:
            block_clause = """
              AND NOT EXISTS (
                SELECT 1 FROM social_relationships br
                WHERE br.relation_type = 'block'
                  AND br.status = 'active'
                  AND (
                    (br.actor_user_id = sp.user_id AND br.target_user_id = ?)
                    OR (br.actor_user_id = ? AND br.target_user_id = sp.user_id)
                  )
              )
            """
            block_parameters = (viewer_user_id, viewer_user_id)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT sp.*
                FROM social_profiles sp
                LEFT JOIN social_user_safety_settings safety ON safety.user_id = sp.user_id
                WHERE sp.visibility != 'private'
                  AND (
                    (? = '' AND sp.visibility = 'public' AND COALESCE(safety.profile_discoverable, 1) = 1)
                    OR (
                      ? != ''
                      AND (
                        sp.slug = ?
                        OR (
                          sp.visibility = 'public'
                          AND COALESCE(safety.profile_discoverable, 1) = 1
                          AND LOWER(sp.display_name || ' ' || sp.slug) LIKE ?
                        )
                      )
                    )
                  )
                  {block_clause}
                ORDER BY CASE WHEN sp.slug = ? THEN 0 ELSE 1 END, sp.updated_at DESC, sp.display_name
                LIMIT 20
                """,
                (cleaned, cleaned, cleaned, like, *block_parameters, cleaned),
            ).fetchall()
            user_ids = [int(row["user_id"]) for row in rows]
            printer_counts: dict[int, int] = {}
            if user_ids:
                placeholders = ", ".join("?" for _ in user_ids)
                count_rows = connection.execute(
                    f"""
                    SELECT owner_user_id, COUNT(*) AS total
                    FROM printers
                    WHERE public_profile_enabled = 1
                      AND owner_user_id IN ({placeholders})
                    GROUP BY owner_user_id
                    """,
                    tuple(user_ids),
                ).fetchall()
                printer_counts = {int(row["owner_user_id"]): int(row["total"]) for row in count_rows}
        return [
            _profile_from_row(row).model_copy(update={"public_printer_count": printer_counts.get(int(row["user_id"]), 0)})
            for row in rows
        ]

    def update_printer_public(self, printer_id: int, owner_user_id: int, payload: PrinterPublicUpdate) -> PublicPrinter | None:
        with connect_database(self.database_path) as connection:
            printer = connection.execute(
                "SELECT id, name, owner_user_id FROM printers WHERE id = ? AND owner_user_id = ?",
                (printer_id, owner_user_id),
            ).fetchone()
            if printer is None:
                return None
            profile = connection.execute("SELECT 1 FROM social_profiles WHERE user_id = ?", (owner_user_id,)).fetchone()
            if profile is None:
                user = connection.execute("SELECT email, display_name FROM auth_users WHERE id = ?", (owner_user_id,)).fetchone()
                if user is None:
                    raise ValueError("usuário não encontrado")
                display_name = clean_optional_text(user["display_name"]) or str(user["email"]).split("@")[0]
                connection.execute(
                    "INSERT INTO social_profiles (user_id, slug, display_name) VALUES (?, ?, ?)",
                    (owner_user_id, self._unique_slug(connection, display_name, owner_user_id), display_name),
                )
            if payload.public_profile_enabled and payload.catalog_variant_id is None:
                raise ValueError("impressora pública exige variante do catálogo")
            if payload.catalog_variant_id is not None:
                variant = connection.execute(
                    """
                    SELECT id FROM catalog_printer_variants
                    WHERE id = ? AND trust_state NOT IN ('blocked', 'obsolete')
                    """,
                    (payload.catalog_variant_id,),
                ).fetchone()
                if variant is None:
                    raise ValueError("variante de catálogo inválida para publicação")
            connection.execute(
                """
                UPDATE printers
                SET public_profile_enabled = ?, catalog_variant_id = ?, public_name = ?,
                    public_description = ?, public_mods_json = ?, public_images_json = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    1 if payload.public_profile_enabled else 0,
                    payload.catalog_variant_id,
                    clean_optional_text(payload.public_name) or str(printer["name"]),
                    clean_optional_text(payload.public_description),
                    json.dumps(clean_text_list(payload.public_mods, 80), ensure_ascii=False),
                    json.dumps(payload.public_images, ensure_ascii=False),
                    printer_id,
                ),
            )
            self.sync_communities_for_user(connection, owner_user_id)
            self.sync_default_feed_items(connection)
        return self.public_printer(printer_id)

    def public_printer(self, printer_id: int, viewer_user_id: int | None = None) -> PublicPrinter | None:
        clauses = ["p.id = ?", "p.public_profile_enabled = 1", "sp.visibility != 'private'"]
        parameters: list[object] = [printer_id]
        if viewer_user_id is not None:
            clauses.append(
                """
                NOT EXISTS (
                  SELECT 1 FROM social_relationships br
                  WHERE br.relation_type = 'block'
                    AND br.status = 'active'
                    AND (
                      (br.actor_user_id = p.owner_user_id AND br.target_user_id = ?)
                      OR (br.actor_user_id = ? AND br.target_user_id = p.owner_user_id)
                    )
                )
                """
            )
            parameters.extend([viewer_user_id, viewer_user_id])
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                PUBLIC_PRINTER_SQL + f" WHERE {' AND '.join(clauses)}",
                tuple(parameters),
            ).fetchone()
        return _public_printer_from_row(row) if row else None

    def list_public_printers_for_profile(self, slug: str, viewer_user_id: int | None = None) -> list[PublicPrinter]:
        clean_slug = normalize_slug(slug)
        clauses = ["sp.slug = ?", "sp.visibility != 'private'", "p.public_profile_enabled = 1"]
        parameters: list[object] = [clean_slug]
        if viewer_user_id is not None:
            clauses.append(
                """
                NOT EXISTS (
                  SELECT 1 FROM social_relationships br
                  WHERE br.relation_type = 'block'
                    AND br.status = 'active'
                    AND (
                      (br.actor_user_id = p.owner_user_id AND br.target_user_id = ?)
                      OR (br.actor_user_id = ? AND br.target_user_id = p.owner_user_id)
                    )
                )
                """
            )
            parameters.extend([viewer_user_id, viewer_user_id])
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                PUBLIC_PRINTER_SQL
                + f"""
                WHERE {' AND '.join(clauses)}
                ORDER BY p.updated_at DESC, p.id DESC
                """,
                tuple(parameters),
            ).fetchall()
        return [_public_printer_from_row(row) for row in rows]

    def search_public_printers(
        self,
        *,
        manufacturer: str | None = None,
        model: str | None = None,
        variant: str | None = None,
        mod: str | None = None,
        viewer_user_id: int | None = None,
    ) -> list[PublicPrinter]:
        clauses = ["sp.visibility = 'public'", "p.public_profile_enabled = 1"]
        parameters: list[object] = []
        like_filters = [
            ("mf.name || ' ' || mf.slug", manufacturer),
            ("m.name || ' ' || m.slug", model),
            ("v.name || ' ' || v.slug", variant),
            ("p.public_mods_json", mod),
        ]
        for expression, value in like_filters:
            cleaned = clean_optional_text(value)
            if cleaned:
                clauses.append(f"LOWER({expression}) LIKE ?")
                parameters.append(f"%{cleaned.lower()}%")
        if viewer_user_id is not None:
            clauses.append(
                """
                NOT EXISTS (
                  SELECT 1 FROM social_relationships br
                  WHERE br.relation_type = 'block'
                    AND br.status = 'active'
                    AND (
                      (br.actor_user_id = p.owner_user_id AND br.target_user_id = ?)
                      OR (br.actor_user_id = ? AND br.target_user_id = p.owner_user_id)
                    )
                )
                """
            )
            parameters.extend([viewer_user_id, viewer_user_id])
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                PUBLIC_PRINTER_SQL
                + f"""
                WHERE {' AND '.join(clauses)}
                ORDER BY p.updated_at DESC, p.id DESC
                LIMIT 100
                """,
                tuple(parameters),
            ).fetchall()
        return [_public_printer_from_row(row) for row in rows]

    def list_communities(
        self,
        *,
        manufacturer: str | None = None,
        model: str | None = None,
        variant: str | None = None,
        component: str | None = None,
    ) -> list[Community]:
        clauses, parameters = self._community_filters(
            manufacturer=manufacturer,
            model=model,
            variant=variant,
            component=component,
        )
        where_sql = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with connect_database(self.database_path) as connection:
            rows = connection.execute(COMMUNITY_SQL + where_sql + COMMUNITY_GROUP_SQL + " ORDER BY c.scope, c.name", tuple(parameters)).fetchall()
        return [_community_from_row(row) for row in rows]

    def community_detail(self, slug: str) -> CommunityDetail | None:
        clean_slug = normalize_slug(slug)
        with connect_database(self.database_path) as connection:
            row = connection.execute(COMMUNITY_SQL + " WHERE c.slug = ?" + COMMUNITY_GROUP_SQL, (clean_slug,)).fetchone()
            if row is None:
                return None
            community = _community_from_row(row)
            if community.status == "merged" and community.merged_into_id is None:
                return CommunityDetail(**community.model_dump(), filters=self.list_catalog())
            member_rows = connection.execute(
                """
                SELECT sp.*
                FROM social_community_members cm
                JOIN social_profiles sp ON sp.user_id = cm.user_id
                WHERE cm.community_id = ? AND cm.active = 1 AND sp.visibility = 'public'
                GROUP BY sp.user_id
                ORDER BY sp.display_name
                """,
                (row["id"],),
            ).fetchall()
            printer_rows = connection.execute(
                PUBLIC_PRINTER_SQL
                + """
                JOIN social_community_members cm ON cm.printer_id = p.id
                WHERE cm.community_id = ? AND cm.active = 1
                  AND p.public_profile_enabled = 1
                  AND sp.visibility = 'public'
                  AND ? IN ('active', 'uncurated')
                ORDER BY p.updated_at DESC
                """,
                (row["id"], community.status),
            ).fetchall()
        return CommunityDetail(
            **community.model_dump(),
            members=[] if community.status not in {"active", "uncurated"} else [_profile_from_row(member_row) for member_row in member_rows],
            printers=[] if community.status not in {"active", "uncurated"} else [_public_printer_from_row(printer_row) for printer_row in printer_rows],
            filters=self.list_catalog(),
        )

    def list_community_feed(
        self,
        slug: str,
        *,
        content_type: FeedContentType | None = None,
        component: str | None = None,
        material: str | None = None,
        firmware_family: str | None = None,
        problem: str | None = None,
        order: FeedOrder = "recent",
        page: int = 1,
        page_size: int = 20,
    ) -> CommunityFeedSummary | None:
        clean_slug = normalize_slug(slug)
        safe_page = max(page, 1)
        safe_page_size = min(max(page_size, 1), 50)
        with connect_database(self.database_path) as connection:
            row = connection.execute(COMMUNITY_SQL + " WHERE c.slug = ?" + COMMUNITY_GROUP_SQL, (clean_slug,)).fetchone()
            if row is None:
                return None
            community = _community_from_row(row)
            clauses = ["f.community_id = ?", "f.visibility = 'public'", "f.deleted_at IS NULL", "? IN ('active', 'uncurated')"]
            parameters: list[object] = [community.id, community.status]
            for column, value in [
                ("f.content_type", content_type),
                ("f.component", component),
                ("f.material", material),
                ("f.firmware_family", firmware_family),
                ("f.problem_tag", problem),
            ]:
                cleaned = clean_optional_text(value)
                if cleaned:
                    clauses.append(f"LOWER({column}) = LOWER(?)")
                    parameters.append(cleaned)
            order_sql = {
                "recent": "f.created_at DESC, f.id DESC",
                "recommended": "f.pinned DESC, CASE f.content_type WHEN 'curation_notice' THEN 0 WHEN 'question' THEN 1 WHEN 'technical_post' THEN 2 WHEN 'mod' THEN 3 ELSE 4 END, f.created_at DESC, f.id DESC",
                "pinned": "f.pinned DESC, f.created_at DESC, f.id DESC",
            }[order]
            rows = connection.execute(
                FEED_ITEM_SQL
                + f"""
                WHERE {' AND '.join(clauses)}
                ORDER BY {order_sql}
                LIMIT ? OFFSET ?
                """,
                tuple([*parameters, safe_page_size + 1, (safe_page - 1) * safe_page_size]),
            ).fetchall()
            filter_rows = connection.execute(
                """
                SELECT component, material, firmware_family, problem_tag
                FROM social_feed_items
                WHERE community_id = ? AND visibility = 'public' AND deleted_at IS NULL
                """,
                (community.id,),
            ).fetchall()
        return CommunityFeedSummary(
            community=community,
            items=[_feed_item_from_row(item) for item in rows[:safe_page_size]],
            page=safe_page,
            page_size=safe_page_size,
            has_more=len(rows) > safe_page_size,
            order=order,
            filters=_feed_filter_options(filter_rows),
        )

    def create_feed_item(self, payload: CommunityFeedCreate) -> CommunityFeedItem:
        with connect_database(self.database_path) as connection:
            community = connection.execute("SELECT status FROM social_communities WHERE id = ?", (payload.community_id,)).fetchone()
            if community is None:
                raise ValueError("comunidade não encontrada")
            if community["status"] not in {"active", "uncurated"}:
                raise ValueError("comunidade não aceita novos itens de feed")
            if payload.author_user_id is not None:
                self._ensure_user_exists(connection, payload.author_user_id)
            cursor = connection.execute(
                """
                INSERT INTO social_feed_items (
                    community_id, author_user_id, content_type, title, body, component, material,
                    firmware_family, problem_tag, attachments_json, pinned, visibility, source_type, source_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.community_id,
                    payload.author_user_id,
                    payload.content_type,
                    payload.title.strip(),
                    payload.body.strip(),
                    clean_optional_text(payload.component),
                    clean_optional_text(payload.material),
                    clean_optional_text(payload.firmware_family),
                    clean_optional_text(payload.problem_tag),
                    json.dumps(payload.attachments, ensure_ascii=False, sort_keys=True),
                    1 if payload.pinned else 0,
                    payload.visibility,
                    payload.source_type.strip()[:60],
                    clean_optional_text(payload.source_id),
                ),
            )
            row = connection.execute(FEED_ITEM_SQL + "WHERE f.id = ?", (cursor.lastrowid,)).fetchone()
        return _feed_item_from_row(row)

    def create_library_item(self, actor_user_id: int, payload: LibraryItemCreate) -> LibraryItem:
        with connect_database(self.database_path) as connection:
            self._ensure_user_exists(connection, actor_user_id)
            self._ensure_profile_for_user(connection, actor_user_id)
            community_id = self._library_community_id(connection, payload.community_slug, payload.visibility)
            self._ensure_library_variant(connection, payload.catalog_variant_id)
            self._ensure_library_item_publishable(connection, payload.visibility, payload.license, payload.original_author_name, payload.publication_terms_accepted, payload.remix_source_item_id)
            cursor = connection.execute(
                """
                INSERT INTO social_library_items (
                    owner_user_id, community_id, catalog_variant_id, title, description, visibility,
                    component, version_label, material_suggestion, supports_required, orientation_notes, license,
                    original_author_name, source_url, attribution_text, remix_source_item_id,
                    publication_terms_accepted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CASE WHEN ? THEN CURRENT_TIMESTAMP ELSE NULL END)
                """,
                (
                    actor_user_id,
                    community_id,
                    payload.catalog_variant_id,
                    payload.title.strip(),
                    payload.description.strip(),
                    payload.visibility,
                    clean_optional_text(payload.component),
                    payload.version_label or "v1",
                    clean_optional_text(payload.material_suggestion),
                    1 if payload.supports_required else 0,
                    clean_optional_text(payload.orientation_notes),
                    payload.license,
                    clean_optional_text(payload.original_author_name),
                    clean_optional_text(payload.source_url),
                    clean_optional_text(payload.attribution_text),
                    payload.remix_source_item_id,
                    1 if payload.publication_terms_accepted else 0,
                ),
            )
            item_id = int(cursor.lastrowid)
            self._replace_library_files(connection, item_id, payload.files)
            self._create_library_version_snapshot(
                connection,
                item_id,
                actor_user_id,
                payload.version_label or "v1",
                "Versão inicial",
                make_current=True,
            )
            self._audit(connection, "social_library_item", item_id, "create", actor_user_id, {"retention_days": 180})
            row = self._library_item_row(connection, item_id)
            return self._library_item_from_row(connection, row)

    def update_library_item(self, item_id: int, actor_user_id: int, is_admin: bool, payload: LibraryItemUpdate) -> LibraryItem:
        with connect_database(self.database_path) as connection:
            existing = self._library_item_row(connection, item_id, include_archived=True)
            if existing is None:
                raise ValueError("item de biblioteca não encontrado")
            self._ensure_library_owner(existing, actor_user_id, is_admin)
            updates: list[str] = []
            parameters: list[object] = []
            data = payload.model_dump(exclude_unset=True)
            if "title" in data and payload.title is not None:
                updates.append("title = ?")
                parameters.append(payload.title.strip())
            if "description" in data and payload.description is not None:
                updates.append("description = ?")
                parameters.append(payload.description.strip())
            if "visibility" in data and payload.visibility is not None:
                if payload.visibility == "community" and "community_slug" not in data and existing["community_id"] is None:
                    raise ValueError("visibilidade de comunidade exige comunidade")
                updates.append("visibility = ?")
                parameters.append(payload.visibility)
            if "community_slug" in data:
                visibility = payload.visibility or existing["visibility"]
                updates.append("community_id = ?")
                parameters.append(self._library_community_id(connection, payload.community_slug, visibility))
            if "catalog_variant_id" in data:
                self._ensure_library_variant(connection, payload.catalog_variant_id)
                updates.append("catalog_variant_id = ?")
                parameters.append(payload.catalog_variant_id)
            for column, value in [
                ("component", payload.component),
                ("version_label", payload.version_label),
                ("material_suggestion", payload.material_suggestion),
                ("orientation_notes", payload.orientation_notes),
            ]:
                if column in data:
                    updates.append(f"{column} = ?")
                    parameters.append(clean_optional_text(value))
            if "supports_required" in data and payload.supports_required is not None:
                updates.append("supports_required = ?")
                parameters.append(1 if payload.supports_required else 0)
            if "license" in data and payload.license is not None:
                updates.append("license = ?")
                parameters.append(payload.license)
            for column, value in [
                ("original_author_name", payload.original_author_name),
                ("source_url", payload.source_url),
                ("attribution_text", payload.attribution_text),
            ]:
                if column in data:
                    updates.append(f"{column} = ?")
                    parameters.append(clean_optional_text(value))
            if "remix_source_item_id" in data:
                self._ensure_library_remix_source(connection, payload.remix_source_item_id, item_id)
                updates.append("remix_source_item_id = ?")
                parameters.append(payload.remix_source_item_id)
            if payload.publication_terms_accepted is True:
                updates.append("publication_terms_accepted_at = COALESCE(publication_terms_accepted_at, CURRENT_TIMESTAMP)")
            resulting_visibility = payload.visibility or existing["visibility"]
            resulting_license = payload.license or existing["license"]
            resulting_author = payload.original_author_name if "original_author_name" in data else existing["original_author_name"]
            resulting_terms = bool(payload.publication_terms_accepted) or existing["publication_terms_accepted_at"] is not None
            resulting_remix = payload.remix_source_item_id if "remix_source_item_id" in data else existing["remix_source_item_id"]
            self._ensure_library_item_publishable(connection, resulting_visibility, resulting_license, resulting_author, resulting_terms, resulting_remix, current_item_id=item_id)
            if updates:
                updates.append("updated_at = CURRENT_TIMESTAMP")
                connection.execute(f"UPDATE social_library_items SET {', '.join(updates)} WHERE id = ?", (*parameters, item_id))
            if payload.files is not None:
                self._replace_library_files(connection, item_id, payload.files)
                self._create_library_version_snapshot(
                    connection,
                    item_id,
                    actor_user_id,
                    payload.version_label or str(existing["version_label"]),
                    "Atualização dos arquivos do modelo",
                    make_current=True,
                )
            self._audit(connection, "social_library_item", item_id, "update", actor_user_id, {"retention_days": 180})
            row = self._library_item_row(connection, item_id)
            return self._library_item_from_row(connection, row)

    def archive_library_item(self, item_id: int, actor_user_id: int, is_admin: bool) -> None:
        with connect_database(self.database_path) as connection:
            row = self._library_item_row(connection, item_id, include_archived=True)
            if row is None:
                raise ValueError("item de biblioteca não encontrado")
            self._ensure_library_owner(row, actor_user_id, is_admin)
            connection.execute("UPDATE social_library_items SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (item_id,))
            self._audit(connection, "social_library_item", item_id, "archive", actor_user_id, {"retention_days": 180})

    def library_item(self, item_id: int, viewer_user_id: int | None = None) -> LibraryItem | None:
        with connect_database(self.database_path) as connection:
            row = self._library_item_row(connection, item_id)
            if row is None or not self._can_view_library_item(connection, row, viewer_user_id):
                return None
            return self._library_item_from_row(connection, row)

    def list_library_for_community(self, slug: str, viewer_user_id: int | None = None) -> list[LibraryItem]:
        clean_slug = normalize_slug(slug)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                LIBRARY_ITEM_SQL
                + """
                WHERE c.slug = ? AND li.status = 'active'
                GROUP BY li.id
                ORDER BY li.updated_at DESC, li.id DESC
                LIMIT 100
                """,
                (clean_slug,),
            ).fetchall()
            return [
                self._library_item_from_row(connection, row)
                for row in rows
                if self._can_view_library_item(connection, row, viewer_user_id)
            ]

    def list_library_for_profile(self, slug: str, viewer_user_id: int | None = None) -> list[LibraryItem]:
        clean_slug = normalize_slug(slug)
        with connect_database(self.database_path) as connection:
            owner = connection.execute("SELECT user_id FROM social_profiles WHERE slug = ? AND visibility != 'private'", (clean_slug,)).fetchone()
            if owner is None:
                return []
            rows = connection.execute(
                LIBRARY_ITEM_SQL
                + """
                WHERE li.owner_user_id = ? AND li.status = 'active'
                GROUP BY li.id
                ORDER BY li.updated_at DESC, li.id DESC
                LIMIT 100
                """,
                (owner["user_id"],),
            ).fetchall()
            return [
                self._library_item_from_row(connection, row)
                for row in rows
                if self._can_view_library_item(connection, row, viewer_user_id)
            ]

    def register_library_download(self, item_id: int, viewer_user_id: int | None = None, version_id: int | None = None) -> LibraryItem | None:
        with connect_database(self.database_path) as connection:
            row = self._library_item_row(connection, item_id)
            if row is None or not self._can_view_library_item(connection, row, viewer_user_id):
                return None
            if version_id is not None:
                version = connection.execute(
                    "SELECT id FROM social_library_versions WHERE id = ? AND item_id = ?",
                    (version_id, item_id),
                ).fetchone()
                if version is None:
                    raise ValueError("versão não encontrada")
            connection.execute(
                """
                INSERT INTO social_library_downloads (item_id, version_id, user_id, anonymous_label)
                VALUES (?, ?, ?, ?)
                """,
                (item_id, version_id, viewer_user_id, None if viewer_user_id else "public"),
            )
            updated = self._library_item_row(connection, item_id)
            return self._library_item_from_row(connection, updated)

    def library_organizer(self, actor_user_id: int) -> LibraryOrganizerSummary:
        with connect_database(self.database_path) as connection:
            self._ensure_user_exists(connection, actor_user_id)
            return self._library_organizer_summary(connection, actor_user_id)

    def set_library_favorite(self, item_id: int, actor_user_id: int, enabled: bool) -> LibraryItem:
        with connect_database(self.database_path) as connection:
            row = self._library_item_row(connection, item_id)
            if row is None or not self._can_view_library_item(connection, row, actor_user_id):
                raise ValueError("arquivo não encontrado")
            if enabled:
                connection.execute(
                    "INSERT OR IGNORE INTO social_library_favorites (user_id, item_id) VALUES (?, ?)",
                    (actor_user_id, item_id),
                )
            else:
                connection.execute("DELETE FROM social_library_favorites WHERE user_id = ? AND item_id = ?", (actor_user_id, item_id))
            self._audit(connection, "social_library_item", item_id, "favorite" if enabled else "unfavorite", actor_user_id, {"retention_days": 180})
            updated = self._library_item_row(connection, item_id)
            return self._library_item_from_row(connection, updated)

    def create_library_collection(self, actor_user_id: int, payload: LibraryCollectionCreate) -> LibraryOrganizerSummary:
        with connect_database(self.database_path) as connection:
            self._ensure_user_exists(connection, actor_user_id)
            community_id = self._collection_community_id(connection, payload.community_slug, payload.visibility)
            cursor = connection.execute(
                """
                INSERT INTO social_library_collections (owner_user_id, community_id, name, description, visibility)
                VALUES (?, ?, ?, ?, ?)
                """,
                (actor_user_id, community_id, payload.name.strip(), payload.description.strip(), payload.visibility),
            )
            self._audit(connection, "social_library_collection", int(cursor.lastrowid), "create", actor_user_id, {"retention_days": 180})
            return self._library_organizer_summary(connection, actor_user_id)

    def add_library_collection_item(self, collection_id: int, actor_user_id: int, payload: LibraryCollectionItemCreate) -> LibraryOrganizerSummary:
        with connect_database(self.database_path) as connection:
            collection = self._library_collection_row(connection, collection_id)
            if collection is None:
                raise ValueError("coleção não encontrada")
            self._ensure_collection_owner(collection, actor_user_id)
            item_row = self._library_item_row(connection, payload.item_id)
            if item_row is None or not self._can_view_library_item(connection, item_row, actor_user_id):
                raise ValueError("arquivo não encontrado")
            version_id = payload.version_id or self._current_library_version_id(connection, payload.item_id)
            self._ensure_library_version(connection, payload.item_id, version_id)
            connection.execute(
                """
                INSERT INTO social_library_collection_items (collection_id, item_id, version_id, added_by_user_id, notes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(collection_id, item_id, version_id) DO UPDATE SET
                    notes = excluded.notes
                """,
                (collection_id, payload.item_id, version_id, actor_user_id, clean_optional_text(payload.notes)),
            )
            self._audit(connection, "social_library_collection", collection_id, "add_item", actor_user_id, {"retention_days": 180, "item_id": payload.item_id, "version_id": version_id})
            return self._library_organizer_summary(connection, actor_user_id)

    def create_print_list(self, actor_user_id: int, payload: PrintListCreate) -> LibraryOrganizerSummary:
        with connect_database(self.database_path) as connection:
            self._ensure_user_exists(connection, actor_user_id)
            self._ensure_print_list_printer(connection, actor_user_id, payload.printer_id)
            cursor = connection.execute(
                "INSERT INTO social_print_lists (owner_user_id, printer_id, name) VALUES (?, ?, ?)",
                (actor_user_id, payload.printer_id, payload.name.strip()),
            )
            self._audit(connection, "social_print_list", int(cursor.lastrowid), "create", actor_user_id, {"retention_days": 180})
            return self._library_organizer_summary(connection, actor_user_id)

    def add_print_list_item(self, print_list_id: int, actor_user_id: int, payload: PrintListItemCreate) -> LibraryOrganizerSummary:
        with connect_database(self.database_path) as connection:
            print_list = self._print_list_row(connection, print_list_id)
            if print_list is None:
                raise ValueError("lista de impressão não encontrada")
            self._ensure_print_list_owner(print_list, actor_user_id)
            item_row = self._library_item_row(connection, payload.item_id)
            if item_row is None or not self._can_view_library_item(connection, item_row, actor_user_id):
                raise ValueError("arquivo não encontrado")
            self._ensure_library_version(connection, payload.item_id, payload.version_id)
            connection.execute(
                """
                INSERT INTO social_print_list_items (print_list_id, item_id, version_id, status, notes)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(print_list_id, item_id, version_id) DO UPDATE SET
                    status = excluded.status,
                    notes = excluded.notes,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (print_list_id, payload.item_id, payload.version_id, payload.status, clean_optional_text(payload.notes)),
            )
            self._audit(connection, "social_print_list", print_list_id, "add_item", actor_user_id, {"retention_days": 180, "item_id": payload.item_id, "version_id": payload.version_id})
            return self._library_organizer_summary(connection, actor_user_id)

    def update_print_list_item(self, print_list_item_id: int, actor_user_id: int, payload: PrintListItemUpdate) -> LibraryOrganizerSummary:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT pli.id, pli.print_list_id, pl.owner_user_id
                FROM social_print_list_items pli
                JOIN social_print_lists pl ON pl.id = pli.print_list_id
                WHERE pli.id = ?
                """,
                (print_list_item_id,),
            ).fetchone()
            if row is None:
                raise ValueError("item de lista não encontrado")
            self._ensure_print_list_owner(row, actor_user_id)
            connection.execute(
                "UPDATE social_print_list_items SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (payload.status, clean_optional_text(payload.notes), print_list_item_id),
            )
            self._audit(connection, "social_print_list", int(row["print_list_id"]), "update_item", actor_user_id, {"retention_days": 180, "item_id": print_list_item_id, "status": payload.status})
            return self._library_organizer_summary(connection, actor_user_id)

    def create_library_version(self, item_id: int, actor_user_id: int, is_admin: bool, payload: LibraryVersionCreate) -> LibraryItem:
        with connect_database(self.database_path) as connection:
            row = self._library_item_row(connection, item_id, include_archived=True)
            if row is None:
                raise ValueError("item de biblioteca não encontrado")
            self._ensure_library_owner(row, actor_user_id, is_admin)
            if row["status"] != "active":
                raise ValueError("item arquivado não aceita nova versão")
            self._replace_library_files(connection, item_id, payload.files)
            self._create_library_version_snapshot(
                connection,
                item_id,
                actor_user_id,
                payload.version_label,
                payload.changelog,
                make_current=True,
            )
            self._audit(connection, "social_library_item", item_id, "version_create", actor_user_id, {"retention_days": 180, "version_label": payload.version_label})
            updated = self._library_item_row(connection, item_id)
            return self._library_item_from_row(connection, updated)

    def promote_library_version(self, item_id: int, version_id: int, actor_user_id: int, is_admin: bool) -> LibraryItem:
        with connect_database(self.database_path) as connection:
            row = self._library_item_row(connection, item_id, include_archived=True)
            if row is None:
                raise ValueError("item de biblioteca não encontrado")
            self._ensure_library_owner(row, actor_user_id, is_admin)
            version = connection.execute(
                "SELECT id, version_label, files_snapshot_json FROM social_library_versions WHERE id = ? AND item_id = ?",
                (version_id, item_id),
            ).fetchone()
            if version is None:
                raise ValueError("versão não encontrada")
            self._restore_library_files_from_snapshot(connection, item_id, str(version["files_snapshot_json"]))
            connection.execute("UPDATE social_library_versions SET is_current = 0 WHERE item_id = ?", (item_id,))
            connection.execute("UPDATE social_library_versions SET is_current = 1 WHERE id = ?", (version_id,))
            connection.execute(
                "UPDATE social_library_items SET version_label = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (version["version_label"], item_id),
            )
            self._audit(connection, "social_library_item", item_id, "version_promote", actor_user_id, {"retention_days": 180, "version_id": version_id})
            updated = self._library_item_row(connection, item_id)
            return self._library_item_from_row(connection, updated)

    def upload_library_file(self, item_id: int, actor_user_id: int, is_admin: bool, file_name: str, body: bytes) -> LibraryItem:
        clean_name = clean_library_file_name(file_name)
        if not body:
            raise ValueError("arquivo vazio")
        if len(body) > 25 * 1024 * 1024:
            raise ValueError("arquivo excede limite de 25 MB")
        file_kind = _library_file_kind_from_name(clean_name)
        checksum = hashlib.sha256(body).hexdigest()
        validation_status = "quarantined"
        rejection_reason = None
        try:
            _validate_library_upload(clean_name, file_kind, body)
        except ValueError as exc:
            validation_status = "rejected"
            rejection_reason = str(exc)
        extension = Path(clean_name).suffix.lower()
        storage = SocialStorageRepository(self.database_path)
        with connect_database(self.database_path) as connection:
            existing = self._library_item_row(connection, item_id, include_archived=True)
            if existing is None:
                raise ValueError("item de biblioteca não encontrado")
            self._ensure_library_owner(existing, actor_user_id, is_admin)
            storage.ensure_upload_allowed(connection, int(existing["owner_user_id"]), len(body))
            stored = storage.storage.write_quarantine(checksum, extension, body)
            duplicate = connection.execute(
                """
                SELECT id, quarantine_key FROM social_library_files
                WHERE sha256 = ? AND validation_status IN ('quarantined', 'validated')
                ORDER BY id
                LIMIT 1
                """,
                (checksum,),
            ).fetchone()
            cursor = connection.execute(
                """
                INSERT INTO social_library_files (
                    item_id, file_kind, file_name, size_bytes, sha256, validation_status,
                    quarantine_key, uploaded_size_bytes, uploaded_at, rejection_reason, deduplicated_from_file_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
                """,
                (
                    item_id,
                    file_kind,
                    clean_name,
                    len(body),
                    checksum,
                    validation_status,
                    stored.key,
                    len(body),
                    rejection_reason,
                    duplicate["id"] if duplicate is not None else None,
                ),
            )
            action = "upload_rejected" if validation_status == "rejected" else "upload_quarantined"
            self._audit(
                connection,
                "social_library_file",
                int(cursor.lastrowid),
                action,
                actor_user_id,
                {"item_id": item_id, "size_bytes": len(body), "sha256": checksum, "retention_days": 180},
            )
            row = self._library_item_row(connection, item_id)
            return self._library_item_from_row(connection, row)

    def analyze_library_file(self, file_id: int, actor_user_id: int, is_admin: bool) -> LibraryItem:
        with connect_database(self.database_path) as connection:
            file_row = connection.execute(
                """
                SELECT lf.*, li.owner_user_id
                FROM social_library_files lf
                JOIN social_library_items li ON li.id = lf.item_id
                WHERE lf.id = ?
                """,
                (file_id,),
            ).fetchone()
            if file_row is None:
                raise ValueError("arquivo não encontrado")
            self._ensure_library_owner(file_row, actor_user_id, is_admin)
            if file_row["validation_status"] not in {"quarantined", "analyzed", "analysis_failed"}:
                raise ValueError("arquivo precisa estar em quarentena para análise")
            quarantine_key = clean_optional_text(file_row["quarantine_key"])
            if not quarantine_key:
                raise ValueError("arquivo sem objeto de quarentena")
            path = SocialStorageRepository(self.database_path).storage.quarantine_path(quarantine_key)
            if not path.is_file():
                raise ValueError("arquivo de quarentena não encontrado")
            body = path.read_bytes()
            try:
                analysis = analyze_3d_model_bytes(str(file_row["file_name"]), file_row["file_kind"], body)
                status = "analyzed"
                thumbnail = build_analysis_thumbnail_svg(analysis)
            except ValueError as exc:
                analysis = {
                    "status": "failed",
                    "problems": [{"code": "analysis_failed", "severity": "error", "message": str(exc)}],
                }
                status = "analysis_failed"
                thumbnail = None
            connection.execute(
                """
                UPDATE social_library_files
                SET analysis_json = ?, thumbnail_svg = ?, analyzed_at = CURRENT_TIMESTAMP,
                    validation_status = ?, rejection_reason = CASE WHEN ? = 'analysis_failed' THEN ? ELSE rejection_reason END
                WHERE id = ?
                """,
                (json.dumps(analysis, ensure_ascii=False, sort_keys=True), thumbnail, status, status, analysis["problems"][0]["message"] if status == "analysis_failed" else None, file_id),
            )
            self._audit(
                connection,
                "social_library_file",
                file_id,
                "analysis_completed" if status == "analyzed" else "analysis_failed",
                actor_user_id,
                {"retention_days": 180, "status": status},
            )
            row = self._library_item_row(connection, int(file_row["item_id"]))
            return self._library_item_from_row(connection, row)

    def create_community_post(self, slug: str, actor_user_id: int, payload: CommunityPostCreate) -> CommunityFeedItem:
        clean_slug = normalize_slug(slug)
        with connect_database(self.database_path) as connection:
            self.sync_all_communities(connection)
            community = connection.execute("SELECT id, status FROM social_communities WHERE slug = ?", (clean_slug,)).fetchone()
            if community is None:
                raise ValueError("comunidade não encontrada")
            if community["status"] not in {"active", "uncurated"}:
                raise ValueError("comunidade não aceita novas discussões")
            self._ensure_user_exists(connection, actor_user_id)
            cursor = connection.execute(
                """
                INSERT INTO social_feed_items (
                    community_id, author_user_id, content_type, title, body, component, material,
                    firmware_family, problem_tag, attachments_json, visibility, source_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'public', 'user_post')
                """,
                (
                    community["id"],
                    actor_user_id,
                    payload.content_type,
                    payload.title.strip(),
                    payload.body.strip(),
                    clean_optional_text(payload.component),
                    clean_optional_text(payload.material),
                    clean_optional_text(payload.firmware_family),
                    clean_optional_text(payload.problem_tag),
                    json.dumps(payload.attachments, ensure_ascii=False, sort_keys=True),
                ),
            )
            post_id = int(cursor.lastrowid)
            self._audit_discussion(connection, "post", post_id, actor_user_id, "created", {})
            row = connection.execute(FEED_ITEM_SQL + "WHERE f.id = ?", (post_id,)).fetchone()
        return _feed_item_from_row(row)

    def update_post(self, post_id: int, actor_user_id: int, actor_is_admin: bool, payload: CommunityPostUpdate) -> CommunityFeedItem:
        with connect_database(self.database_path) as connection:
            row = self._feed_row_for_update(connection, post_id)
            self._ensure_discussion_permission(connection, row, actor_user_id, actor_is_admin)
            previous = {"title": row["title"], "body": row["body"], "attachments": _json_list_of_dicts(row["attachments_json"])}
            title = payload.title.strip() if payload.title is not None else row["title"]
            body = payload.body.strip() if payload.body is not None else row["body"]
            attachments = payload.attachments if payload.attachments is not None else previous["attachments"]
            connection.execute(
                """
                UPDATE social_feed_items
                SET title = ?, body = ?, attachments_json = ?, edit_count = edit_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (title, body, json.dumps(attachments, ensure_ascii=False, sort_keys=True), post_id),
            )
            self._audit_discussion(connection, "post", post_id, actor_user_id, "updated", previous)
            updated = connection.execute(FEED_ITEM_SQL + "WHERE f.id = ?", (post_id,)).fetchone()
        return _feed_item_from_row(updated)

    def delete_post(self, post_id: int, actor_user_id: int, actor_is_admin: bool) -> None:
        with connect_database(self.database_path) as connection:
            row = self._feed_row_for_update(connection, post_id)
            self._ensure_discussion_permission(connection, row, actor_user_id, actor_is_admin)
            previous = {"title": row["title"], "body": row["body"]}
            connection.execute(
                """
                UPDATE social_feed_items
                SET deleted_at = CURRENT_TIMESTAMP, edit_count = edit_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (post_id,),
            )
            self._audit_discussion(connection, "post", post_id, actor_user_id, "deleted", previous)

    def discussion_detail(self, post_id: int) -> DiscussionDetail | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(FEED_ITEM_SQL + "WHERE f.id = ? AND f.visibility = 'public'", (post_id,)).fetchone()
            if row is None:
                return None
            comment_rows = connection.execute(DISCUSSION_COMMENT_SQL + "WHERE c.feed_item_id = ? ORDER BY c.created_at, c.id", (post_id,)).fetchall()
            reaction_rows = connection.execute(
                """
                SELECT reaction_type, COUNT(*) AS count
                FROM social_discussion_reactions
                WHERE target_type = 'post' AND target_id = ?
                GROUP BY reaction_type
                ORDER BY reaction_type
                """,
                (post_id,),
            ).fetchall()
        return DiscussionDetail(
            post=_feed_item_from_row(row),
            comments=_comment_tree(comment_rows),
            reactions=[DiscussionReactionCount(reaction_type=item["reaction_type"], count=int(item["count"])) for item in reaction_rows],
        )

    def create_comment(self, post_id: int, actor_user_id: int, payload: DiscussionCommentCreate) -> DiscussionComment:
        with connect_database(self.database_path) as connection:
            post = self._feed_row_for_update(connection, post_id)
            if post["deleted_at"] is not None:
                raise ValueError("discussão removida não aceita comentário")
            self._ensure_user_exists(connection, actor_user_id)
            if payload.parent_comment_id is not None:
                parent = connection.execute(
                    "SELECT parent_comment_id, feed_item_id, deleted_at FROM social_discussion_comments WHERE id = ?",
                    (payload.parent_comment_id,),
                ).fetchone()
                if parent is None or parent["feed_item_id"] != post_id or parent["deleted_at"] is not None:
                    raise ValueError("comentário pai inválido")
                if parent["parent_comment_id"] is not None:
                    raise ValueError("respostas aceitam apenas um nível")
            cursor = connection.execute(
                """
                INSERT INTO social_discussion_comments (feed_item_id, author_user_id, parent_comment_id, body, attachments_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    post_id,
                    actor_user_id,
                    payload.parent_comment_id,
                    payload.body.strip(),
                    json.dumps(payload.attachments, ensure_ascii=False, sort_keys=True),
                ),
            )
            comment_id = int(cursor.lastrowid)
            self._audit_discussion(connection, "comment", comment_id, actor_user_id, "created", {})
            row = connection.execute(DISCUSSION_COMMENT_SQL + "WHERE c.id = ?", (comment_id,)).fetchone()
        return _comment_from_row(row)

    def update_comment(self, comment_id: int, actor_user_id: int, actor_is_admin: bool, payload: DiscussionCommentUpdate) -> DiscussionComment:
        with connect_database(self.database_path) as connection:
            row = self._comment_row_for_update(connection, comment_id)
            post = self._feed_row_for_update(connection, int(row["feed_item_id"]))
            self._ensure_comment_permission(connection, row, post, actor_user_id, actor_is_admin)
            previous = {"body": row["body"], "attachments": _json_list_of_dicts(row["attachments_json"])}
            connection.execute(
                """
                UPDATE social_discussion_comments
                SET body = ?, attachments_json = ?, edit_count = edit_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (payload.body.strip(), json.dumps(payload.attachments, ensure_ascii=False, sort_keys=True), comment_id),
            )
            self._audit_discussion(connection, "comment", comment_id, actor_user_id, "updated", previous)
            updated = connection.execute(DISCUSSION_COMMENT_SQL + "WHERE c.id = ?", (comment_id,)).fetchone()
        return _comment_from_row(updated)

    def delete_comment(self, comment_id: int, actor_user_id: int, actor_is_admin: bool) -> None:
        with connect_database(self.database_path) as connection:
            row = self._comment_row_for_update(connection, comment_id)
            post = self._feed_row_for_update(connection, int(row["feed_item_id"]))
            self._ensure_comment_permission(connection, row, post, actor_user_id, actor_is_admin)
            connection.execute(
                """
                UPDATE social_discussion_comments
                SET deleted_at = CURRENT_TIMESTAMP, edit_count = edit_count + 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (comment_id,),
            )
            self._audit_discussion(connection, "comment", comment_id, actor_user_id, "deleted", {"body": row["body"]})

    def set_reaction(self, target_type: Literal["post", "comment"], target_id: int, actor_user_id: int, reaction_type: DiscussionReactionType, active: bool) -> None:
        with connect_database(self.database_path) as connection:
            self._ensure_user_exists(connection, actor_user_id)
            if target_type == "post":
                row = self._feed_row_for_update(connection, target_id)
                if row["deleted_at"] is not None:
                    raise ValueError("discussão removida não aceita reação")
            else:
                row = self._comment_row_for_update(connection, target_id)
                if row["deleted_at"] is not None:
                    raise ValueError("comentário removido não aceita reação")
            if active:
                connection.execute(
                    """
                    INSERT INTO social_discussion_reactions (target_type, target_id, user_id, reaction_type)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(target_type, target_id, user_id, reaction_type) DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                    """,
                    (target_type, target_id, actor_user_id, reaction_type),
                )
            else:
                connection.execute(
                    """
                    DELETE FROM social_discussion_reactions
                    WHERE target_type = ? AND target_id = ? AND user_id = ? AND reaction_type = ?
                    """,
                    (target_type, target_id, actor_user_id, reaction_type),
                )

    def mark_solution(self, post_id: int, comment_id: int | None, actor_user_id: int, actor_is_admin: bool) -> CommunityFeedItem:
        with connect_database(self.database_path) as connection:
            post = self._feed_row_for_update(connection, post_id)
            self._ensure_discussion_permission(connection, post, actor_user_id, actor_is_admin)
            if post["content_type"] != "question":
                raise ValueError("solução só pode ser marcada em dúvida")
            if comment_id is not None:
                comment = connection.execute(
                    "SELECT id, feed_item_id, deleted_at FROM social_discussion_comments WHERE id = ?",
                    (comment_id,),
                ).fetchone()
                if comment is None or comment["feed_item_id"] != post_id or comment["deleted_at"] is not None:
                    raise ValueError("comentário de solução inválido")
            connection.execute(
                """
                UPDATE social_feed_items
                SET solution_comment_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (comment_id, post_id),
            )
            self._audit_discussion(
                connection,
                "post",
                post_id,
                actor_user_id,
                "solution_marked" if comment_id is not None else "solution_cleared",
                {"previous_solution_comment_id": post["solution_comment_id"]},
            )
            updated = connection.execute(FEED_ITEM_SQL + "WHERE f.id = ?", (post_id,)).fetchone()
        return _feed_item_from_row(updated)

    def set_relationship(self, actor_user_id: int, target_user_id: int, relation_type: RelationshipType, status: RelationshipStatus) -> RelationshipRecord:
        if actor_user_id == target_user_id:
            raise ValueError("relação consigo mesmo não é permitida")
        with connect_database(self.database_path) as connection:
            self._ensure_user_exists(connection, target_user_id)
            if relation_type != "block" and self._is_blocked(connection, actor_user_id, target_user_id):
                raise PermissionError("relação bloqueada por bloqueio social")
            if relation_type == "block":
                connection.execute(
                    """
                    UPDATE social_relationships
                    SET status = 'ended', ended_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE ((actor_user_id = ? AND target_user_id = ?) OR (actor_user_id = ? AND target_user_id = ?))
                      AND relation_type IN ('follow', 'friend')
                      AND status != 'ended'
                    """,
                    (actor_user_id, target_user_id, target_user_id, actor_user_id),
                )
                self._audit_relationship(connection, actor_user_id, target_user_id, "block_ended_existing_relations")
            if relation_type == "friend" and status == "pending":
                accepted = connection.execute(
                    """
                    SELECT 1 FROM social_relationships
                    WHERE relation_type = 'friend'
                      AND status = 'accepted'
                      AND ((actor_user_id = ? AND target_user_id = ?) OR (actor_user_id = ? AND target_user_id = ?))
                    """,
                    (actor_user_id, target_user_id, target_user_id, actor_user_id),
                ).fetchone()
                if accepted is not None:
                    return self._relationship(actor_user_id, target_user_id, "friend")
            connection.execute(
                """
                INSERT INTO social_relationships (actor_user_id, target_user_id, relation_type, status)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(actor_user_id, target_user_id, relation_type) DO UPDATE SET
                    status = excluded.status,
                    ended_at = CASE WHEN excluded.status = 'ended' THEN CURRENT_TIMESTAMP ELSE NULL END,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (actor_user_id, target_user_id, relation_type, status),
            )
            self._audit_relationship(connection, actor_user_id, target_user_id, f"{relation_type}_{status}")
        return self._relationship(actor_user_id, target_user_id, relation_type)

    def accept_friend(self, actor_user_id: int, requester_user_id: int) -> RelationshipRecord:
        if actor_user_id == requester_user_id:
            raise ValueError("relação consigo mesmo não é permitida")
        with connect_database(self.database_path) as connection:
            if self._is_blocked(connection, actor_user_id, requester_user_id):
                raise PermissionError("relação bloqueada por bloqueio social")
            pending = connection.execute(
                """
                SELECT 1 FROM social_relationships
                WHERE actor_user_id = ? AND target_user_id = ? AND relation_type = 'friend' AND status = 'pending'
                """,
                (requester_user_id, actor_user_id),
            ).fetchone()
            if pending is None:
                raise ValueError("solicitação de amizade não encontrada")
            connection.execute(
                """
                UPDATE social_relationships
                SET status = 'accepted', updated_at = CURRENT_TIMESTAMP
                WHERE actor_user_id = ? AND target_user_id = ? AND relation_type = 'friend'
                """,
                (requester_user_id, actor_user_id),
            )
            connection.execute(
                """
                INSERT INTO social_relationships (actor_user_id, target_user_id, relation_type, status)
                VALUES (?, ?, 'friend', 'accepted')
                ON CONFLICT(actor_user_id, target_user_id, relation_type) DO UPDATE SET
                    status = 'accepted', ended_at = NULL, updated_at = CURRENT_TIMESTAMP
                """,
                (actor_user_id, requester_user_id),
            )
            self._audit_relationship(connection, actor_user_id, requester_user_id, "friend_accepted")
        return self._relationship(actor_user_id, requester_user_id, "friend")

    def reject_friend(self, actor_user_id: int, requester_user_id: int) -> None:
        if actor_user_id == requester_user_id:
            raise ValueError("relação consigo mesmo não é permitida")
        with connect_database(self.database_path) as connection:
            self._ensure_user_exists(connection, requester_user_id)
            connection.execute(
                """
                UPDATE social_relationships
                SET status = 'ended', ended_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE actor_user_id = ? AND target_user_id = ?
                  AND relation_type = 'friend'
                  AND status = 'pending'
                """,
                (requester_user_id, actor_user_id),
            )
            self._audit_relationship(connection, actor_user_id, requester_user_id, "friend_rejected")

    def cancel_friend_request(self, actor_user_id: int, target_user_id: int) -> None:
        if actor_user_id == target_user_id:
            raise ValueError("relação consigo mesmo não é permitida")
        with connect_database(self.database_path) as connection:
            self._ensure_user_exists(connection, target_user_id)
            connection.execute(
                """
                UPDATE social_relationships
                SET status = 'ended', ended_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE actor_user_id = ? AND target_user_id = ?
                  AND relation_type = 'friend'
                  AND status = 'pending'
                """,
                (actor_user_id, target_user_id),
            )
            self._audit_relationship(connection, actor_user_id, target_user_id, "friend_request_cancelled")

    def unfriend(self, actor_user_id: int, target_user_id: int) -> None:
        if actor_user_id == target_user_id:
            raise ValueError("relação consigo mesmo não é permitida")
        with connect_database(self.database_path) as connection:
            self._ensure_user_exists(connection, target_user_id)
            connection.execute(
                """
                UPDATE social_relationships
                SET status = 'ended', ended_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE relation_type = 'friend'
                  AND status = 'accepted'
                  AND ((actor_user_id = ? AND target_user_id = ?) OR (actor_user_id = ? AND target_user_id = ?))
                """,
                (actor_user_id, target_user_id, target_user_id, actor_user_id),
            )
            self._audit_relationship(connection, actor_user_id, target_user_id, "friend_ended")

    def relationship_summary(self, user_id: int) -> RelationshipSummary:
        with connect_database(self.database_path) as connection:
            outgoing = connection.execute(RELATIONSHIP_SQL + " WHERE r.actor_user_id = ? AND r.status != 'ended'", (user_id,)).fetchall()
            incoming = connection.execute(
                RELATIONSHIP_INCOMING_SQL + " WHERE r.target_user_id = ? AND r.status != 'ended'",
                (user_id,),
            ).fetchall()
        outgoing_records = [_relationship_from_row(row) for row in outgoing]
        incoming_records = [_relationship_from_row(row) for row in incoming]
        return RelationshipSummary(
            following=[item for item in outgoing_records if item.relation_type == "follow" and item.status == "active"],
            followers=[item for item in incoming_records if item.relation_type == "follow" and item.status == "active"],
            friends=[item for item in outgoing_records if item.relation_type == "friend" and item.status == "accepted"],
            blocked=[item for item in outgoing_records if item.relation_type == "block" and item.status == "active"],
            pending_friend_requests=[item for item in incoming_records if item.relation_type == "friend" and item.status == "pending"],
            sent_friend_requests=[item for item in outgoing_records if item.relation_type == "friend" and item.status == "pending"],
        )

    def sync_all_communities(self, connection) -> None:
        manufacturer_rows = connection.execute("SELECT id, slug, name, trust_state FROM catalog_manufacturers WHERE trust_state != 'blocked'").fetchall()
        model_rows = connection.execute(
            """
            SELECT m.id, m.slug, m.name, m.trust_state AS model_trust_state,
                   mf.id AS manufacturer_id, mf.slug AS manufacturer_slug,
                   mf.name AS manufacturer_name, mf.trust_state AS manufacturer_trust_state
            FROM catalog_printer_models m
            JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
            WHERE m.trust_state != 'blocked' AND mf.trust_state != 'blocked'
            """
        ).fetchall()
        variant_rows = connection.execute(
            """
            SELECT v.id, v.slug, v.name, v.trust_state AS variant_trust_state,
                   m.id AS model_id, mf.id AS manufacturer_id,
                   m.slug AS model_slug, mf.slug AS manufacturer_slug, m.trust_state AS model_trust_state,
                   mf.trust_state AS manufacturer_trust_state
            FROM catalog_printer_variants v
            JOIN catalog_printer_models m ON m.id = v.model_id
            JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
            WHERE v.trust_state != 'blocked' AND m.trust_state != 'blocked' AND mf.trust_state != 'blocked'
            """
        ).fetchall()
        for row in manufacturer_rows:
            self._upsert_community(
                connection,
                f"maker-{row['slug']}",
                str(row["name"]),
                "manufacturer",
                row["id"],
                None,
                None,
                _community_status_from_trust(row["trust_state"]),
            )
        for row in model_rows:
            status = _community_status_from_trust(row["model_trust_state"], row["manufacturer_trust_state"])
            self._upsert_community(connection, f"model-{row['manufacturer_slug']}-{row['slug']}", f"{row['manufacturer_name']} {row['name']}", "model", row["manufacturer_id"], row["id"], None, status)
        for row in variant_rows:
            status = _community_status_from_trust(row["variant_trust_state"], row["model_trust_state"], row["manufacturer_trust_state"])
            self._upsert_community(connection, f"variant-{row['manufacturer_slug']}-{row['model_slug']}-{row['slug']}", str(row["name"]), "variant", row["manufacturer_id"], row["model_id"], row["id"], status)

    def sync_default_feed_items(self, connection) -> None:
        rows = connection.execute(
            """
            SELECT c.id, c.name, c.status, mf.name AS manufacturer_name, m.name AS model_name,
                   v.name AS variant_name, v.components_json, v.firmware_family
            FROM social_communities c
            LEFT JOIN catalog_manufacturers mf ON mf.id = c.manufacturer_id
            LEFT JOIN catalog_printer_models m ON m.id = c.model_id
            LEFT JOIN catalog_printer_variants v ON v.id = c.variant_id
            WHERE c.status IN ('active', 'uncurated')
            """
        ).fetchall()
        for row in rows:
            source_id = f"community:{row['id']}:curation"
            context = " / ".join(str(row[key]) for key in ("manufacturer_name", "model_name", "variant_name") if row[key])
            body = f"Feed técnico para {context or row['name']}. Use filtros por componente, material, firmware, problema e tipo de conteúdo."
            connection.execute(
                """
                INSERT INTO social_feed_items (
                    community_id, content_type, title, body, component, firmware_family,
                    pinned, visibility, source_type, source_id
                )
                VALUES (?, 'curation_notice', 'Contexto técnico da comunidade', ?, ?, ?, 1, 'public', 'catalog_curation', ?)
                ON CONFLICT(source_type, source_id) DO UPDATE SET
                    body = excluded.body,
                    component = excluded.component,
                    firmware_family = excluded.firmware_family,
                    pinned = excluded.pinned,
                    visibility = excluded.visibility,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (row["id"], body, _primary_component(row["components_json"]), row["firmware_family"], source_id),
            )

    def sync_communities_for_user(self, connection, user_id: int) -> None:
        self.sync_all_communities(connection)
        connection.execute(
            """
            UPDATE social_community_members
            SET active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id,),
        )
        rows = connection.execute(
            """
            SELECT p.id AS printer_id, v.id AS variant_id, m.id AS model_id, mf.id AS manufacturer_id
            FROM printers p
            JOIN social_profiles sp ON sp.user_id = p.owner_user_id
            JOIN catalog_printer_variants v ON v.id = p.catalog_variant_id
            JOIN catalog_printer_models m ON m.id = v.model_id
            JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
            WHERE p.owner_user_id = ?
              AND p.public_profile_enabled = 1
              AND sp.visibility = 'public'
            """,
            (user_id,),
        ).fetchall()
        for row in rows:
            community_rows = connection.execute(
                """
                SELECT id FROM social_communities
                WHERE manufacturer_id = ?
                  AND (model_id IS NULL OR model_id = ?)
                  AND (variant_id IS NULL OR variant_id = ?)
                  AND status IN ('active', 'uncurated')
                """,
                (row["manufacturer_id"], row["model_id"], row["variant_id"]),
            ).fetchall()
            for community in community_rows:
                connection.execute(
                    """
                    INSERT INTO social_community_members (community_id, user_id, printer_id, source, active)
                    VALUES (?, ?, ?, 'public_printer', 1)
                    ON CONFLICT(community_id, user_id, printer_id) DO UPDATE SET
                        active = 1,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (community["id"], user_id, row["printer_id"]),
                )

    def _upsert_community(self, connection, slug: str, name: str, scope: str, manufacturer_id: int | None, model_id: int | None, variant_id: int | None, status: CommunityStatus) -> None:
        connection.execute(
            """
            INSERT INTO social_communities (slug, name, scope, manufacturer_id, model_id, variant_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                name = excluded.name,
                status = CASE
                    WHEN social_communities.status = 'merged' THEN social_communities.status
                    ELSE excluded.status
                END,
                updated_at = CURRENT_TIMESTAMP
            """,
            (slug, name, scope, manufacturer_id, model_id, variant_id, status),
        )

    def _community_filters(
        self,
        *,
        manufacturer: str | None,
        model: str | None,
        variant: str | None,
        component: str | None,
    ) -> tuple[list[str], list[object]]:
        clauses: list[str] = []
        parameters: list[object] = []
        like_filters = [
            ("mf.slug || ' ' || mf.name", manufacturer),
            ("m.slug || ' ' || COALESCE(m.name, '')", model),
            ("v.slug || ' ' || COALESCE(v.name, '')", variant),
            ("COALESCE(v.components_json, '')", component),
        ]
        for expression, value in like_filters:
            cleaned = clean_optional_text(value)
            if cleaned:
                clauses.append(f"LOWER({expression}) LIKE ?")
                parameters.append(f"%{cleaned.lower()}%")
        return clauses, parameters

    def _relationship(self, actor_user_id: int, target_user_id: int, relation_type: RelationshipType) -> RelationshipRecord:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                RELATIONSHIP_SQL + " WHERE r.actor_user_id = ? AND r.target_user_id = ? AND r.relation_type = ?",
                (actor_user_id, target_user_id, relation_type),
            ).fetchone()
        if row is None:
            raise RuntimeError("relação social não persistida")
        return _relationship_from_row(row)

    def _unique_slug(self, connection, value: str, user_id: int) -> str:
        base = normalize_slug(value)
        slug = base
        suffix = 2
        while connection.execute("SELECT 1 FROM social_profiles WHERE slug = ? AND user_id != ?", (slug, user_id)).fetchone() or connection.execute(
            "SELECT 1 FROM social_profile_slug_history WHERE slug = ? AND user_id != ?",
            (slug, user_id),
        ).fetchone():
            slug = f"{base}-{suffix}"
            suffix += 1
        return slug

    def _profile_with_reserved_slugs(self, connection, row) -> PublicProfile:
        reserved = connection.execute(
            """
            SELECT slug FROM social_profile_slug_history
            WHERE user_id = ?
            ORDER BY replaced_at DESC, id DESC
            """,
            (row["user_id"],),
        ).fetchall()
        return _profile_from_row(row).model_copy(update={"reserved_slugs": [str(item["slug"]) for item in reserved]})

    def _is_blocked(self, connection, left_user_id: int, right_user_id: int) -> bool:
        row = connection.execute(
            """
            SELECT 1 FROM social_relationships
            WHERE relation_type = 'block'
              AND status = 'active'
              AND ((actor_user_id = ? AND target_user_id = ?) OR (actor_user_id = ? AND target_user_id = ?))
            """,
            (left_user_id, right_user_id, right_user_id, left_user_id),
        ).fetchone()
        return row is not None

    def _ensure_user_exists(self, connection, user_id: int) -> None:
        if connection.execute("SELECT 1 FROM auth_users WHERE id = ?", (user_id,)).fetchone() is None:
            raise ValueError("usuário não encontrado")

    def _feed_row_for_update(self, connection, post_id: int):
        row = connection.execute(FEED_ITEM_SQL + "WHERE f.id = ?", (post_id,)).fetchone()
        if row is None:
            raise ValueError("discussão não encontrada")
        return row

    def _comment_row_for_update(self, connection, comment_id: int):
        row = connection.execute(DISCUSSION_COMMENT_SQL + "WHERE c.id = ?", (comment_id,)).fetchone()
        if row is None:
            raise ValueError("comentário não encontrado")
        return row

    def _ensure_discussion_permission(self, connection, post_row, actor_user_id: int, actor_is_admin: bool) -> None:
        if actor_is_admin or post_row["author_user_id"] == actor_user_id:
            return
        if self._is_community_moderator(connection, int(post_row["community_id"]), actor_user_id):
            return
        raise PermissionError("ação permitida apenas para autor, moderador ou administrador")

    def _ensure_comment_permission(self, connection, comment_row, post_row, actor_user_id: int, actor_is_admin: bool) -> None:
        if actor_is_admin or comment_row["author_user_id"] == actor_user_id:
            return
        if self._is_community_moderator(connection, int(post_row["community_id"]), actor_user_id):
            return
        raise PermissionError("ação permitida apenas para autor, moderador ou administrador")

    def _is_community_moderator(self, connection, community_id: int, user_id: int) -> bool:
        row = connection.execute(
            """
            SELECT 1 FROM social_community_members
            WHERE community_id = ? AND user_id = ? AND active = 1
            LIMIT 1
            """,
            (community_id, user_id),
        ).fetchone()
        return row is not None

    def _ensure_profile_for_user(self, connection, user_id: int) -> None:
        if connection.execute("SELECT 1 FROM social_profiles WHERE user_id = ?", (user_id,)).fetchone() is not None:
            return
        user = connection.execute("SELECT email, display_name FROM auth_users WHERE id = ?", (user_id,)).fetchone()
        if user is None:
            raise ValueError("usuário não encontrado")
        display_name = clean_optional_text(user["display_name"]) or str(user["email"]).split("@")[0]
        connection.execute(
            "INSERT INTO social_profiles (user_id, slug, display_name) VALUES (?, ?, ?)",
            (user_id, self._unique_slug(connection, display_name, user_id), display_name),
        )

    def _library_community_id(self, connection, community_slug: str | None, visibility: LibraryVisibility) -> int | None:
        if visibility == "community" and not community_slug:
            raise ValueError("visibilidade de comunidade exige comunidade")
        if not community_slug:
            return None
        community = connection.execute(
            "SELECT id, status FROM social_communities WHERE slug = ?",
            (normalize_slug(community_slug),),
        ).fetchone()
        if community is None:
            raise ValueError("comunidade não encontrada")
        if community["status"] not in {"active", "uncurated"}:
            raise ValueError("comunidade não aceita novos arquivos")
        return int(community["id"])

    def _ensure_library_variant(self, connection, variant_id: int | None) -> None:
        if variant_id is None:
            return
        row = connection.execute(
            "SELECT id FROM catalog_printer_variants WHERE id = ? AND trust_state NOT IN ('blocked', 'obsolete')",
            (variant_id,),
        ).fetchone()
        if row is None:
            raise ValueError("variante de catálogo inválida")

    def _ensure_library_remix_source(self, connection, remix_source_item_id: int | None, current_item_id: int | None = None) -> None:
        if remix_source_item_id is None:
            return
        if current_item_id is not None and remix_source_item_id == current_item_id:
            raise ValueError("remix não pode referenciar o próprio item")
        row = connection.execute(
            "SELECT id FROM social_library_items WHERE id = ? AND status = 'active'",
            (remix_source_item_id,),
        ).fetchone()
        if row is None:
            raise ValueError("item de origem do remix não encontrado")

    def _ensure_library_item_publishable(
        self,
        connection,
        visibility: LibraryVisibility,
        license_value: LibraryLicense,
        original_author_name: str | None,
        publication_terms_accepted: bool,
        remix_source_item_id: int | None,
        *,
        current_item_id: int | None = None,
    ) -> None:
        self._ensure_library_remix_source(connection, remix_source_item_id, current_item_id)
        if visibility not in {"public", "community"}:
            return
        if not clean_optional_text(original_author_name):
            raise ValueError("publicação pública exige autoria declarada")
        if not license_value:
            raise ValueError("publicação pública exige licença")
        if not publication_terms_accepted:
            raise ValueError("publicação pública exige aceite dos termos")

    def _replace_library_files(self, connection, item_id: int, files: list[LibraryFileMetadata]) -> None:
        if not files:
            raise ValueError("item de biblioteca exige pelo menos um arquivo")
        connection.execute("DELETE FROM social_library_files WHERE item_id = ?", (item_id,))
        for file in files:
            connection.execute(
                """
                INSERT INTO social_library_files (
                    item_id, file_kind, file_name, original_url, size_bytes, sha256, validation_status
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    file.file_kind,
                    file.file_name,
                    clean_optional_text(file.original_url),
                    file.size_bytes,
                    file.sha256,
                    "metadata_only",
                ),
            )

    def _create_library_version_snapshot(
        self,
        connection,
        item_id: int,
        actor_user_id: int,
        version_label: str,
        changelog: str,
        *,
        make_current: bool,
    ) -> None:
        files = self._library_file_snapshot_rows(connection, item_id)
        if not files:
            raise ValueError("versão exige pelo menos um arquivo")
        metadata = connection.execute(
            """
            SELECT title, description, visibility, component, material_suggestion,
                   supports_required, orientation_notes, license, original_author_name,
                   source_url, attribution_text, remix_source_item_id
            FROM social_library_items
            WHERE id = ?
            """,
            (item_id,),
        ).fetchone()
        if metadata is None:
            raise ValueError("item de biblioteca não encontrado")
        if make_current:
            connection.execute("UPDATE social_library_versions SET is_current = 0 WHERE item_id = ?", (item_id,))
        connection.execute(
            """
            INSERT INTO social_library_versions (
                item_id, version_label, changelog, files_snapshot_json, metadata_snapshot_json,
                created_by_user_id, is_current
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item_id,
                clean_optional_text(version_label) or "v1",
                clean_discussion_text(changelog),
                json.dumps(files, ensure_ascii=False, sort_keys=True),
                json.dumps({key: metadata[key] for key in metadata.keys()}, ensure_ascii=False, sort_keys=True),
                actor_user_id,
                1 if make_current else 0,
            ),
        )
        if make_current:
            connection.execute(
                "UPDATE social_library_items SET version_label = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (clean_optional_text(version_label) or "v1", item_id),
            )

    def _library_file_snapshot_rows(self, connection, item_id: int) -> list[dict[str, object]]:
        rows = connection.execute(
            """
            SELECT file_kind, file_name, original_url, size_bytes, sha256, validation_status,
                   storage_key, quarantine_key, uploaded_size_bytes, rejection_reason,
                   deduplicated_from_file_id, analysis_json, thumbnail_svg, analyzed_at
            FROM social_library_files
            WHERE item_id = ?
            ORDER BY id
            """,
            (item_id,),
        ).fetchall()
        return [
            {
                "file_kind": row["file_kind"],
                "file_name": row["file_name"],
                "original_url": row["original_url"],
                "size_bytes": row["size_bytes"],
                "sha256": row["sha256"],
                "validation_status": row["validation_status"],
                "storage_key": row["storage_key"],
                "quarantine_key": row["quarantine_key"],
                "uploaded_size_bytes": row["uploaded_size_bytes"],
                "rejection_reason": row["rejection_reason"],
                "deduplicated_from_file_id": row["deduplicated_from_file_id"],
                "analysis_json": row["analysis_json"],
                "thumbnail_svg": row["thumbnail_svg"],
                "analyzed_at": row["analyzed_at"],
            }
            for row in rows
        ]

    def _restore_library_files_from_snapshot(self, connection, item_id: int, files_snapshot_json: str) -> None:
        parsed_files = json.loads(files_snapshot_json or "[]")
        files = [file for file in parsed_files if isinstance(file, dict)] if isinstance(parsed_files, list) else []
        if not files:
            raise ValueError("versão sem arquivos")
        connection.execute("DELETE FROM social_library_files WHERE item_id = ?", (item_id,))
        for file in files:
            connection.execute(
                """
                INSERT INTO social_library_files (
                    item_id, file_kind, file_name, original_url, size_bytes, sha256, validation_status,
                    storage_key, quarantine_key, uploaded_size_bytes, rejection_reason,
                    deduplicated_from_file_id, analysis_json, thumbnail_svg, analyzed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item_id,
                    file.get("file_kind"),
                    file.get("file_name"),
                    clean_optional_text(file.get("original_url")),
                    file.get("size_bytes"),
                    file.get("sha256"),
                    file.get("validation_status") or "metadata_only",
                    clean_optional_text(file.get("storage_key")),
                    clean_optional_text(file.get("quarantine_key")),
                    file.get("uploaded_size_bytes"),
                    clean_optional_text(file.get("rejection_reason")),
                    file.get("deduplicated_from_file_id"),
                    clean_optional_text(file.get("analysis_json")) or "{}",
                    clean_optional_text(file.get("thumbnail_svg")),
                    clean_optional_text(file.get("analyzed_at")),
                ),
            )

    def _library_organizer_summary(self, connection, actor_user_id: int) -> LibraryOrganizerSummary:
        favorite_rows = connection.execute(
            LIBRARY_ITEM_SQL
            + """
            WHERE fav.user_id = ? AND li.status = 'active'
            GROUP BY li.id
            ORDER BY fav.created_at DESC
            LIMIT 60
            """,
            (actor_user_id,),
        ).fetchall()
        favorites = [
            self._library_item_from_row(connection, row).model_copy(update={"viewer_favorite": True})
            for row in favorite_rows
            if self._can_view_library_item(connection, row, actor_user_id)
        ]
        return LibraryOrganizerSummary(
            favorites=favorites,
            collections=self._library_collections(connection, actor_user_id),
            print_lists=self._print_lists(connection, actor_user_id),
            downloads=self._library_download_history(connection, actor_user_id),
        )

    def _library_collections(self, connection, actor_user_id: int) -> list[LibraryCollection]:
        rows = connection.execute(
            """
            SELECT col.id, col.owner_user_id, col.community_id, c.slug AS community_slug, c.name AS community_name,
                   col.name, col.description, col.visibility, col.created_at, col.updated_at,
                   COUNT(ci.item_id) AS item_count
            FROM social_library_collections col
            LEFT JOIN social_communities c ON c.id = col.community_id
            LEFT JOIN social_library_collection_items ci ON ci.collection_id = col.id
            WHERE col.owner_user_id = ? AND col.status = 'active'
            GROUP BY col.id
            ORDER BY col.updated_at DESC, col.id DESC
            LIMIT 50
            """,
            (actor_user_id,),
        ).fetchall()
        return [
            LibraryCollection(
                id=int(row["id"]),
                owner_user_id=int(row["owner_user_id"]),
                community_id=row["community_id"],
                community_slug=row["community_slug"],
                community_name=row["community_name"],
                name=str(row["name"]),
                description=str(row["description"] or ""),
                visibility=row["visibility"],
                item_count=int(row["item_count"] or 0),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    def _print_lists(self, connection, actor_user_id: int) -> list[PrintList]:
        rows = connection.execute(
            """
            SELECT pl.id, pl.owner_user_id, pl.printer_id, p.name AS printer_name,
                   pl.name, pl.status, pl.created_at, pl.updated_at
            FROM social_print_lists pl
            LEFT JOIN printers p ON p.id = pl.printer_id
            WHERE pl.owner_user_id = ? AND pl.status = 'active'
            ORDER BY pl.updated_at DESC, pl.id DESC
            LIMIT 50
            """,
            (actor_user_id,),
        ).fetchall()
        return [
            PrintList(
                id=int(row["id"]),
                owner_user_id=int(row["owner_user_id"]),
                printer_id=row["printer_id"],
                printer_name=row["printer_name"],
                name=str(row["name"]),
                status=row["status"],
                items=self._print_list_items(connection, int(row["id"])),
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    def _print_list_items(self, connection, print_list_id: int) -> list[PrintListItem]:
        rows = connection.execute(
            """
            SELECT pli.id, pli.item_id, pli.version_id, li.title AS item_title,
                   v.version_label, pli.status, pli.notes, pli.created_at, pli.updated_at
            FROM social_print_list_items pli
            JOIN social_library_items li ON li.id = pli.item_id
            JOIN social_library_versions v ON v.id = pli.version_id
            WHERE pli.print_list_id = ?
            ORDER BY pli.updated_at DESC, pli.id DESC
            LIMIT 100
            """,
            (print_list_id,),
        ).fetchall()
        return [
            PrintListItem(
                id=int(row["id"]),
                item_id=int(row["item_id"]),
                version_id=int(row["version_id"]),
                item_title=str(row["item_title"]),
                version_label=str(row["version_label"]),
                status=row["status"],
                notes=row["notes"],
                created_at=str(row["created_at"]),
                updated_at=str(row["updated_at"]),
            )
            for row in rows
        ]

    def _library_download_history(self, connection, actor_user_id: int) -> list[LibraryDownloadHistoryItem]:
        rows = connection.execute(
            """
            SELECT d.id, d.item_id, d.version_id, li.title, v.version_label, d.created_at
            FROM social_library_downloads d
            JOIN social_library_items li ON li.id = d.item_id
            LEFT JOIN social_library_versions v ON v.id = d.version_id
            WHERE d.user_id = ?
            ORDER BY d.created_at DESC, d.id DESC
            LIMIT 80
            """,
            (actor_user_id,),
        ).fetchall()
        return [
            LibraryDownloadHistoryItem(
                id=int(row["id"]),
                item_id=int(row["item_id"]),
                version_id=row["version_id"],
                title=str(row["title"]),
                version_label=row["version_label"],
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def _collection_community_id(self, connection, community_slug: str | None, visibility: LibraryCollectionVisibility) -> int | None:
        if visibility == "community" and not community_slug:
            raise ValueError("coleção de comunidade exige comunidade")
        if not community_slug:
            return None
        return self._library_community_id(connection, community_slug, "community")

    def _library_collection_row(self, connection, collection_id: int):
        return connection.execute(
            "SELECT id, owner_user_id FROM social_library_collections WHERE id = ? AND status = 'active'",
            (collection_id,),
        ).fetchone()

    def _print_list_row(self, connection, print_list_id: int):
        return connection.execute(
            "SELECT id, owner_user_id FROM social_print_lists WHERE id = ? AND status = 'active'",
            (print_list_id,),
        ).fetchone()

    def _ensure_collection_owner(self, row, actor_user_id: int) -> None:
        if int(row["owner_user_id"]) != actor_user_id:
            raise PermissionError("ação permitida apenas para dono da coleção")

    def _ensure_print_list_owner(self, row, actor_user_id: int) -> None:
        if int(row["owner_user_id"]) != actor_user_id:
            raise PermissionError("ação permitida apenas para dono da lista")

    def _ensure_print_list_printer(self, connection, actor_user_id: int, printer_id: int | None) -> None:
        if printer_id is None:
            return
        row = connection.execute(
            "SELECT id FROM printers WHERE id = ? AND owner_user_id = ?",
            (printer_id, actor_user_id),
        ).fetchone()
        if row is None:
            raise ValueError("impressora não encontrada para a lista")

    def _current_library_version_id(self, connection, item_id: int) -> int:
        row = connection.execute(
            "SELECT id FROM social_library_versions WHERE item_id = ? AND is_current = 1 ORDER BY id DESC LIMIT 1",
            (item_id,),
        ).fetchone()
        if row is None:
            raise ValueError("arquivo sem versão atual")
        return int(row["id"])

    def _ensure_library_version(self, connection, item_id: int, version_id: int) -> None:
        row = connection.execute(
            "SELECT id FROM social_library_versions WHERE item_id = ? AND id = ?",
            (item_id, version_id),
        ).fetchone()
        if row is None:
            raise ValueError("versão não encontrada")

    def _library_item_row(self, connection, item_id: int, *, include_archived: bool = False):
        status_clause = "" if include_archived else " AND li.status = 'active'"
        return connection.execute(
            LIBRARY_ITEM_SQL
            + f"""
            WHERE li.id = ?{status_clause}
            GROUP BY li.id
            """,
            (item_id,),
        ).fetchone()

    def _library_item_from_row(self, connection, row) -> LibraryItem:
        file_rows = connection.execute(
            """
            SELECT id, file_kind, file_name, original_url, size_bytes, sha256, validation_status,
                   storage_key, quarantine_key, uploaded_size_bytes, rejection_reason, deduplicated_from_file_id,
                   analysis_json, thumbnail_svg, analyzed_at
            FROM social_library_files
            WHERE item_id = ?
            ORDER BY id
            """,
            (row["id"],),
        ).fetchall()
        version_rows = connection.execute(
            """
            SELECT v.id, v.item_id, v.version_label, v.changelog, v.files_snapshot_json,
                   v.metadata_snapshot_json, v.created_by_user_id, v.is_current, v.created_at,
                   COUNT(DISTINCT d.id) AS download_count
            FROM social_library_versions v
            LEFT JOIN social_library_downloads d ON d.version_id = v.id
            WHERE v.item_id = ?
            GROUP BY v.id
            ORDER BY v.is_current DESC, v.created_at DESC, v.id DESC
            """,
            (row["id"],),
        ).fetchall()
        return _library_item_from_row(row, file_rows, version_rows)

    def _can_view_library_item(self, connection, row, viewer_user_id: int | None) -> bool:
        if row["status"] != "active":
            return False
        owner_id = int(row["owner_user_id"])
        if viewer_user_id == owner_id:
            return True
        if viewer_user_id is not None and self._is_blocked(connection, owner_id, viewer_user_id):
            return False
        if row["visibility"] in {"public", "community"}:
            return True
        if row["visibility"] == "friends" and viewer_user_id is not None:
            return self._are_friends(connection, owner_id, viewer_user_id)
        return False

    def _ensure_library_owner(self, row, actor_user_id: int, is_admin: bool) -> None:
        if is_admin or int(row["owner_user_id"]) == actor_user_id:
            return
        raise PermissionError("ação permitida apenas para dono do arquivo ou administrador")

    def _are_friends(self, connection, left_user_id: int, right_user_id: int) -> bool:
        row = connection.execute(
            """
            SELECT 1 FROM social_relationships
            WHERE relation_type = 'friend' AND status = 'accepted'
              AND (
                (actor_user_id = ? AND target_user_id = ?)
                OR (actor_user_id = ? AND target_user_id = ?)
              )
            LIMIT 1
            """,
            (left_user_id, right_user_id, right_user_id, left_user_id),
        ).fetchone()
        return row is not None

    def _audit_relationship(self, connection, actor_user_id: int, target_user_id: int, action: str) -> None:
        self._audit(
            connection,
            "social_relationship",
            target_user_id,
            action,
            actor_user_id,
            {"target_user_id": target_user_id, "retention_days": 180},
        )

    def _audit_discussion(self, connection, target_type: Literal["post", "comment"], target_id: int, actor_user_id: int, action: str, previous: dict[str, object]) -> None:
        connection.execute(
            """
            INSERT INTO social_discussion_edit_history (target_type, target_id, actor_user_id, action, previous_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (target_type, target_id, actor_user_id, action, json.dumps(previous, ensure_ascii=False, sort_keys=True, default=str)),
        )
        self._audit(connection, f"social_discussion_{target_type}", target_id, action, actor_user_id, {"retention_days": 180})

    def _audit(self, connection, entity_type: str, entity_id: int, action: str, actor_user_id: int, payload: dict[str, object]) -> None:
        connection.execute(
            """
            INSERT INTO catalog_audit_events (entity_type, entity_id, action, actor_user_id, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (entity_type, entity_id, action, actor_user_id, json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)),
        )

    def _get_manufacturer(self, entity_id: int) -> CatalogManufacturer:
        for manufacturer in self.list_catalog().manufacturers:
            if manufacturer.id == entity_id:
                return manufacturer
        raise RuntimeError("fabricante não persistido")

    def _get_model(self, entity_id: int) -> CatalogModel:
        for manufacturer in self.list_catalog().manufacturers:
            for model in manufacturer.models:
                if model.id == entity_id:
                    return model
        raise RuntimeError("modelo não persistido")

    def _get_variant(self, entity_id: int) -> CatalogVariant:
        for manufacturer in self.list_catalog(include_blocked=True).manufacturers:
            for model in manufacturer.models:
                for variant in model.variants:
                    if variant.id == entity_id:
                        return variant
        raise RuntimeError("variante não persistida")


PUBLIC_PRINTER_SQL = """
SELECT p.id, p.owner_user_id, sp.slug AS owner_slug, sp.display_name AS owner_display_name,
       COALESCE(p.public_name, p.name) AS public_name, p.public_description,
       p.public_mods_json, p.public_images_json, p.catalog_variant_id,
       mf.slug AS manufacturer_slug, mf.name AS manufacturer_name,
       m.slug AS model_slug, m.name AS model_name, m.kinematics,
       v.name AS variant_name, v.slug AS variant_slug, v.build_volume_json,
       p.updated_at
FROM printers p
JOIN social_profiles sp ON sp.user_id = p.owner_user_id
JOIN catalog_printer_variants v ON v.id = p.catalog_variant_id
JOIN catalog_printer_models m ON m.id = v.model_id
JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
"""

COMMUNITY_SQL = """
SELECT c.id, c.slug, c.name, c.scope, c.status, c.manufacturer_id, mf.slug AS manufacturer_slug,
       mf.name AS manufacturer_name, mf.logo_url AS manufacturer_logo_url,
       c.model_id, m.slug AS model_slug, m.name AS model_name,
       c.variant_id, v.slug AS variant_slug, v.name AS variant_name,
       c.merged_into_id, merged.slug AS merged_into_slug, merged.name AS merged_into_name,
       COUNT(DISTINCT CASE
           WHEN cm.active = 1 AND p.public_profile_enabled = 1 AND sp.visibility = 'public' AND c.status IN ('active', 'uncurated')
           THEN cm.user_id
       END) AS member_count,
       COUNT(DISTINCT CASE
           WHEN cm.active = 1 AND p.public_profile_enabled = 1 AND sp.visibility = 'public' AND c.status IN ('active', 'uncurated')
           THEN cm.printer_id
       END) AS printer_count,
       COUNT(DISTINCT CASE
           WHEN li.status = 'active' AND li.visibility IN ('public', 'community') AND c.status IN ('active', 'uncurated')
           THEN li.id
       END) AS file_count,
       COUNT(DISTINCT CASE
           WHEN cm.active = 1 AND p.public_profile_enabled = 1 AND sp.visibility = 'public'
                AND c.status IN ('active', 'uncurated') AND COALESCE(p.public_mods_json, '[]') NOT IN ('[]', '')
           THEN cm.printer_id
       END) AS mod_count
FROM social_communities c
LEFT JOIN social_community_members cm ON cm.community_id = c.id
LEFT JOIN printers p ON p.id = cm.printer_id
LEFT JOIN social_profiles sp ON sp.user_id = cm.user_id
LEFT JOIN catalog_manufacturers mf ON mf.id = c.manufacturer_id
LEFT JOIN catalog_printer_models m ON m.id = c.model_id
LEFT JOIN catalog_printer_variants v ON v.id = c.variant_id
LEFT JOIN social_communities merged ON merged.id = c.merged_into_id
LEFT JOIN social_library_items li ON li.community_id = c.id
"""

COMMUNITY_GROUP_SQL = """
GROUP BY c.id, c.slug, c.name, c.scope, c.status, c.manufacturer_id, mf.slug, mf.name, mf.logo_url,
         c.model_id, m.slug, m.name, c.variant_id, v.slug, v.name,
         c.merged_into_id, merged.slug, merged.name
"""

RELATIONSHIP_SQL = """
SELECT r.target_user_id, sp.slug AS target_slug, sp.display_name AS target_display_name,
       r.relation_type, r.status, r.created_at, r.updated_at
FROM social_relationships r
LEFT JOIN social_profiles sp ON sp.user_id = r.target_user_id
"""

RELATIONSHIP_INCOMING_SQL = """
SELECT r.actor_user_id AS target_user_id, sp.slug AS target_slug, sp.display_name AS target_display_name,
       r.relation_type, r.status, r.created_at, r.updated_at
FROM social_relationships r
LEFT JOIN social_profiles sp ON sp.user_id = r.actor_user_id
"""

LIBRARY_ITEM_SQL = """
SELECT li.id, li.owner_user_id, sp.slug AS owner_slug, sp.display_name AS owner_display_name,
       li.community_id, c.slug AS community_slug, c.name AS community_name,
       li.catalog_variant_id, mf.name AS manufacturer_name, m.name AS model_name, v.name AS variant_name,
       li.title, li.description, li.visibility, li.component, li.version_label,
       li.material_suggestion, li.supports_required, li.orientation_notes, li.license,
       li.original_author_name, li.source_url, li.attribution_text, li.remix_source_item_id,
       remix.title AS remix_source_title, li.publication_terms_accepted_at,
       li.status, li.created_at, li.updated_at,
       COUNT(DISTINCT fav.user_id) AS favorite_count,
       COUNT(DISTINCT ci.collection_id) AS collection_count,
       COUNT(DISTINCT pli.id) AS print_list_count,
       COUNT(DISTINCT d.id) AS download_count
FROM social_library_items li
JOIN social_profiles sp ON sp.user_id = li.owner_user_id
LEFT JOIN social_communities c ON c.id = li.community_id
LEFT JOIN catalog_printer_variants v ON v.id = li.catalog_variant_id
LEFT JOIN catalog_printer_models m ON m.id = v.model_id
LEFT JOIN catalog_manufacturers mf ON mf.id = m.manufacturer_id
LEFT JOIN social_library_downloads d ON d.item_id = li.id
LEFT JOIN social_library_items remix ON remix.id = li.remix_source_item_id
LEFT JOIN social_library_favorites fav ON fav.item_id = li.id
LEFT JOIN social_library_collection_items ci ON ci.item_id = li.id
LEFT JOIN social_print_list_items pli ON pli.item_id = li.id
"""

FEED_ITEM_SQL = """
SELECT f.id, f.community_id, f.author_user_id, sp.slug AS author_slug, sp.display_name AS author_display_name,
       f.content_type, f.title, f.body, f.component, f.material, f.firmware_family, f.problem_tag,
       f.attachments_json, f.pinned, f.solution_comment_id, f.edit_count, f.deleted_at,
       f.source_type, f.source_id, f.created_at, f.updated_at,
       (SELECT COUNT(*) FROM social_discussion_comments c WHERE c.feed_item_id = f.id AND c.deleted_at IS NULL) AS comment_count,
       (SELECT COUNT(*) FROM social_discussion_reactions r WHERE r.target_type = 'post' AND r.target_id = f.id) AS reaction_count
FROM social_feed_items f
LEFT JOIN social_profiles sp ON sp.user_id = f.author_user_id AND sp.visibility = 'public'
"""

DISCUSSION_COMMENT_SQL = """
SELECT c.id, c.feed_item_id, c.author_user_id, sp.slug AS author_slug, sp.display_name AS author_display_name,
       c.parent_comment_id, c.body, c.attachments_json, c.edit_count, c.deleted_at, c.created_at, c.updated_at
FROM social_discussion_comments c
LEFT JOIN social_profiles sp ON sp.user_id = c.author_user_id AND sp.visibility = 'public'
"""


def normalize_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    slug = slug.strip("-")
    if not slug:
        raise ValueError("slug inválido")
    return slug[:80]


def clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def clean_library_file_name(value: str) -> str:
    cleaned = value.strip()
    if not cleaned or "/" in cleaned or "\\" in cleaned or ".." in cleaned:
        raise ValueError("nome de arquivo inválido")
    suffix = Path(cleaned).suffix.lower()
    allowed_suffixes = {".stl", ".3mf", ".zip"}
    if suffix not in allowed_suffixes:
        raise ValueError("biblioteca aceita STL, 3MF ou pacote ZIP")
    return cleaned


def _library_file_kind_from_name(file_name: str) -> LibraryFileKind:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".stl":
        return "stl"
    if suffix == ".3mf":
        return "3mf"
    return "bundle"


def _validate_library_upload(file_name: str, file_kind: LibraryFileKind, body: bytes) -> None:
    if file_kind == "stl":
        if len(body) < 84:
            raise ValueError("STL pequeno demais")
        if not (body[:5].lower() == b"solid" or b"facet normal" in body[:4096] or len(body) >= 84):
            raise ValueError("assinatura STL inválida")
        return
    if not body.startswith(b"PK\x03\x04"):
        raise ValueError("assinatura ZIP/3MF inválida")
    from io import BytesIO

    try:
        with zipfile.ZipFile(BytesIO(body)) as archive:
            entries = archive.infolist()
            if not entries:
                raise ValueError("pacote vazio")
            if len(entries) > 120:
                raise ValueError("pacote com arquivos demais")
            total_uncompressed = 0
            has_model_file = False
            has_3mf_content_types = False
            for entry in entries:
                name = entry.filename
                if name.startswith("/") or "\\" in name or ".." in Path(name).parts:
                    raise ValueError("pacote contém path perigoso")
                total_uncompressed += int(entry.file_size)
                if total_uncompressed > 100 * 1024 * 1024:
                    raise ValueError("pacote excede limite descompactado")
                if entry.compress_size and entry.file_size / max(entry.compress_size, 1) > 100:
                    raise ValueError("pacote tem razão de compressão suspeita")
                lower = name.lower()
                has_model_file = has_model_file or lower.endswith((".stl", ".3mf", ".model"))
                has_3mf_content_types = has_3mf_content_types or lower == "[content_types].xml"
            if file_kind == "3mf" and not has_3mf_content_types:
                raise ValueError("3MF sem manifesto obrigatório")
            if file_kind == "bundle" and not has_model_file:
                raise ValueError("pacote sem modelo STL/3MF")
    except zipfile.BadZipFile as exc:
        raise ValueError("pacote ZIP/3MF inválido") from exc


def analyze_3d_model_bytes(file_name: str, file_kind: LibraryFileKind, body: bytes) -> dict[str, object]:
    if not body:
        raise ValueError("arquivo vazio")
    if file_kind == "stl":
        return _analyze_stl(body)
    if file_kind == "3mf":
        return _analyze_3mf(body)
    return _analyze_bundle(body)


def _analyze_stl(body: bytes) -> dict[str, object]:
    vertices: list[tuple[float, float, float]] = []
    triangle_count = 0
    if len(body) >= 84:
        declared = struct.unpack("<I", body[80:84])[0]
        expected = 84 + declared * 50
        if declared > 0 and expected <= len(body):
            triangle_count = int(declared)
            offset = 84
            for _ in range(min(declared, 200_000)):
                chunk = body[offset + 12 : offset + 48]
                if len(chunk) < 36:
                    break
                vertices.extend(struct.unpack("<fffffffff", chunk)[i : i + 3] for i in range(0, 9, 3))
                offset += 50
    if not vertices:
        text = body[:2_000_000].decode("utf-8", errors="ignore")
        vertex_matches = re.findall(r"vertex\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)", text, flags=re.IGNORECASE)
        vertices = [(float(x), float(y), float(z)) for x, y, z in vertex_matches[:600_000]]
        triangle_count = max(1, len(vertices) // 3) if vertices else 0
    if not vertices:
        raise ValueError("STL sem vértices reconhecíveis")
    return _analysis_from_vertices(vertices, triangle_count, mesh_count=1, source_format="stl")


def _analyze_3mf(body: bytes) -> dict[str, object]:
    from io import BytesIO

    vertices: list[tuple[float, float, float]] = []
    mesh_count = 0
    triangle_count = 0
    with zipfile.ZipFile(BytesIO(body)) as archive:
        model_names = [name for name in archive.namelist() if name.lower().endswith(".model")]
        if not model_names:
            raise ValueError("3MF sem modelo 3D")
        for name in model_names[:12]:
            root = ET.fromstring(archive.read(name))
            local_vertices: list[tuple[float, float, float]] = []
            for vertex in root.iter():
                if _xml_local_name(vertex.tag) != "vertex":
                    continue
                try:
                    local_vertices.append((float(vertex.attrib["x"]), float(vertex.attrib["y"]), float(vertex.attrib["z"])))
                except (KeyError, ValueError):
                    continue
            local_triangles = sum(1 for item in root.iter() if _xml_local_name(item.tag) == "triangle")
            if local_vertices:
                mesh_count += 1
                vertices.extend(local_vertices[:200_000])
                triangle_count += local_triangles
    if not vertices:
        raise ValueError("3MF sem vértices reconhecíveis")
    return _analysis_from_vertices(vertices, triangle_count, mesh_count=max(mesh_count, 1), source_format="3mf")


def _analyze_bundle(body: bytes) -> dict[str, object]:
    from io import BytesIO

    summaries: list[dict[str, object]] = []
    with zipfile.ZipFile(BytesIO(body)) as archive:
        for name in archive.namelist()[:120]:
            lower = name.lower()
            if lower.endswith(".stl"):
                try:
                    summaries.append(_analyze_stl(archive.read(name)))
                except ValueError:
                    continue
            elif lower.endswith(".3mf"):
                try:
                    summaries.append(_analyze_3mf(archive.read(name)))
                except ValueError:
                    continue
    if not summaries:
        raise ValueError("pacote sem modelo analisável")
    first = summaries[0]
    total_triangles = sum(int(item.get("triangle_count") or 0) for item in summaries)
    problems = [problem for item in summaries for problem in item.get("problems", []) if isinstance(problem, dict)]
    return {
        **first,
        "source_format": "bundle",
        "mesh_count": len(summaries),
        "triangle_count": total_triangles,
        "problems": problems,
    }


def _analysis_from_vertices(vertices: list[tuple[float, float, float]], triangle_count: int, *, mesh_count: int, source_format: str) -> dict[str, object]:
    xs = [point[0] for point in vertices]
    ys = [point[1] for point in vertices]
    zs = [point[2] for point in vertices]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    min_z, max_z = min(zs), max(zs)
    dimensions = {"x": round(max_x - min_x, 3), "y": round(max_y - min_y, 3), "z": round(max_z - min_z, 3)}
    volume = round(dimensions["x"] * dimensions["y"] * dimensions["z"], 3)
    problems: list[dict[str, str]] = []
    if triangle_count <= 0:
        problems.append({"code": "invalid_mesh", "severity": "error", "message": "Malha sem triângulos reconhecidos."})
    if any(value <= 0 for value in dimensions.values()):
        problems.append({"code": "flat_model", "severity": "warning", "message": "Uma dimensão ficou zerada ou negativa."})
    if max(dimensions.values()) > 600 or min(value for value in dimensions.values() if value > 0) < 0.2:
        problems.append({"code": "suspicious_scale", "severity": "warning", "message": "Escala parece suspeita para impressão FDM comum."})
    if dimensions["x"] > 350 or dimensions["y"] > 350 or dimensions["z"] > 350:
        problems.append({"code": "oversized_model", "severity": "warning", "message": "Dimensões podem não caber em impressoras comuns."})
    support_likely = dimensions["z"] > 0 and (dimensions["z"] / max(dimensions["x"], dimensions["y"], 1)) > 1.8
    if support_likely:
        problems.append({"code": "support_likely", "severity": "info", "message": "Orientação alta sugere avaliar suportes."})
    return {
        "status": "ok",
        "source_format": source_format,
        "dimensions_mm": dimensions,
        "bounding_box": {
            "min": {"x": round(min_x, 3), "y": round(min_y, 3), "z": round(min_z, 3)},
            "max": {"x": round(max_x, 3), "y": round(max_y, 3), "z": round(max_z, 3)},
        },
        "approx_volume_mm3": volume,
        "mesh_count": mesh_count,
        "triangle_count": triangle_count,
        "support_likely": support_likely,
        "problems": problems,
    }


def build_analysis_thumbnail_svg(analysis: dict[str, object]) -> str:
    dimensions = analysis.get("dimensions_mm") if isinstance(analysis.get("dimensions_mm"), dict) else {}
    width = max(float(dimensions.get("x") or 1), 1.0)
    depth = max(float(dimensions.get("y") or 1), 1.0)
    height = max(float(dimensions.get("z") or 1), 1.0)
    scale = 120 / max(width, depth, height)
    rect_w = max(16, min(120, width * scale))
    rect_h = max(16, min(90, depth * scale))
    z_h = max(8, min(44, height * scale * 0.55))
    x = 70 - rect_w / 2
    y = 116 - rect_h / 2
    return (
        "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 140 140\" role=\"img\" aria-label=\"Preview técnico do modelo\">"
        "<rect width=\"140\" height=\"140\" rx=\"8\" fill=\"#f3f7f8\"/>"
        f"<path d=\"M{x:.1f} {y:.1f}h{rect_w:.1f}l-18 -{z_h:.1f}h-{rect_w:.1f}z\" fill=\"#d8e8ed\" stroke=\"#6d8b96\"/>"
        f"<path d=\"M{x:.1f} {y:.1f}v{rect_h:.1f}h{rect_w:.1f}v-{rect_h:.1f}z\" fill=\"#ffffff\" stroke=\"#6d8b96\"/>"
        f"<path d=\"M{x + rect_w:.1f} {y:.1f}l-18 -{z_h:.1f}v{rect_h:.1f}l18 {z_h:.1f}z\" fill=\"#c7dbe2\" stroke=\"#6d8b96\"/>"
        f"<text x=\"70\" y=\"132\" text-anchor=\"middle\" font-size=\"10\" fill=\"#28424d\">{width:.0f} x {depth:.0f} x {height:.0f} mm</text>"
        "</svg>"
    )


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def clean_text_list(values: list[str], max_length: int) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        item = str(value).strip()
        if not item or item in seen:
            continue
        cleaned.append(item[:max_length])
        seen.add(item)
    return cleaned


def clean_public_image_urls(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        image_url = validate_public_url(str(value)[:500], field_name="imagem pública", allowed_hosts=None)
        if image_url is None or image_url in seen:
            continue
        cleaned.append(image_url)
        seen.add(image_url)
    return cleaned


def clean_discussion_text(value: str) -> str:
    cleaned = value.replace("\x00", "").strip()
    if re.search(r"<\s*/?\s*[a-zA-Z][^>]*>", cleaned) or re.search(r"javascript\s*:", cleaned, flags=re.IGNORECASE):
        raise ValueError("HTML ou script não é permitido")
    return cleaned


def clean_discussion_attachments(values: list[dict[str, str]]) -> list[dict[str, str]]:
    cleaned: list[dict[str, str]] = []
    seen: set[str] = set()
    for raw in values:
        kind = str(raw.get("kind", "link")).strip().lower()
        if kind not in {"image", "link"}:
            raise ValueError("tipo de anexo inválido")
        url = validate_public_url(raw.get("url"), field_name="anexo", allowed_hosts=None)
        if not url or url in seen:
            continue
        label = clean_discussion_text(str(raw.get("label") or ""))[:80]
        cleaned.append({"kind": kind, "url": url, "label": label or ("Imagem" if kind == "image" else "Link")})
        seen.add(url)
    return cleaned


def validate_public_url(value: str | None, *, field_name: str, allowed_hosts: set[str] | None) -> str | None:
    cleaned = clean_optional_text(value)
    if cleaned is None:
        return None
    parsed = urlparse(cleaned)
    if parsed.scheme != "https":
        raise ValueError(f"{field_name} deve usar https")
    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f"{field_name} deve informar host público válido")
    hostname = parsed.hostname.lower().strip(".")
    if _is_private_or_local_host(hostname):
        raise ValueError(f"{field_name} não pode apontar para host local ou privado")
    if allowed_hosts is not None and not any(hostname == host or hostname.endswith(f".{host}") for host in allowed_hosts):
        raise ValueError(f"{field_name} usa host não permitido")
    return cleaned


def _is_private_or_local_host(hostname: str) -> bool:
    if hostname in {"localhost", "local", "internal"} or hostname.endswith((".localhost", ".local", ".internal", ".lan")):
        return True
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast


def _clean_social_links(values: dict[str, str | None]) -> dict[str, str | None]:
    host_rules: dict[str, set[str] | None] = {
        "website": None,
        "github": {"github.com"},
        "instagram": {"instagram.com"},
        "youtube": {"youtube.com", "youtu.be"},
        "x": {"x.com", "twitter.com"},
        "printables": {"printables.com"},
        "makerworld": {"makerworld.com"},
    }
    cleaned: dict[str, str | None] = {}
    for key, raw_value in values.items():
        if key not in host_rules:
            continue
        valid_url = validate_public_url(raw_value, field_name=f"social_links.{key}", allowed_hosts=host_rules[key])
        if valid_url:
            cleaned[key] = valid_url
    return cleaned



def _json_dict(value: str | None) -> dict[str, object]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed]


def _json_list_of_dicts(value: str | None) -> list[dict[str, str]]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    cleaned: list[dict[str, str]] = []
    for item in parsed:
        if isinstance(item, dict):
            cleaned.append({str(key): str(val) for key, val in item.items() if val is not None})
    return cleaned


def _variant_from_row(row) -> CatalogVariant:
    return CatalogVariant(
        id=int(row["id"]),
        slug=str(row["slug"]),
        name=str(row["name"]),
        build_volume=_json_dict(row["build_volume_json"]),
        components=_json_dict(row["components_json"]),
        firmware_family=row["firmware_family"],
        trust_state=row["trust_state"],
        source=str(row["source"]),
    )


def _variant_detail_from_row(row) -> CatalogVariantDetail:
    variant = _variant_from_row(row)
    return CatalogVariantDetail(
        **variant.model_dump(),
        manufacturer_id=int(row["manufacturer_id"]),
        manufacturer_slug=str(row["manufacturer_slug"]),
        manufacturer_name=str(row["manufacturer_name"]),
        model_id=int(row["model_id"]),
        model_slug=str(row["model_slug"]),
        model_name=str(row["model_name"]),
        kinematics=str(row["kinematics"]),
    )


def _catalog_state_filter(column: str, include_blocked: bool, include_obsolete: bool) -> str:
    blocked = "1 = 1" if include_blocked else f"{column} != 'blocked'"
    obsolete = "1 = 1" if include_obsolete else f"{column} != 'obsolete'"
    return f"{blocked} AND {obsolete}"


def _community_status_from_trust(*states: str) -> CommunityStatus:
    if "obsolete" in states:
        return "obsolete"
    if any(state in {"draft", "community"} for state in states):
        return "uncurated"
    return "active"


def _profile_from_row(row) -> PublicProfile:
    keys = set(row.keys())
    return PublicProfile(
        user_id=int(row["user_id"]),
        slug=str(row["slug"]),
        display_name=str(row["display_name"]),
        bio=row["bio"],
        avatar_url=row["avatar_url"],
        location=row["location"],
        social_links={key: clean_optional_text(value) for key, value in _json_dict(row["social_links_json"]).items()},
        visibility=row["visibility"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        public_printer_count=int(row["public_printer_count"]) if "public_printer_count" in keys and row["public_printer_count"] is not None else 0,
    )


def _public_printer_from_row(row) -> PublicPrinter:
    return PublicPrinter(
        id=int(row["id"]),
        owner_user_id=int(row["owner_user_id"]),
        owner_slug=row["owner_slug"],
        owner_display_name=row["owner_display_name"],
        public_name=str(row["public_name"]),
        public_description=row["public_description"],
        public_mods=_json_list(row["public_mods_json"]),
        public_images=_json_list(row["public_images_json"]),
        catalog_variant_id=int(row["catalog_variant_id"]),
        manufacturer_slug=str(row["manufacturer_slug"]),
        manufacturer_name=str(row["manufacturer_name"]),
        model_slug=str(row["model_slug"]),
        model_name=str(row["model_name"]),
        variant_name=str(row["variant_name"]),
        variant_slug=str(row["variant_slug"]),
        build_volume=_json_dict(row["build_volume_json"]),
        kinematics=str(row["kinematics"]),
        updated_at=str(row["updated_at"]),
    )


def _community_from_row(row) -> Community:
    return Community(
        id=int(row["id"]),
        slug=str(row["slug"]),
        name=str(row["name"]),
        scope=row["scope"],
        status=row["status"],
        manufacturer_id=row["manufacturer_id"],
        manufacturer_slug=row["manufacturer_slug"],
        manufacturer_name=row["manufacturer_name"],
        manufacturer_logo_url=clean_optional_text(row["manufacturer_logo_url"]),
        model_id=row["model_id"],
        model_slug=row["model_slug"],
        model_name=row["model_name"],
        variant_id=row["variant_id"],
        variant_slug=row["variant_slug"],
        variant_name=row["variant_name"],
        merged_into_id=row["merged_into_id"],
        merged_into_slug=row["merged_into_slug"],
        merged_into_name=row["merged_into_name"],
        member_count=int(row["member_count"] or 0),
        printer_count=int(row["printer_count"] or 0),
        file_count=int(row["file_count"] or 0),
        mod_count=int(row["mod_count"] or 0),
    )


def _feed_item_from_row(row) -> CommunityFeedItem:
    deleted_at = row["deleted_at"]
    return CommunityFeedItem(
        id=int(row["id"]),
        community_id=int(row["community_id"]),
        author_user_id=row["author_user_id"],
        author_slug=row["author_slug"],
        author_display_name=row["author_display_name"],
        content_type=row["content_type"],
        title="Conteúdo removido" if deleted_at else str(row["title"]),
        body="" if deleted_at else str(row["body"] or ""),
        component=row["component"],
        material=row["material"],
        firmware_family=row["firmware_family"],
        problem_tag=row["problem_tag"],
        attachments=[] if deleted_at else _json_list_of_dicts(row["attachments_json"]),
        pinned=bool(row["pinned"]),
        comment_count=int(row["comment_count"] or 0),
        reaction_count=int(row["reaction_count"] or 0),
        solution_comment_id=row["solution_comment_id"],
        edit_count=int(row["edit_count"] or 0),
        deleted_at=deleted_at,
        source_type=str(row["source_type"]),
        source_id=row["source_id"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _library_item_from_row(row, file_rows, version_rows=None) -> LibraryItem:
    versions = [_library_version_from_row(version_row) for version_row in (version_rows or [])]
    return LibraryItem(
        id=int(row["id"]),
        owner_user_id=int(row["owner_user_id"]),
        owner_slug=row["owner_slug"],
        owner_display_name=row["owner_display_name"],
        community_id=row["community_id"],
        community_slug=row["community_slug"],
        community_name=row["community_name"],
        catalog_variant_id=row["catalog_variant_id"],
        manufacturer_name=row["manufacturer_name"],
        model_name=row["model_name"],
        variant_name=row["variant_name"],
        title=str(row["title"]),
        description=str(row["description"] or ""),
        visibility=row["visibility"],
        component=row["component"],
        version_label=str(row["version_label"]),
        material_suggestion=row["material_suggestion"],
        supports_required=bool(row["supports_required"]),
        orientation_notes=row["orientation_notes"],
        license=row["license"],
        original_author_name=row["original_author_name"],
        source_url=row["source_url"],
        attribution_text=row["attribution_text"],
        remix_source_item_id=row["remix_source_item_id"],
        remix_source_title=row["remix_source_title"],
        publication_terms_accepted_at=row["publication_terms_accepted_at"],
        status=row["status"],
        files=[
            LibraryFileMetadata(
                id=int(file_row["id"]),
                file_kind=file_row["file_kind"],
                file_name=str(file_row["file_name"]),
                original_url=file_row["original_url"],
                size_bytes=file_row["size_bytes"],
                sha256=file_row["sha256"],
                validation_status=str(file_row["validation_status"]),
                storage_key=file_row["storage_key"],
                quarantine_key=file_row["quarantine_key"],
                uploaded_size_bytes=file_row["uploaded_size_bytes"],
                rejection_reason=file_row["rejection_reason"],
                deduplicated_from_file_id=file_row["deduplicated_from_file_id"],
                analysis=_json_dict(file_row["analysis_json"]),
                thumbnail_svg=file_row["thumbnail_svg"],
                analyzed_at=file_row["analyzed_at"],
            )
            for file_row in file_rows
        ],
        versions=versions,
        current_version_id=next((version.id for version in versions if version.is_current), None),
        favorite_count=int(row["favorite_count"] or 0),
        collection_count=int(row["collection_count"] or 0),
        print_list_count=int(row["print_list_count"] or 0),
        download_count=int(row["download_count"] or 0),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _library_version_from_row(row) -> LibraryVersion:
    files = []
    raw_files = json.loads(row["files_snapshot_json"] or "[]")
    if isinstance(raw_files, list):
        for file in raw_files:
            if not isinstance(file, dict):
                continue
            files.append(
                LibraryFileMetadata(
                    file_kind=file.get("file_kind"),
                    file_name=str(file.get("file_name") or "arquivo.stl"),
                    original_url=file.get("original_url"),
                    size_bytes=file.get("size_bytes"),
                    sha256=file.get("sha256"),
                    validation_status=str(file.get("validation_status") or "metadata_only"),
                    storage_key=file.get("storage_key"),
                    quarantine_key=file.get("quarantine_key"),
                    uploaded_size_bytes=file.get("uploaded_size_bytes"),
                    rejection_reason=file.get("rejection_reason"),
                    deduplicated_from_file_id=file.get("deduplicated_from_file_id"),
                    analysis=_json_dict(file.get("analysis_json")),
                    thumbnail_svg=file.get("thumbnail_svg"),
                    analyzed_at=file.get("analyzed_at"),
                )
            )
    return LibraryVersion(
        id=int(row["id"]),
        item_id=int(row["item_id"]),
        version_label=str(row["version_label"]),
        changelog=str(row["changelog"] or ""),
        files=files,
        metadata_snapshot=_json_dict(row["metadata_snapshot_json"]),
        is_current=bool(row["is_current"]),
        created_by_user_id=int(row["created_by_user_id"]),
        created_at=str(row["created_at"]),
        download_count=int(row["download_count"] or 0),
    )


def _comment_from_row(row) -> DiscussionComment:
    deleted_at = row["deleted_at"]
    return DiscussionComment(
        id=int(row["id"]),
        feed_item_id=int(row["feed_item_id"]),
        author_user_id=int(row["author_user_id"]),
        author_slug=row["author_slug"],
        author_display_name=row["author_display_name"],
        parent_comment_id=row["parent_comment_id"],
        body="" if deleted_at else str(row["body"]),
        attachments=[] if deleted_at else _json_list_of_dicts(row["attachments_json"]),
        edit_count=int(row["edit_count"] or 0),
        deleted_at=deleted_at,
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _comment_tree(rows) -> list[DiscussionComment]:
    comments = [_comment_from_row(row) for row in rows]
    by_id = {comment.id: comment for comment in comments}
    roots: list[DiscussionComment] = []
    for comment in comments:
        if comment.parent_comment_id and comment.parent_comment_id in by_id:
            parent = by_id[comment.parent_comment_id]
            parent.replies.append(comment)
        else:
            roots.append(comment)
    return roots


def _feed_filter_options(rows) -> dict[str, list[str]]:
    values: dict[str, set[str]] = {"components": set(), "materials": set(), "firmware": set(), "problems": set()}
    for row in rows:
        if row["component"]:
            values["components"].add(str(row["component"]))
        if row["material"]:
            values["materials"].add(str(row["material"]))
        if row["firmware_family"]:
            values["firmware"].add(str(row["firmware_family"]))
        if row["problem_tag"]:
            values["problems"].add(str(row["problem_tag"]))
    return {key: sorted(item for item in option_values if item) for key, option_values in values.items()}


def _primary_component(value: str | None) -> str | None:
    components = _json_dict(value)
    for key in ("toolhead", "extruder", "probe", "mainboard", "hotend", "bed"):
        if components.get(key):
            return str(components[key])[:80]
    return None


def _relationship_from_row(row) -> RelationshipRecord:
    return RelationshipRecord(
        target_user_id=int(row["target_user_id"]),
        target_slug=row["target_slug"],
        target_display_name=row["target_display_name"],
        relation_type=row["relation_type"],
        status=row["status"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )
