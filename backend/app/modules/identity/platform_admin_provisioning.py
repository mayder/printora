from __future__ import annotations

from pathlib import Path
import stat

from app.auth import AuthRepository
from app.config import Settings
from app.database import initialize_database
from app.modules.identity.contracts import UserRegisterRequest
from app.platform_access import is_platform_admin


def read_password(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("password-file deve ser arquivo regular sem symlink")
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise ValueError("password-file deve permitir acesso somente ao proprietário")
    password = path.read_text(encoding="utf-8").rstrip("\r\n")
    if not password:
        raise ValueError("password-file está vazio")
    return password


def provision_platform_admin(
    *,
    data_dir: Path,
    email: str,
    password_file: Path,
    display_name: str,
    initialize_empty: bool,
) -> dict[str, object]:
    settings = Settings(data_dir=data_dir)
    normalized_email = email.strip().casefold()
    if not is_platform_admin(normalized_email, settings):
        raise ValueError("email não pertence a PRINTORA_PLATFORM_ADMIN_EMAILS")

    database_path = settings.database_path
    if not database_path.exists():
        if not initialize_empty:
            raise ValueError("base ausente; use --initialize-empty somente em ambiente novo e isolado")
        initialize_database(database_path)

    repository = AuthRepository(database_path)
    existing = repository.get_user_by_email(normalized_email)
    if existing is not None:
        return {
            "created": False,
            "database_path": str(database_path),
            "email": existing.email,
            "platform_admin": existing.platform_admin,
            "user_id": existing.id,
        }

    user = repository.create_user(
        UserRegisterRequest(
            email=normalized_email,
            password=read_password(password_file),
            display_name=display_name,
        )
    )
    return {
        "created": True,
        "database_path": str(database_path),
        "email": user.email,
        "platform_admin": user.platform_admin,
        "user_id": user.id,
    }
