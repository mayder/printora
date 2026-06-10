from __future__ import annotations

import base64
import json
import re
import textwrap
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class ConfigOptionPatch(BaseModel):
    option: str = Field(min_length=1, max_length=80)
    value: str = Field(min_length=1, max_length=160)

    @field_validator("option")
    @classmethod
    def validate_option(cls, value: str) -> str:
        clean = value.strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", clean):
            raise ValueError("opção inválida")
        return clean

    @field_validator("value")
    @classmethod
    def validate_value(cls, value: str) -> str:
        clean = value.strip()
        if "\n" in clean or "\r" in clean or "\x00" in clean:
            raise ValueError("valor inválido")
        return clean


class ConfigRemediationRequest(BaseModel):
    section: str = Field(min_length=1, max_length=120)
    options: list[ConfigOptionPatch] = Field(min_length=1, max_length=20)
    source: str = Field(default="calibration", max_length=80)
    execution_id: int | None = Field(default=None, ge=1)

    @field_validator("section")
    @classmethod
    def validate_section(cls, value: str) -> str:
        clean = value.strip()
        if not clean:
            raise ValueError("seção obrigatória")
        if not re.fullmatch(r"[A-Za-z0-9_ -]+", clean):
            raise ValueError("seção inválida")
        return clean


class ConfigRemediationApplyRequest(ConfigRemediationRequest):
    target_ids: list[str] = Field(min_length=1, max_length=20)
    step_up_token: str | None = Field(default=None, max_length=160)


