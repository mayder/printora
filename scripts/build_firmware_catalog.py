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
from urllib.parse import urlparse
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.firmware.presets import BOARD_PRESETS


ALLOWED_DOMAIN = "canbus.esoterical.online"
MANIFEST_PATH = Path("backend/app/data/firmware_canbus_manifest.json")
DEFAULT_OUTPUT = Path("backend/app/data/firmware_hardware_catalog.json")
STATUS_CATALOGED = "catalogada"
STATUS_BLOCKED = "bloqueada_com_motivo"
HARDWARE_CATEGORIES = {"can_adapter", "mainboard", "toolhead"}
WORKFLOW_CATEGORIES = {
    "home",
    "getting_started",
    "can_adapter_overview",
    "usb_can_bridge_overview",
    "mainboard_overview",
    "toolhead_overview",
    "final_steps",
}
VENDOR_PREFIXES = (
    "BigTreeTech",
    "Makerbase",
    "Mellow",
    "Fysetc",
    "LDO",
    "MKS",
    "AFC",
    "DragonDinghy",
)
MCU_RE = re.compile(r"\b(?:stm32[a-z]\d+[a-z0-9]*|rp2040|lpc176[89]|samd21|samd51)\b", re.IGNORECASE)
BITRATE_RE = re.compile(r"\b(?:250000|500000|1000000)\b")


@dataclass(frozen=True)
class ExistingCatalogData:
    preset_ids_by_key: dict[str, list[str]]


class MainContentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._in_main = False
        self._main_depth = 0
        self._in_code = False
        self._in_heading = False
        self._code_parts: list[str] = []
        self._heading_parts: list[str] = []
        self.text_parts: list[str] = []
        self.code_blocks: list[str] = []
        self.headings: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "main":
            self._in_main = True
            self._main_depth = 1
            return
        if not self._in_main:
            return
        self._main_depth += 1
        if tag in {"code", "pre"}:
            self._in_code = True
            self._code_parts = []
        if tag in {"h1", "h2", "h3", "h4"}:
            self._in_heading = True
            self._heading_parts = []

    def handle_endtag(self, tag: str) -> None:
        if not self._in_main:
            return
        if tag in {"code", "pre"} and self._in_code:
            code = _normalize_block("\n".join(self._code_parts))
            if code:
                self.code_blocks.append(code)
            self._in_code = False
            self._code_parts = []
        if tag in {"h1", "h2", "h3", "h4"} and self._in_heading:
            heading = _normalize_text(" ".join(self._heading_parts))
            if heading:
                self.headings.append(heading)
            self._in_heading = False
            self._heading_parts = []
        if tag == "main":
            self._in_main = False
            self._main_depth = 0
            return
        self._main_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._in_main:
            return
        self.text_parts.append(data)
        if self._in_code:
            self._code_parts.append(data)
        if self._in_heading:
            self._heading_parts.append(data)

    @property
    def text(self) -> str:
        return _normalize_text(" ".join(self.text_parts))


def build_catalog(*, manifest_path: Path, timeout_seconds: float, generated_at: str) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    existing = load_existing_catalog(DEFAULT_OUTPUT)
    normalized_pages = []
    content_by_url = {}
    for page in manifest["pages"]:
        if page["status"] != STATUS_CATALOGED:
            normalized_pages.append(page)
            continue
        try:
            parsed = parse_page(fetch_page(page["url"], timeout_seconds))
        except OSError as exc:
            blocked_page = {**page, "status": STATUS_BLOCKED, "reason": f"Falha ao coletar conteúdo para normalização: {exc}"}
            normalized_pages.append(blocked_page)
            continue
        normalized_pages.append(page)
        content_by_url[page["url"]] = parsed

    normalized_manifest = {
        "schema_version": manifest["schema_version"],
        "source_url": manifest["source"]["base_url"],
        "retrieved_at": manifest["source"]["retrieved_at"],
        "total_pages": len(normalized_pages),
        "pages": normalized_pages,
    }
    hardware = normalize_hardware(normalized_pages, content_by_url, existing)
    update_flows = normalize_guides(normalized_pages, content_by_url, {"updating"})
    troubleshooting = normalize_guides(normalized_pages, content_by_url, {"troubleshooting"})
    workflows = normalize_workflows(normalized_pages, content_by_url)
    catalog = {
        "schema_version": 1,
        "source": {
            "name": "Esoterical CANBus Guide",
            "url": manifest["source"]["base_url"],
            "retrieved_at": manifest["source"]["retrieved_at"],
            "notes": [
                "Catalogo local gerado a partir do menu publico do guia Esoterical CANBus.",
                "Normalizacao automatica preserva URL de referencia e evita inferir campos quando o conteudo nao e claro.",
            ],
        },
        "manifest": normalized_manifest,
        "generation_metadata": {
            "generated_by": "scripts/build_firmware_catalog.py",
            "generated_at": generated_at,
            "manifest_path": project_relative_path(manifest_path),
            "source_manifest_hash": sha256_bytes(manifest_path.read_bytes()),
        },
        "workflows": workflows,
        "hardware": hardware,
        "known_hardware_without_local_preset": known_without_preset(hardware),
        "troubleshooting": troubleshooting,
        "update_flows": update_flows,
        "katapult": normalize_katapult(content_by_url),
        "can_speed": normalize_can_speed(content_by_url),
    }
    return catalog


