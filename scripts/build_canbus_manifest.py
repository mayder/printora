#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


BASE_URL = "https://canbus.esoterical.online/"
ALLOWED_DOMAIN = "canbus.esoterical.online"
DEFAULT_OUTPUT = Path("backend/app/data/firmware_canbus_manifest.json")
STATUS_CATALOGED = "catalogada"
STATUS_IGNORED = "ignorada_com_motivo"
STATUS_BLOCKED = "bloqueada_com_motivo"
ALLOWED_STATUSES = {STATUS_CATALOGED, STATUS_IGNORED, STATUS_BLOCKED}


@dataclass(frozen=True)
class MenuLink:
    url: str
    title: str
    category: str
    menu_order: int


class NavLinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_nav = False
        self._nav_depth = 0
        self._current_href: str | None = None
        self._current_classes: set[str] = set()
        self._current_text: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "nav" and attributes.get("id") == "site-nav":
            self._in_nav = True
            self._nav_depth = 1
            return
        if not self._in_nav:
            return
        self._nav_depth += 1
        if tag != "a":
            return
        classes = set((attributes.get("class") or "").split())
        if "nav-list-link" not in classes:
            return
        self._current_href = attributes.get("href")
        self._current_classes = classes
        self._current_text = []

    def handle_endtag(self, tag: str) -> None:
        if not self._in_nav:
            return
        if tag == "a" and self._current_href and "nav-list-link" in self._current_classes:
            text = _normalize_text(" ".join(self._current_text))
            if text:
                self.links.append((self._current_href, text))
            self._current_href = None
            self._current_classes = set()
            self._current_text = []
        if tag == "nav":
            self._nav_depth -= 1
            if self._nav_depth <= 0:
                self._in_nav = False
            return
        self._nav_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._current_href:
            self._current_text.append(data)


class TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.parts.append(data)

    @property
    def title(self) -> str:
        title = _normalize_text(" ".join(self.parts))
        return title.split("|", 1)[0].strip() if "|" in title else title


def build_manifest(*, timeout_seconds: float, retrieved_at: str) -> dict[str, Any]:
    index_html = fetch_page(BASE_URL, timeout_seconds)
    menu_links = parse_menu_links(index_html)
    pages = []
    for link in menu_links:
        pages.append(fetch_manifest_page(link, timeout_seconds))
    return {
        "schema_version": 1,
        "source": {
            "name": "Esoterical CANBus Guide",
            "base_url": BASE_URL,
            "domain": ALLOWED_DOMAIN,
            "retrieved_at": retrieved_at,
        },
        "safe_mode": {
            "mode": "read_only_http_manifest",
            "dry_run_default": True,
            "domain_limited": True,
            "allowed_domain": ALLOWED_DOMAIN,
            "mutating_commands_executed": False,
            "notes": [
                "Crawler only performs HTTP GET requests against the public guide domain.",
                "No firmware build, flash, update, SSH, restart, or local runtime mutation is executed.",
            ],
        },
        "summary": {
            "total_pages": len(pages),
            "catalogada": sum(1 for page in pages if page["status"] == STATUS_CATALOGED),
            "ignorada_com_motivo": sum(1 for page in pages if page["status"] == STATUS_IGNORED),
            "bloqueada_com_motivo": sum(1 for page in pages if page["status"] == STATUS_BLOCKED),
        },
        "pages": pages,
    }


def parse_menu_links(index_html: str) -> list[MenuLink]:
    parser = NavLinkParser()
    parser.feed(index_html)
    links: list[MenuLink] = []
    seen: set[str] = set()
    for order, (href, title) in enumerate(parser.links, start=1):
        absolute_url = normalize_url(urljoin(BASE_URL, href))
        assert_allowed_domain(absolute_url)
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        links.append(MenuLink(url=absolute_url, title=title, category=categorize_url(absolute_url), menu_order=order))
    return links


def fetch_manifest_page(link: MenuLink, timeout_seconds: float) -> dict[str, Any]:
    try:
        body = fetch_page(link.url, timeout_seconds)
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return {
            "url": link.url,
            "title": link.title,
            "category": link.category,
            "menu_order": link.menu_order,
            "content_hash": None,
            "status": STATUS_BLOCKED,
            "reason": f"HTTP fetch failed: {exc}",
        }
    parsed_title = extract_title(body) or link.title
    return {
        "url": link.url,
        "title": parsed_title,
        "menu_title": link.title,
        "category": link.category,
        "menu_order": link.menu_order,
        "content_hash": sha256_text(normalize_html_for_hash(body)),
        "status": STATUS_CATALOGED,
        "reason": None,
    }


def fetch_page(url: str, timeout_seconds: float) -> str:
    assert_allowed_domain(url)
    request = Request(url, headers={"User-Agent": "Printora firmware catalog manifest crawler"})
    with urlopen(request, timeout=timeout_seconds) as response:
        content_type = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(content_type, errors="replace")


def assert_allowed_domain(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.netloc != ALLOWED_DOMAIN:
        raise ValueError(f"URL fora do domínio permitido: {url}")


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path or "/"
    if path == "/index.html":
        path = "/"
    return f"https://{ALLOWED_DOMAIN}{path}"


def categorize_url(url: str) -> str:
    path = urlparse(url).path
    if path == "/":
        return "home"
    if path == "/Getting_Started.html":
        return "getting_started"
    if path == "/Dedicated_USB_Can_Device.html":
        return "can_adapter_overview"
    if path.startswith("/can_adapter/"):
        return "can_adapter"
    if path == "/USB_CAN_Bridge_Mainboard.html":
        return "usb_can_bridge_overview"
    if path == "/mainboard_flashing.html" or path == "/mainboard_flashing/common_hardware.html":
        return "mainboard_overview"
    if path.startswith("/mainboard_flashing/common_hardware/"):
        return "mainboard"
    if path == "/toolhead_flashing.html" or path == "/toolhead_flashing/common_hardware.html":
        return "toolhead_overview"
    if path.startswith("/toolhead_flashing/common_hardware/"):
        return "toolhead"
    if path == "/Final_Steps.html":
        return "final_steps"
    if path in {
        "/Updating.html",
        "/toolhead_klipper_updating.html",
        "/mainboard_klipper_updating.html",
        "/katapult_updating.html",
        "/updating_can_speed.html",
    }:
        return "updating"
    if path == "/troubleshooting.html" or path.startswith("/troubleshooting/"):
        return "troubleshooting"
    return "other"


def extract_title(html_text: str) -> str:
    parser = TitleParser()
    parser.feed(html_text)
    return parser.title


def normalize_html_for_hash(html_text: str) -> str:
    text = re.sub(r"\s+", " ", html.unescape(html_text)).strip()
    return text


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Printora Esoterical CANBus public-menu manifest.")
    parser.add_argument("--write", action="store_true", help="Write the manifest file. Default is dry-run only.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Manifest output path.")
    parser.add_argument("--timeout", type=float, default=10.0, help="HTTP timeout per page in seconds.")
    parser.add_argument("--retrieved-at", default=date.today().isoformat(), help="Capture date stored in the manifest.")
    args = parser.parse_args(argv)

    manifest = build_manifest(timeout_seconds=args.timeout, retrieved_at=args.retrieved_at)
    rendered = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(f"Manifest written to {args.output} with {manifest['summary']['total_pages']} page(s).")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
