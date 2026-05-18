import json
import re
from typing import Any

from pydantic import BaseModel

from app.backups import BackupRunRecord
from app.printers import PrinterRecord
from app.snapshots import SnapshotDiff, SnapshotRecord


class SanitizedReport(BaseModel):
    printer_id: int
    safe_mode: str
    format: str
    redactions: list[str]
    markdown: str


class Sanitizer:
    _url_pattern = re.compile(r"https?://[^\s)>\]]+", re.IGNORECASE)
    _ipv4_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    _home_path_pattern = re.compile(r"/home/[^/\s]+/[^\s)>\]]+")
    _sensitive_assignment_pattern = re.compile(
        r"(?i)\b(password|passwd|senha|token|secret|api[_-]?key|access[_-]?key|private[_-]?key|psk)\b"
        r"(\s*[:=]\s*)"
        r"([^,\s}\]]+)"
    )

    def __init__(self) -> None:
        self.redactions: set[str] = set()

    def clean(self, value: Any) -> str:
        if isinstance(value, str):
            return self.clean_text(value)
        return self.clean_text(json.dumps(value, ensure_ascii=False, sort_keys=True))

    def clean_text(self, text: str) -> str:
        sanitized = self._sensitive_assignment_pattern.sub(self._redact_secret, text)
        sanitized = self._url_pattern.sub(self._redact_url, sanitized)
        sanitized = self._home_path_pattern.sub(self._redact_path, sanitized)
        sanitized = self._ipv4_pattern.sub(self._redact_ip, sanitized)
        return sanitized

    def _redact_secret(self, match: re.Match[str]) -> str:
        self.redactions.add("secret_values")
        return f"{match.group(1)}{match.group(2)}<redacted>"

    def _redact_url(self, _: re.Match[str]) -> str:
        self.redactions.add("urls")
        return "<url>"

    def _redact_ip(self, _: re.Match[str]) -> str:
        self.redactions.add("ip_addresses")
        return "<ip>"

    def _redact_path(self, _: re.Match[str]) -> str:
        self.redactions.add("home_paths")
        return "<path>"


def build_sanitized_report(
    printer: PrinterRecord,
    health: dict[str, Any],
    snapshots: list[SnapshotRecord],
    latest_diff: SnapshotDiff | None,
    backup_runs: list[BackupRunRecord],
) -> SanitizedReport:
    sanitizer = Sanitizer()
    lines = [
        "# Relatório sanitizado MayderPrintLab",
        "",
        "## Impressora",
        "",
        f"- ID: {printer.id}",
        f"- Nome: {sanitizer.clean(printer.name)}",
        f"- Moonraker: {sanitizer.clean(printer.moonraker_url)}",
        f"- Modo host audit: {sanitizer.clean(printer.host_audit_mode)}",
        "",
        "## Saúde operacional",
        "",
        f"- Modo seguro: {sanitizer.clean(health.get('safe_mode', 'read_only'))}",
        f"- Conectado: {sanitizer.clean(health.get('connected'))}",
        f"- Decisão: {sanitizer.clean(health.get('decision'))}",
        f"- Resumo: {sanitizer.clean(health.get('summary'))}",
        f"- Contadores: {sanitizer.clean(health.get('counts', {}))}",
        "",
        "### Itens de ação",
        "",
    ]

    items = health.get("items")
    if isinstance(items, list) and items:
        for item in items:
            if not isinstance(item, dict):
                continue
            lines.append(
                "- "
                f"{sanitizer.clean(item.get('title', 'item'))}: "
                f"{sanitizer.clean(item.get('severity', '-'))}; "
                f"{sanitizer.clean(item.get('detail', '-'))}; "
                f"ação: {sanitizer.clean(item.get('action', '-'))}"
            )
    else:
        lines.append("- Nenhum item disponível.")

    lines.extend(
        [
            "",
            "## Snapshots",
            "",
            f"- Quantidade considerada: {len(snapshots)}",
        ]
    )
    for snapshot in snapshots[:5]:
        lines.append(
            f"- #{snapshot.id} · {sanitizer.clean(snapshot.created_at)} · "
            f"{sanitizer.clean(snapshot.snapshot_type)} · {sanitizer.clean(snapshot.summary)}"
        )

    lines.extend(["", "## Última comparação", ""])
    if latest_diff is None:
        lines.append("- Sem comparação recente disponível.")
    else:
        lines.append(f"- Resumo: {sanitizer.clean(latest_diff.summary)}")
        lines.append(f"- Severidade: {sanitizer.clean(latest_diff.highest_severity)}")
        for change in latest_diff.changes[:10]:
            lines.append(
                "- "
                f"{sanitizer.clean(change.title)}: "
                f"{sanitizer.clean(change.detail)} "
                f"antes={sanitizer.clean(change.before)} depois={sanitizer.clean(change.after)}"
            )

    lines.extend(["", "## Backups", ""])
    if backup_runs:
        for run in backup_runs[:5]:
            lines.append(
                f"- #{run.id} · {sanitizer.clean(run.created_at)} · {sanitizer.clean(run.status)} · "
                f"dry_run={sanitizer.clean(run.dry_run)} · arquivos={run.total_files} · "
                f"bytes={run.total_bytes} · {sanitizer.clean(run.message)}"
            )
    else:
        lines.append("- Nenhum histórico de backup disponível.")

    lines.extend(
        [
            "",
            "## Sanitização",
            "",
            "- Este relatório remove URLs, IPs, caminhos locais de usuário e valores sensíveis detectáveis.",
            "- Revise antes de publicar em Discord, fórum ou issue pública.",
        ]
    )

    markdown = "\n".join(lines)
    return SanitizedReport(
        printer_id=printer.id,
        safe_mode="read_only",
        format="markdown",
        redactions=sorted(sanitizer.redactions),
        markdown=markdown,
    )
