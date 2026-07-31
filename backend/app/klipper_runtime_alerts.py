from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Literal


RuntimeAlertSeverity = Literal["warning", "blocker"]

_CRITICAL_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (
        r"lost communication with mcu|unable to connect to mcu|mcu .*shutdown",
        "Comunicação com MCU interrompida",
        "Interrompa novas operações e valide alimentação, conexão e logs antes de reiniciar.",
    ),
    (
        r"timer too close|internal error on command",
        "Falha crítica de temporização do Klipper",
        "Não continue imprimindo. Preserve o estado e revise carga do host e klippy.log.",
    ),
    (
        r"adc out of range|heater .*not heating|verify_heater",
        "Falha crítica de temperatura",
        "Desligue os aquecedores com segurança e revise sensor, chicote e heater antes de imprimir.",
    ),
    (
        r"mcu protocol error|command format mismatch",
        "Incompatibilidade entre Klipper e MCU",
        "Não atualize durante impressão. Recompile e grave todas as MCUs em uma janela controlada.",
    ),
    (
        r"transition to shutdown state|klipper state: shutdown|\bshutdown\b",
        "Klipper entrou em shutdown",
        "Não envie comandos. Abra o monitoramento e revise a causa completa antes de reiniciar.",
    ),
)

_WARNING_PATTERNS: tuple[tuple[str, str, str], ...] = (
    (
        r"has deprecated code|recompiling and flashing is recommended",
        "Firmware da MCU desatualizado",
        "Planeje recompilar e gravar a MCU com a mesma versão do Klipper host, com a impressora parada e rollback disponível.",
    ),
    (
        r"klipper warning",
        "Aviso do Klipper",
        "Revise o aviso no monitoramento antes de uma operação longa.",
    ),
)


@dataclass(frozen=True)
class KlipperRuntimeAlert:
    key: str
    title: str
    severity: RuntimeAlertSeverity
    detail: str
    action: str


def runtime_alert_payload(result: dict[str, Any] | None) -> tuple[list[str], str]:
    payload = result or {}
    raw_messages = payload.get("runtime_alerts")
    messages = []
    if isinstance(raw_messages, list):
        messages = [_clean_message(value) for value in raw_messages]
        messages = [message for message in messages if message]
    state = str(payload.get("runtime_alerts_state") or "unsupported")
    return messages, state


def classify_runtime_alerts(messages: list[str]) -> list[KlipperRuntimeAlert]:
    alerts: list[KlipperRuntimeAlert] = []
    seen: set[str] = set()
    for message in messages:
        clean = _clean_message(message)
        if not clean:
            continue
        classification = _classification(clean)
        if classification is None:
            continue
        severity, title, action = classification
        fingerprint = hashlib.sha256(clean.casefold().encode("utf-8")).hexdigest()[:16]
        key = f"klipper_runtime_{fingerprint}"
        if key in seen:
            continue
        seen.add(key)
        alerts.append(
            KlipperRuntimeAlert(
                key=key,
                title=title,
                severity=severity,
                detail=clean,
                action=action,
            )
        )
    return alerts


def _classification(message: str) -> tuple[RuntimeAlertSeverity, str, str] | None:
    lowered = message.casefold()
    for pattern, title, action in _CRITICAL_PATTERNS:
        if re.search(pattern, lowered):
            return "blocker", title, action
    if lowered.startswith("!!"):
        return (
            "blocker",
            "Erro crítico do Klipper",
            "Não envie novos comandos. Abra o monitoramento e revise a mensagem completa antes de continuar.",
        )
    for pattern, title, action in _WARNING_PATTERNS:
        if re.search(pattern, lowered):
            return "warning", title, action
    return None


def _clean_message(value: object) -> str:
    return " ".join(str(value or "").split())[:1200]
