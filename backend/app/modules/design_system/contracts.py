from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class DesignTokenContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(pattern=r"^--[a-z0-9-]+$")
    value: str = Field(min_length=1, max_length=80)
    purpose: str = Field(min_length=1, max_length=160)


class DesignCapabilityContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    capability_id: str = Field(pattern=r"^CAP-18-0[1-8]$")
    com_ids: tuple[str, ...] = Field(min_length=7, max_length=7)
    screen_id: str = Field(pattern=r"^SCR-01(?:3[7-9]|4[0-4])$")
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=280)
    route: str = Field(pattern=r"^/community/design_system/[a-z0-9-]+$")
    tokens: tuple[DesignTokenContract, ...] = ()
    supported_states: tuple[str, ...]


class DesignSystemPermissionsContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    can_view: bool = True
    can_customize_local: bool = True
    can_publish_global: bool = False


class DesignSystemCatalogContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: str = "1.0.0"
    compatible_with: tuple[str, ...] = ("1.x",)
    permissions: DesignSystemPermissionsContract
    capabilities: tuple[DesignCapabilityContract, ...]
