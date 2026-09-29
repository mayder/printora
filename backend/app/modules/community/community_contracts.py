from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.community.catalog_contracts import CatalogSummary
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

ProfileVisibility = Literal["public", "unlisted", "private"]


CommunityStatus = Literal["active", "uncurated", "obsolete", "merged"]


RelationshipType = Literal["follow", "friend", "block"]


RelationshipStatus = Literal["active", "pending", "accepted", "ended"]


FeedContentType = Literal["technical_post", "question", "mod", "print_result", "file_announcement", "curation_notice"]


FeedOrder = Literal["recent", "recommended", "pinned"]


DiscussionReactionType = Literal["like", "useful", "thanks"]


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
