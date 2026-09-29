from __future__ import annotations

import base64
import hashlib
import hmac
import os
import struct
import time


PBKDF2_ITERATIONS = 210_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256:" + ":".join(
        [
            str(PBKDF2_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode(),
            base64.urlsafe_b64encode(digest).decode(),
        ]
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded.split(":", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        salt = base64.urlsafe_b64decode(salt_text)
        expected = base64.urlsafe_b64decode(digest_text)
    except (TypeError, ValueError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations)
    return hmac.compare_digest(actual, expected)


def verify_totp(secret: str, code: str, now: int | None = None) -> bool:
    cleaned = code.strip()
    if not cleaned.isdigit() or len(cleaned) != 6:
        return False
    timestamp = int(time.time()) if now is None else now
    for offset in (-1, 0, 1):
        if hmac.compare_digest(totp_code(secret, timestamp + offset * 30), cleaned):
            return True
    return False


def totp_code(secret: str, timestamp: int | None = None) -> str:
    current = int(time.time()) if timestamp is None else timestamp
    counter = current // 30
    key = _base32_decode(secret)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


def new_mfa_secret() -> str:
    return base64.b32encode(os.urandom(20)).decode().rstrip("=")


def _base32_decode(value: str) -> bytes:
    padding = "=" * ((8 - len(value) % 8) % 8)
    return base64.b32decode(value + padding, casefold=True)
