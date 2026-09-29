from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


AccessibilityTheme = Literal["system", "light", "dark", "high-contrast"]
TactileFormat = Literal["svg", "brf"]


class AccessibilityCapabilityContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    capability_id: str = Field(pattern=r"^CAP-09-0[1-8]$")
    com_ids: tuple[str, ...] = Field(min_length=7, max_length=7)
    screen_id: str = Field(pattern=r"^SCR-00(?:6[5-9]|7[0-2])$")
    slug: str = Field(pattern=r"^[a-z0-9-]+$")
    title: str = Field(min_length=1, max_length=120)
    summary: str = Field(min_length=1, max_length=280)
    route: str = Field(pattern=r"^/community/accessibility/[a-z0-9-]+$")
    evidence: tuple[str, ...] = Field(min_length=1, max_length=8)
    supported_states: tuple[str, ...]


class AccessibilityCatalogContract(BaseModel):
    model_config = ConfigDict(frozen=True)

    contract_version: str = "1.0.0"
    compatible_with: tuple[str, ...] = ("1.x",)
    capabilities: tuple[AccessibilityCapabilityContract, ...]


class AccessibilityPreferenceValues(BaseModel):
    model_config = ConfigDict(extra="forbid")

    theme: AccessibilityTheme = "system"
    text_scale_percent: int = Field(default=100, ge=100, le=200)
    reduce_motion: bool = False
    screen_reader_announcements: bool = True
    keyboard_navigation: bool = True
    voice_navigation: bool = False
    captions: bool = True
    audio_descriptions: bool = False
    simple_language: bool = False
    low_cognitive_load: bool = False
    three_d_text_alternative: bool = True
    tactile_format: TactileFormat = "svg"


class AccessibilityPreferencesUpdateRequest(AccessibilityPreferenceValues):
    expected_revision: int = Field(ge=0)


class AccessibilityPreferencesContract(AccessibilityPreferenceValues):
    model_config = ConfigDict(frozen=True)

    contract_version: str = "1.0.0"
    compatible_with: tuple[str, ...] = ("1.x",)
    revision: int = Field(ge=0)
    updated_at: str | None = None