def build_config_remediation_script(
    request: ConfigRemediationRequest | ConfigRemediationApplyRequest,
    *,
    mode: Literal["preview", "apply"],
) -> str:
    payload = request.model_dump()
    payload["mode"] = mode
    encoded = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode()).decode()
    script = r"""\
        set -euo pipefail
        export PRINTORA_REMEDIATION_PAYLOAD_B64='__PRINTORA_PAYLOAD_B64__'
        python3 - <<'PY'
        import base64
        import difflib
        import hashlib
        import json
        import os
        import re
        import shutil
        import sys
        from datetime import datetime, timezone
        from pathlib import Path

        payload = json.loads(base64.b64decode(os.environ["PRINTORA_REMEDIATION_PAYLOAD_B64"]).decode())
        mode = str(payload.get("mode") or "preview")
        section = str(payload.get("section") or "").strip()
        options = [(str(item.get("option") or "").strip(), str(item.get("value") or "").strip()) for item in payload.get("options") or []]
        selected = set(str(item) for item in payload.get("target_ids") or [])
        def _candidate_config_roots():
            values = []
            for env_name in ("PRINTORA_KLIPPER_CONFIG_DIR", "KLIPPER_CONFIG_DIR", "PRINTER_CONFIG_DIR", "MOONRAKER_CONFIG_DIR"):
                raw = os.environ.get(env_name)
                if raw:
                    values.append(Path(raw).expanduser())
            values.extend([
                Path.cwd(),
                Path.cwd() / "printer_data" / "config",
                Path.home() / "printer_data" / "config",
                Path("/home/pi/printer_data/config"),
                Path("/home/biqu/printer_data/config"),
                Path("/home/mks/printer_data/config"),
                Path("/home/orangepi/printer_data/config"),
            ])
            home_root = Path("/home")
            if home_root.is_dir():
                values.extend(sorted(home_root.glob("*/printer_data/config")))
            resolved = []
            seen = set()
            for value in values:
                options_to_check = [value]
                if value.name != "config":
                    options_to_check.append(value / "printer_data" / "config")
                for option in options_to_check:
                    try:
                        candidate = option.resolve()
                    except Exception:
                        candidate = option
                    key = str(candidate)
                    if key in seen or not candidate.is_dir():
                        continue
                    if not any(candidate.glob("*.cfg")) and not any(candidate.glob("*.conf")):
                        continue
                    seen.add(key)
                    resolved.append(candidate)
            return resolved

        roots = _candidate_config_roots()
        if not roots:
            checked = [
                str(Path.home() / "printer_data" / "config"),
                "/home/pi/printer_data/config",
                "/home/biqu/printer_data/config",
                "/home/mks/printer_data/config",
                "/home/orangepi/printer_data/config",
            ]
            print(json.dumps({"status": "failed", "error": "config root não encontrado", "checked_roots": checked}, ensure_ascii=False))
            sys.exit(2)

        excluded_dirs = {".git", "__pycache__", "backups", "backup", "logs", "database"}
        section_re = re.compile(r"^\s*\[([^\]]+)\]\s*(?:[#;].*)?$")
        option_re = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)(\s*(?:[#;].*)?)?$")

        def is_active(line):
            stripped = line.lstrip()
            return stripped and not stripped.startswith("#") and not stripped.startswith(";")

        def rel_path(root, path):
            return str(path.relative_to(root))

        def display_path(root, path):
            if len(roots) == 1:
                return rel_path(root, path)
            return f"{root}:{rel_path(root, path)}"

        def iter_config_files():
            for root in roots:
                for path in sorted(root.rglob("*")):
                    if not path.is_file():
                        continue
                    if any(part in excluded_dirs for part in path.relative_to(root).parts[:-1]):
                        continue
                    if path.suffix.lower() not in {".cfg", ".conf"}:
                        continue
                    yield root, path

        def section_blocks(lines):
            starts = []
            for idx, line in enumerate(lines):
                if not is_active(line):
                    continue
                match = section_re.match(line)
                if match:
                    starts.append((idx, match.group(1).strip()))
            for pos, (start, name) in enumerate(starts):
                end = starts[pos + 1][0] if pos + 1 < len(starts) else len(lines)
                yield start, end, name

        def target_id(root, rel, start, end, name):
            return hashlib.sha256(f"{root}:{rel}:{start + 1}:{end}:{name}".encode()).hexdigest()[:16]

        def patch_block(lines, start, end):
            patched = list(lines)
            existing = {}
            for idx in range(start + 1, end):
                if not is_active(patched[idx]):
                    continue
                match = option_re.match(patched[idx].rstrip("\n"))
                if match:
                    existing[match.group(2)] = idx
            inserts = []
            for opt, value in options:
                if opt in existing:
                    idx = existing[opt]
                    match = option_re.match(patched[idx].rstrip("\n"))
                    indent = match.group(1) if match else ""
                    comment = match.group(4) if match and match.group(4) else ""
                    patched[idx] = f"{indent}{opt}: {value}{comment}\n"
                else:
                    inserts.append(f"{opt}: {value}\n")
            if inserts:
                insert_at = end
                patched[insert_at:insert_at] = inserts
                end += len(inserts)
            return patched, end

        candidates = []
        file_cache = {}
        scanned_files = []
        discovered_sections = {}
        for root, path in iter_config_files():
            rel = rel_path(root, path)
            label = display_path(root, path)
            scanned_files.append(label)
            try:
                lines = path.read_text(errors="replace").splitlines(keepends=True)
            except Exception as exc:
                candidates.append({
                    "id": hashlib.sha256(f"{root}:{rel}:unreadable".encode()).hexdigest()[:16],
                    "path": label,
                    "status": "unreadable",
                    "error": str(exc),
                    "section": section,
                    "start_line": 0,
                    "end_line": 0,
                    "current": "",
                    "proposed": "",
                    "diff": [],
                    "changed": False,
                })
                continue
            file_cache[str(path)] = (root, path, lines)
            for start, end, name in section_blocks(lines):
                discovered_sections.setdefault(name, []).append({"path": label, "start_line": start + 1, "end_line": end})
                if name != section:
                    continue
                patched, _ = patch_block(lines, start, end)
                block_before = "".join(lines[start:end]).rstrip()
                block_after = "".join(patched[start:end]).rstrip()
                diff = list(difflib.unified_diff(
                    "".join(lines[start:end]).splitlines(),
                    "".join(patched[start:end]).splitlines(),
                    fromfile=f"{label}:atual",
                    tofile=f"{label}:proposto",
                    lineterm="",
                ))
                candidates.append({
                    "id": target_id(root, rel, start, end, name),
                    "path": label,
                    "file_key": str(path),
                    "section": name,
                    "start_line": start + 1,
                    "end_line": end,
                    "current": block_before,
                    "proposed": block_after,
                    "diff": diff,
                    "changed": block_before != block_after,
                })

        result = {
            "status": "preview",
            "config_root": ", ".join(str(root) for root in roots),
            "section": section,
            "options": [{"option": opt, "value": value} for opt, value in options],
            "candidates": candidates,
            "scanned_files": scanned_files,
            "matched_sections": discovered_sections.get(section, []),
            "available_sections": sorted(discovered_sections)[:80],
        }
        if mode != "apply":
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(0)
        if not selected:
            print(json.dumps({**result, "status": "blocked", "error": "nenhum alvo selecionado"}, ensure_ascii=False))
            sys.exit(2)

        candidates_by_id = {item.get("id"): item for item in candidates if item.get("id")}
        invalid = sorted(selected - set(candidates_by_id))
        if invalid:
            print(json.dumps({**result, "status": "blocked", "error": "alvo inválido", "invalid_target_ids": invalid}, ensure_ascii=False))
            sys.exit(2)

        backup_root = roots[0] / "backups" / ("printora_config_remediation_" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ"))
        backup_root.mkdir(parents=True, exist_ok=True)
        applied = []
        for file_key, (root, path, original_lines) in file_cache.items():
            rel = rel_path(root, path)
            selected_for_file = [item for item in candidates if item.get("file_key") == file_key and item.get("id") in selected]
            if not selected_for_file:
                continue
            lines = list(original_lines)
            backup_name = hashlib.sha256(f"{root}:{rel}".encode()).hexdigest()[:10] + "__" + rel.replace("/", "__")
            shutil.copy2(path, backup_root / backup_name)
            for candidate in sorted(selected_for_file, key=lambda item: int(item["start_line"]), reverse=True):
                start = int(candidate["start_line"]) - 1
                end = int(candidate["end_line"])
                lines, _ = patch_block(lines, start, end)
                applied.append({"id": candidate["id"], "path": candidate["path"], "start_line": candidate["start_line"], "end_line": candidate["end_line"]})
            path.write_text("".join(lines))

        print(json.dumps({**result, "status": "applied", "backup_path": str(backup_root), "applied": applied}, ensure_ascii=False))
        PY
        """
    clean_script = script[2:] if script.startswith("\\\n") else script
    return textwrap.dedent(clean_script).replace("__PRINTORA_PAYLOAD_B64__", encoded)


def parse_config_remediation_stdout(stdout: str) -> dict[str, Any]:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return {"status": "failed", "error": "retorno inválido do agente", "stdout": stdout[-4000:]}
