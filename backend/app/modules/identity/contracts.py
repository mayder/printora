from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


OrganizationRole = Literal["owner", "admin", "operator"]


def clean_email(value: str) -> str:
    cleaned = value.strip().lower()
    if "@" not in cleaned or cleaned.startswith("@") or cleaned.endswith("@"):
        raise ValueError("email inválido")
    return cleaned


def clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def clean_timezone(value: str) -> str:
    cleaned = value.strip()
    try:
        ZoneInfo(cleaned)
    except ZoneInfoNotFoundError as exc:
        raise ValueError("timezone inválido") from exc
    return cleaned


class UserContactLinks(BaseModel):
    instagram: str | None = Field(default=None, max_length=160)
    x: str | None = Field(default=None, max_length=160)
    facebook: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=240)


class UserRegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=120)
    whatsapp: str | None = Field(default=None, max_length=40)
    telegram: str | None = Field(default=None, max_length=80)
    social_links: UserContactLinks = Field(default_factory=UserContactLinks)
    timezone: str = Field(default="America/Sao_Paulo", min_length=1, max_length=80)

    @field_validator("display_name", "whatsapp", "telegram")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return clean_optional_text(value)

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return clean_email(value)

    @field_validator("timezone")
    @classmethod
    def clean_timezone(cls, value: str) -> str:
        return clean_timezone(value)


class UserProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    whatsapp: str | None = Field(default=None, max_length=40)
    telegram: str | None = Field(default=None, max_length=80)
    social_links: UserContactLinks = Field(default_factory=UserContactLinks)
    timezone: str = Field(default="America/Sao_Paulo", min_length=1, max_length=80)

    @field_validator("display_name", "whatsapp", "telegram")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        return clean_optional_text(value)

    @field_validator("timezone")
    @classmethod
    def clean_profile_timezone(cls, value: str) -> str:
        return clean_timezone(value)


class UserPasswordUpdateRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str = Field(min_length=8, max_length=200)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return clean_email(value)


class MfaLoginRequest(BaseModel):
    challenge_token: str = Field(min_length=20, max_length=240)
    code: str = Field(min_length=6, max_length=8)


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("nome da organização é obrigatório")
        return cleaned


class OrganizationUpdateRequest(OrganizationCreateRequest):
    pass


class OrganizationMemberAddRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    role: OrganizationRole = "operator"

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return clean_email(value)


class OrganizationInviteCreateRequest(BaseModel):
    role: OrganizationRole = "operator"


class OrganizationPrinterLinkRequest(BaseModel):
    printer_id: int = Field(ge=1)


class MfaCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class StepUpRequest(BaseModel):
    purpose: str = Field(default="destructive_action", min_length=3, max_length=80)
    password: str | None = Field(default=None, max_length=200)
    code: str | None = Field(default=None, min_length=6, max_length=8)


class AgentCredentialCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    organization_id: int | None = Field(default=None, ge=1)

    @field_validator("label")
    @classmethod
    def clean_label(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("identificação do agente é obrigatória")
        return cleaned


class AuthOrganization(BaseModel):
    id: int
    name: str
    role: OrganizationRole
    owner_user_id: int


class AuthOrganizationMember(BaseModel):
    user_id: int
    email: str
    display_name: str | None
    role: OrganizationRole
    created_at: str


class AuthOrganizationPrinter(BaseModel):
    printer_id: int
    name: str
    moonraker_url: str
    linked_at: str


class AuthOrganizationInvite(BaseModel):
    id: int
    token_prefix: str
    role: OrganizationRole
    invite_url: str
    expires_at: str
    accepted_at: str | None
    revoked_at: str | None
    created_at: str


class AuthOrganizationDetail(AuthOrganization):
    members: list[AuthOrganizationMember] = Field(default_factory=list)
    printers: list[AuthOrganizationPrinter] = Field(default_factory=list)
    invites: list[AuthOrganizationInvite] = Field(default_factory=list)


class AuthUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str | None
    whatsapp: str | None
    telegram: str | None
    social_links: dict[str, str | None]
    timezone: str
    mfa_enabled: bool
    is_active: bool
    created_at: str
    organizations: list[AuthOrganization] = Field(default_factory=list)


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: AuthUser


class LoginResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    expires_at: str | None = None
    user: AuthUser | None = None
    mfa_required: bool = False
    challenge_token: str | None = None


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str


class StepUpResponse(BaseModel):
    step_up_token: str
    expires_at: str


class AgentCredentialResponse(BaseModel):
    id: int
    label: str
    credential: str
    credential_prefix: str
    organization_id: int | None
    created_at: str


class AgentCredentialRecord(BaseModel):
    id: int
    label: str
    credential_prefix: str
    organization_id: int | None
    revoked: bool
    created_at: str
    last_used_at: str | None


@dataclass(frozen=True)
class CurrentUser:
    user: AuthUser
    token: str
