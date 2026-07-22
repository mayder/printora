from __future__ import annotations

from app.modules.identity.contracts import (
    AuthSessionResponse,
    AuthUser,
    LoginRequest,
    LoginResponse,
    MfaLoginRequest,
    MfaSetupResponse,
    StepUpRequest,
    StepUpResponse,
)
from app.modules.identity.ports import IdentityRepository
from app.modules.identity.security import new_mfa_secret, verify_password, verify_totp


def login(repository: IdentityRepository, payload: LoginRequest) -> LoginResponse:
    user = repository.get_user_by_email(payload.email)
    if user is None or not user.is_active:
        raise ValueError("email ou senha inválidos")
    password_hash = repository.get_password_hash(user.id)
    if password_hash is None or not verify_password(payload.password, password_hash):
        raise ValueError("email ou senha inválidos")
    if user.mfa_enabled:
        return LoginResponse(mfa_required=True, challenge_token=repository.create_mfa_challenge(user.id))
    token, expires_at = repository.create_session(user.id)
    return LoginResponse(access_token=token, expires_at=expires_at, user=user)


def complete_mfa_login(
    repository: IdentityRepository,
    payload: MfaLoginRequest,
) -> AuthSessionResponse:
    user = repository.consume_mfa_challenge(payload.challenge_token)
    if user is None:
        raise ValueError("desafio 2FA inválido ou expirado")
    secret = repository.get_mfa_secret(user.id)
    if secret is None or not verify_totp(secret, payload.code):
        raise ValueError("código 2FA inválido")
    token, expires_at = repository.create_session(user.id)
    return AuthSessionResponse(access_token=token, expires_at=expires_at, user=user)


def setup_mfa(user: AuthUser) -> MfaSetupResponse:
    secret = new_mfa_secret()
    issuer = "Printora"
    label = f"{issuer}:{user.email}"
    uri = f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&digits=6&period=30"
    return MfaSetupResponse(secret=secret, otpauth_uri=uri)


def validate_step_up(
    repository: IdentityRepository,
    user: AuthUser,
    payload: StepUpRequest,
) -> StepUpResponse:
    if user.mfa_enabled:
        secret = repository.get_mfa_secret(user.id)
        if payload.code is None:
            raise ValueError("código 2FA obrigatório para ação crítica")
        if secret is None or not verify_totp(secret, payload.code):
            raise ValueError("código 2FA inválido")
    else:
        password_hash = repository.get_password_hash(user.id)
        if payload.password is None:
            raise ValueError("senha obrigatória para ação crítica")
        if password_hash is None or not verify_password(payload.password, password_hash):
            raise ValueError("senha atual inválida para ação crítica")
    token, expires_at = repository.create_step_up(user.id, payload.purpose)
    return StepUpResponse(step_up_token=token, expires_at=expires_at)