def normalize_hardware(pages: list[dict[str, Any]], content_by_url: dict[str, dict[str, Any]], existing: ExistingCatalogData) -> list[dict[str, Any]]:
    hardware = []
    for page in pages:
        if page["category"] not in HARDWARE_CATEGORIES or not page["url"].endswith("/README.html"):
            continue
        content = content_by_url.get(page["url"], {"text": "", "code_blocks": [], "headings": []})
        vendor, model = split_vendor_model(page["title"])
        role = "can_adapter" if page["category"] == "can_adapter" else page["category"]
        connection = {"can_adapter": "dedicated_usb_can", "mainboard": "usb_can_bridge", "toolhead": "can"}[page["category"]]
        known_mcus = sorted({mcu.lower() for mcu in MCU_RE.findall(content["text"])})
        flash_method = detect_flash_method(page["category"], content["text"])
        bootloader = detect_bootloader(content["text"])
        validation_commands = extract_validation_commands(content["code_blocks"])
        safety_notes = extract_safety_notes(content["text"], validation_commands)
        key = catalog_key(vendor, model)
        hardware.append({
            "id": slugify(f"{vendor}-{model}"),
            "vendor": vendor,
            "modelo": model,
            "role": role,
            "connection": connection,
            "guide_url": page["url"],
            "known_mcus": known_mcus,
            "flash_method": flash_method,
            "bootloader": bootloader,
            "katapult": True if "katapult" in content["text"].lower() or "canboot" in content["text"].lower() else None,
            "validation_commands": validation_commands,
            "safety_notes": safety_notes,
            "preset_ids": existing.preset_ids_by_key.get(key, []),
            "catalog_status": page["status"],
        })
    return sorted(hardware, key=lambda item: (role_order(item["role"]), item["vendor"].lower(), item["modelo"].lower()))


def normalize_guides(pages: list[dict[str, Any]], content_by_url: dict[str, dict[str, Any]], categories: set[str]) -> list[dict[str, Any]]:
    guides = []
    for page in pages:
        if page["category"] not in categories:
            continue
        content = content_by_url.get(page["url"], {"text": "", "code_blocks": [], "headings": []})
        guides.append({
            "id": slugify(page["title"]),
            "title": page["title"],
            "url": page["url"],
            "summary": first_sentence(content["text"]),
            "validation_commands": extract_validation_commands(content["code_blocks"]),
            "safety_notes": extract_safety_notes(content["text"], []),
            "catalog_status": page["status"],
        })
    return guides


