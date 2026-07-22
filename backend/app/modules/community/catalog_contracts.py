from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

TrustState = Literal["official", "community", "draft", "obsolete", "blocked"]


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
