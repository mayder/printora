from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.auth import (
    AgentCredentialCreateRequest,
    AgentCredentialRecord,
    AgentCredentialResponse,
    AuthOrganization,
    AuthRepository,
    AuthSessionResponse,
    AuthUser,
    CurrentUser,
    LoginRequest,
    LoginResponse,
    MfaCodeRequest,
    MfaLoginRequest,
    MfaSetupResponse,
    OrganizationCreateRequest,
    OrganizationMemberAddRequest,
    StepUpRequest,
    StepUpResponse,
    UserRegisterRequest,
    complete_mfa_login,
    login,
    setup_mfa,
    validate_step_up,
    verify_totp,
)
from app.config import get_settings


router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_auth_repository() -> AuthRepository:
    return AuthRepository(get_settings().database_path)


def require_current_user(
    authorization: str | None = Header(default=None),
    repository: AuthRepository = Depends(get_auth_repository),
) -> CurrentUser:
    token = _bearer_token(authorization)
    if token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="autenticação obrigatória")
    user = repository.get_user_by_session(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="sessão expirada ou inválida")
    return CurrentUser(user=user, token=token)


def require_current_user_when_configured(
    authorization: str | None = Header(default=None),
    repository: AuthRepository = Depends(get_auth_repository),
) -> CurrentUser | None:
    if not _has_auth_users(repository):
        return None
    return require_current_user(authorization=authorization, repository=repository)


def _has_auth_users(repository: AuthRepository) -> bool:
    from app.database import connect_database

    with connect_database(repository.database_path) as connection:
        row = connection.execute("SELECT COUNT(*) AS count FROM auth_users WHERE is_active = 1").fetchone()
    return bool(row and int(row["count"]) > 0)


@router.post("/register", response_model=AuthSessionResponse)
async def register_user(
    payload: UserRegisterRequest,
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthSessionResponse:
    try:
        user = repository.create_user(payload)
        token, expires_at = repository.create_session(user.id)
        return AuthSessionResponse(access_token=token, expires_at=expires_at, user=user)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/login", response_model=LoginResponse)
async def login_user(
    payload: LoginRequest,
    repository: AuthRepository = Depends(get_auth_repository),
) -> LoginResponse:
    try:
        return login(repository, payload)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/login/mfa", response_model=AuthSessionResponse)
async def login_mfa(
    payload: MfaLoginRequest,
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthSessionResponse:
    try:
        return complete_mfa_login(repository, payload)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@router.post("/logout")
async def logout_user(
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> dict[str, bool]:
    repository.revoke_session(current.token)
    return {"ok": True}


@router.get("/me", response_model=AuthUser)
async def auth_me(current: CurrentUser = Depends(require_current_user)) -> AuthUser:
    return current.user


@router.post("/organizations", response_model=AuthOrganization)
async def create_organization(
    payload: OrganizationCreateRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthOrganization:
    return repository.create_organization(current.user.id, payload)


@router.get("/organizations", response_model=list[AuthOrganization])
async def list_organizations(
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> list[AuthOrganization]:
    return repository.list_user_organizations(current.user.id)


@router.post("/organizations/{organization_id}/members", response_model=AuthOrganization)
async def add_organization_member(
    organization_id: int,
    payload: OrganizationMemberAddRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthOrganization:
    try:
        return repository.add_organization_member(current.user.id, organization_id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def prepare_mfa(
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> MfaSetupResponse:
    response = setup_mfa(current.user)
    repository.set_mfa_secret(current.user.id, response.secret, enabled=False)
    return response


@router.post("/mfa/enable", response_model=AuthUser)
async def enable_mfa(
    payload: MfaCodeRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthUser:
    secret = repository.get_mfa_secret(current.user.id)
    if secret is None or not verify_totp(secret, payload.code):
        raise HTTPException(status_code=400, detail="código 2FA inválido")
    repository.set_mfa_enabled(current.user.id, True)
    user = repository.get_user(current.user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="usuário não encontrado")
    return user


@router.post("/mfa/disable", response_model=AuthUser)
async def disable_mfa(
    payload: MfaCodeRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> AuthUser:
    secret = repository.get_mfa_secret(current.user.id)
    if current.user.mfa_enabled and (secret is None or not verify_totp(secret, payload.code)):
        raise HTTPException(status_code=400, detail="código 2FA inválido")
    repository.set_mfa_secret(current.user.id, "", enabled=False)
    user = repository.get_user(current.user.id)
    if user is None:
        raise HTTPException(status_code=404, detail="usuário não encontrado")
    return user


@router.post("/step-up", response_model=StepUpResponse)
async def create_step_up_token(
    payload: StepUpRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> StepUpResponse:
    try:
        return validate_step_up(repository, current.user, payload)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/agent-credentials", response_model=AgentCredentialResponse)
async def create_agent_credential(
    payload: AgentCredentialCreateRequest,
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> AgentCredentialResponse:
    try:
        return repository.create_agent_credential(current.user.id, payload)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/agent-credentials", response_model=list[AgentCredentialRecord])
async def list_agent_credentials(
    current: CurrentUser = Depends(require_current_user),
    repository: AuthRepository = Depends(get_auth_repository),
) -> list[AgentCredentialRecord]:
    return repository.list_agent_credentials(current.user.id)


def _bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()