def normalize_workflows(pages: list[dict[str, Any]], content_by_url: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    workflows = []
    for page in pages:
        if page["category"] not in WORKFLOW_CATEGORIES:
            continue
        content = content_by_url.get(page["url"], {"headings": []})
        steps = [heading for heading in content["headings"][:8] if heading.lower() != page["title"].lower()]
        workflows.append({
            "id": slugify(page["title"]),
            "title": page["title"],
            "url": page["url"],
            "steps": steps,
        })
    return workflows


def normalize_katapult(content_by_url: dict[str, dict[str, Any]]) -> dict[str, Any]:
    url = "https://canbus.esoterical.online/katapult_updating.html"
    text = content_by_url.get(url, {}).get("text", "")
    notes = []
    if text:
        notes.extend(sentences_matching(text, ["katapult", "canboot"])[:4])
    return {
        "guide_url": url,
        "required": False,
        "notes": notes or ["Katapult/CanBoot aparece como bootloader de atualizacao, mas nao deve ser tratado como obrigatorio sem validacao do guia da placa."],
    }


def normalize_can_speed(content_by_url: dict[str, dict[str, Any]]) -> dict[str, Any]:
    url = "https://canbus.esoterical.online/updating_can_speed.html"
    text = content_by_url.get(url, {}).get("text", "")
    bitrates = sorted({int(value) for value in BITRATE_RE.findall(text)})
    return {
        "guide_url": url,
        "default_bitrate": None,
        "supported_bitrates": bitrates,
        "notes": sentences_matching(text, ["canbus speed", "bitrate", "can speed"])[:4] or ["Velocidade CAN deve ser validada no ambiente real antes de alteracao."],
    }


def load_existing_catalog(_path: Path) -> ExistingCatalogData:
    values = {}
    for preset in BOARD_PRESETS.values():
        for key in preset_catalog_keys(preset.id, preset.vendor, preset.name):
            values.setdefault(key, [])
            if preset.id not in values[key]:
                values[key].append(preset.id)
    return ExistingCatalogData(preset_ids_by_key=values)


def preset_catalog_keys(preset_id: str, vendor: str, preset_name: str) -> set[str]:
    cleaned = re.sub(r"\b(?:btt|stm32[a-z0-9]+|rp2040|usb|can|bridge)\b", " ", preset_name, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    keys = {catalog_key(vendor, cleaned)}
    for prefix in {vendor, "BTT", "BigTreeTech"}:
        if cleaned.lower().startswith(prefix.lower()):
            keys.add(catalog_key(vendor, cleaned[len(prefix):].strip()))
    keys.update(PRESET_CATALOG_ALIASES.get(preset_id, set()))
    return {key for key in keys if key != catalog_key(vendor, "")}


PRESET_CATALOG_ALIASES = {
    "btt_octopus_pro_f446_usb_can": {"bigtreetech_octopus_pro_v1_1"},
    "btt_octopus_pro_h723_usb_can": {"bigtreetech_octopus_pro_v1_1"},
    "btt_octopus_v1_1_f446_usb_can": {"bigtreetech_octopus"},
    "btt_ebb36_g0b1_can": {"bigtreetech_ebb36_gen2", "bigtreetech_ebb36_v1_2"},
    "btt_ebb42_g0b1_can": {"bigtreetech_ebb42_gen2", "bigtreetech_ebb42_v1_2"},
    "btt_sb2209_rp2040_can": {"bigtreetech_sb2209_rp2040", "bigtreetech_sb2209_and_sb2240"},
    "btt_sb2240_rp2040_can": {"bigtreetech_sb2209_and_sb2240"},
    "btt_kraken_h723_usb_can": {"bigtreetech_kraken"},
    "btt_manta_m5p_g0b1_usb_can": {"bigtreetech_manta_m5p_v1_0"},
    "btt_manta_m8p_v2_h723_usb_can": {"bigtreetech_manta_m8p_v2_0"},
    "btt_skr_3_h743_usb_can": {"bigtreetech_skr_3"},
    "mellow_fly_sb2040_rp2040_can": {"mellow_fly_sb2040v1_v2"},
    "mellow_fly_sb2040_v3_rp2040_can": {"mellow_fly_sb2040v3"},
    "mellow_fly_sht36_v3_rp2040_can": {"mellow_fly_sht36v3"},
    "mellow_fly_super8_pro_h723_usb_can": {"mellow_fly_super8_pro_h723"},
    "fysetc_spider_f446_usb": {"fysetc_spider_v1_0"},
    "fysetc_spider_v2_2_f446_usb_can": {"fysetc_spider_v2_2"},
    "fysetc_spider_v2_3_f446_usb_can": {"fysetc_spider_v2_3"},
    "fysetc_spider_v3_h723_usb_can": {"fysetc_spider_v3_0_h7"},
    "fysetc_h36_g0b1_can": {"fysetc_h36"},
    "fysetc_sb_combo_v2_f072_can": {"fysetc_sb_combo_v2"},
    "fysetc_sb_can_g0b1": {"fysetc_sb_can_th"},
}


def fetch_page(url: str, timeout_seconds: float) -> str:
    assert_allowed_domain(url)
    request = Request(url, headers={"User-Agent": "Printora firmware catalog normalizer"})
    with urlopen(request, timeout=timeout_seconds) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_page(html_text: str) -> dict[str, Any]:
    parser = MainContentParser()
    parser.feed(html_text)
    return {"text": parser.text, "code_blocks": parser.code_blocks, "headings": parser.headings}


def assert_allowed_domain(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"https", "http"} or parsed.netloc != ALLOWED_DOMAIN:
        raise ValueError(f"URL fora do domínio permitido: {url}")


def split_vendor_model(title: str) -> tuple[str, str]:
    for prefix in VENDOR_PREFIXES:
        if title == prefix:
            return prefix, title
        if title.startswith(f"{prefix} "):
            model = title.removeprefix(prefix).strip()
            return prefix, model
        if prefix == "AFC" and title.startswith("AFC-"):
            return "AFC", title
    first, _, rest = title.partition(" ")
    return first, rest or title


def detect_flash_method(category: str, text: str) -> str:
    lowered = text.lower()
    if "dfu-util" in lowered or "dfu mode" in lowered:
        return "dfu_usb"
    if "katapult" not in lowered and "canboot" not in lowered:
        return "unknown"
    if category == "mainboard":
        return "katapult_usb_can"
    if category == "toolhead":
        return "katapult_can"
    return "unknown"


def detect_bootloader(text: str) -> str | None:
    lowered = text.lower()
    if "katapult" in lowered and "canboot" in lowered:
        return "Katapult/CanBoot"
    if "katapult" in lowered:
        return "Katapult"
    if "canboot" in lowered:
        return "CanBoot"
    if "dfu" in lowered:
        return "DFU"
    return None


def extract_validation_commands(code_blocks: list[str]) -> list[str]:
    commands = []
    for block in code_blocks:
        for line in block.splitlines():
            line = line.strip().lstrip("$ ").strip()
            lowered = line.lower()
            if not line or line.startswith("#"):
                continue
            if any(mutating in lowered for mutating in [" -f ", "flash", "make flash", "dfu-util", "restart", "reboot", "shutdown"]):
                continue
            if any(token in lowered for token in ["canbus_query.py", "ip ", "ifconfig", "lsusb", "ls /dev/serial", "grep ", "python3 "]):
                if line not in commands:
                    commands.append(line)
    return commands[:12]


def extract_safety_notes(text: str, validation_commands: list[str]) -> list[str]:
    notes = ["Catalogo normalizado em modo read-only; comandos sao referencia textual e nao sao executados pelo Printora."]
    lowered = text.lower()
    if "stop" in lowered:
        notes.append("Pagina contem checkpoint/STOP; validar resultado esperado antes de prosseguir.")
    if "backup" in lowered:
        notes.append("Pagina menciona backup; preservar arquivos antes de qualquer acao mutavel.")
    if "not mandatory" in lowered and ("katapult" in lowered or "canboot" in lowered):
        notes.append("Katapult/CanBoot aparece como nao obrigatorio no guia.")
    if validation_commands:
        notes.append("Somente comandos de consulta/validacao foram extraidos automaticamente.")
    return notes


def known_without_preset(hardware: list[dict[str, Any]]) -> dict[str, list[str]]:
    groups = {"can_adapters": [], "mainboards": [], "toolheads": []}
    for item in hardware:
        if item["preset_ids"]:
            continue
        label = f"{item['vendor']} {item['modelo']}".strip()
        if item["role"] == "can_adapter":
            groups["can_adapters"].append(label)
        elif item["role"] == "mainboard":
            groups["mainboards"].append(label)
        elif item["role"] == "toolhead":
            groups["toolheads"].append(label)
    return {key: sorted(values) for key, values in groups.items()}


def first_sentence(text: str) -> str | None:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return parts[0][:280] if parts and parts[0] else None


def sentences_matching(text: str, needles: list[str]) -> list[str]:
    values = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        lowered = sentence.lower()
        if any(needle in lowered for needle in needles):
            cleaned = sentence.strip()
            if cleaned and cleaned not in values:
                values.append(cleaned[:320])
    return values


def role_order(role: str) -> int:
    return {"mainboard": 0, "can_adapter": 1, "toolhead": 2}.get(role, 99)


def catalog_key(vendor: str, model: str) -> str:
    return slugify(f"{vendor}-{model}")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "unknown"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def project_relative_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _normalize_block(value: str) -> str:
    return "\n".join(line.rstrip() for line in html.unescape(value).splitlines()).strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the normalized Printora firmware catalog from the Esoterical CANBus manifest.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--generated-at", default=date.today().isoformat())
    parser.add_argument("--write", action="store_true", help="Write the normalized catalog. Default is dry-run only.")
    args = parser.parse_args(argv)

    catalog = build_catalog(manifest_path=args.manifest, timeout_seconds=args.timeout, generated_at=args.generated_at)
    rendered = json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.write:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
        print(
            "Catalog written to "
            f"{args.output}: {len(catalog['hardware'])} hardware, "
            f"{len(catalog['workflows'])} workflows, "
            f"{len(catalog['update_flows'])} update flows, "
            f"{len(catalog['troubleshooting'])} troubleshooting guides."
        )
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
