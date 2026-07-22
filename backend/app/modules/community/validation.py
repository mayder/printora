from __future__ import annotations

import ipaddress
from pathlib import Path
import re
from urllib.parse import urlparse

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
