from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .contracts import (
    CompatibilityRequest,
    CompatibilityResult,
    ConsumptionPayload,
    MaterialAlert,
    MaterialConsumption,
    MaterialQualitySample,
    MaterialSpool,
    QualitySamplePayload,
    SpoolPayload,
    SpoolUpdatePayload,
)
from .repository import MaterialInventoryRepository


VENTILATION_MATERIALS = frozenset({"ABS", "ASA", "NYLON", "PA", "PC", "HIPS"})
MOISTURE_SENSITIVE_MATERIALS = frozenset({"NYLON", "PA", "PC", "PVA", "TPU", "PETG"})


class MaterialInventoryService:
    def __init__(self, repository: MaterialInventoryRepository):
        self.repository = repository

    def list_spools(self, owner_user_id: int) -> list[MaterialSpool]:
        return [self._spool(row) for row in self.repository.list_spools(owner_user_id)]

    def spool(self, spool_id: int, owner_user_id: int) -> MaterialSpool:
        return self._spool(self.repository.spool(spool_id, owner_user_id))

    def create_spool(self, owner_user_id: int, payload: SpoolPayload) -> MaterialSpool:
        return self._spool(self.repository.create_spool(owner_user_id, payload))

    def update_spool(self, spool_id: int, owner_user_id: int, payload: SpoolUpdatePayload) -> MaterialSpool:
        return self._spool(self.repository.update_spool(spool_id, owner_user_id, payload))

    def archive_spool(self, spool_id: int, owner_user_id: int) -> None:
        self.repository.archive_spool(spool_id, owner_user_id)

    def record_consumption(self, owner_user_id: int, payload: ConsumptionPayload) -> MaterialConsumption:
        return MaterialConsumption(**self.repository.record_consumption(owner_user_id, payload))

    def consumptions(self, spool_id: int, owner_user_id: int) -> list[MaterialConsumption]:
        return [MaterialConsumption(**row) for row in self.repository.consumptions(spool_id, owner_user_id)]

    def create_quality_sample(self, owner_user_id: int, payload: QualitySamplePayload) -> MaterialQualitySample:
        return self._quality(self.repository.create_quality_sample(owner_user_id, payload))

    def quality_samples(self, spool_id: int, owner_user_id: int) -> list[MaterialQualitySample]:
        return [self._quality(row) for row in self.repository.quality_samples(spool_id, owner_user_id)]

    def compatibility(self, owner_user_id: int, payload: CompatibilityRequest) -> CompatibilityResult:
        spool = self.repository.spool(payload.spool_id, owner_user_id)
        self.repository.printer_for_owner(payload.printer_id, owner_user_id)
        profile_id = payload.material_profile_id or spool["material_profile_id"]
        reasons: list[str] = []
        warnings: list[str] = []
        unknown = False

        if profile_id is None:
            reasons.append("Selecione um perfil de material para comparar.")
            unknown = True
        else:
            profile = self.repository.profile_for_compatibility(int(profile_id), owner_user_id)
            if str(profile["material_type"]).upper() != str(spool["material_type"]).upper():
                reasons.append("O tipo de material do spool diverge do perfil.")
            if profile["printer_id"] is None:
                reasons.append("O perfil não informa para qual impressora foi validado.")
                unknown = True
            elif int(profile["printer_id"]) != payload.printer_id:
                reasons.append("O perfil foi validado para outra impressora.")

        available = spool["remaining_weight_g"]
        if payload.required_weight_g is None:
            reasons.append("Informe o consumo previsto para confirmar se há material suficiente.")
            unknown = True
        elif available is None:
            reasons.append("O peso disponível ainda não foi confirmado.")
            unknown = True
        elif float(available) < payload.required_weight_g:
            reasons.append("O peso disponível é menor que o consumo previsto.")

        material_type = str(spool["material_type"]).upper()
        if material_type in VENTILATION_MATERIALS:
            warnings.append("Este material exige atenção à ventilação e às orientações do fabricante.")
            if payload.ventilation_confirmed is None:
                reasons.append("Confirme se o ambiente possui ventilação adequada.")
                unknown = True
            elif payload.ventilation_confirmed is False:
                reasons.append("A ventilação necessária não foi confirmada.")

        incompatible_markers = ("diverge", "outra impressora", "menor", "não foi confirmada")
        incompatible = any(marker in reason for reason in reasons for marker in incompatible_markers)
        status = "incompatible" if incompatible else "unknown" if unknown else "compatible"
        if status == "compatible":
            reasons.append("Material, perfil, impressora, ambiente e quantidade foram confirmados.")
        return CompatibilityResult(
            status=status,
            reasons=reasons,
            warnings=warnings,
            available_weight_g=available,
            required_weight_g=payload.required_weight_g,
        )

    def import_spoolman(self, owner_user_id: int, raw_payload: Any) -> tuple[int, int, int]:
        items = extract_spoolman_items(raw_payload)
        imported = 0
        updated = 0
        for item in items:
            _spool, was_created = self.repository.upsert_spoolman(owner_user_id, normalize_spoolman_item(item))
            imported += 1 if was_created else 0
            updated += 0 if was_created else 1
        return imported, updated, len(items)

    def _spool(self, row: dict[str, Any]) -> MaterialSpool:
        return MaterialSpool(**row, alerts=material_alerts(row))

    @staticmethod
    def _quality(row: dict[str, Any]) -> MaterialQualitySample:
        deviation = abs(float(row["measured_value_mm"]) - float(row["nominal_value_mm"]))
        return MaterialQualitySample(**row, deviation_mm=round(deviation, 4))


def material_alerts(spool: dict[str, Any]) -> list[MaterialAlert]:
    alerts: list[MaterialAlert] = []
    material_type = str(spool["material_type"]).upper()
    remaining = spool["remaining_weight_g"]
    initial = spool["initial_weight_g"]
    if remaining is None:
        alerts.append(_alert("weight_unknown", "warning", "Peso não confirmado", "Sem peso disponível, o Printora não pode afirmar que há material suficiente.", "Pese o spool ou sincronize o Spoolman."))
    elif float(remaining) <= 20:
        alerts.append(_alert("discard", "info", "Spool quase vazio", "Separe a sobra e evite descartar ou queimar o material sem seguir a regra local.", "Consulte a orientação de descarte do fabricante e do município."))
    elif initial and float(remaining) <= float(initial) * 0.1:
        alerts.append(_alert("low_weight", "warning", "Pouco material disponível", "O spool possui menos de 10% do peso inicial informado.", "Confirme o consumo previsto antes de fatiar ou imprimir."))
    if material_type in MOISTURE_SENSITIVE_MATERIALS and spool["storage_state"] in {"open", "unknown"}:
        alerts.append(_alert("storage", "warning", "Armazenamento precisa de revisão", "Este material pode mudar de comportamento após exposição à umidade.", "Revise a embalagem e siga a secagem indicada pelo fabricante."))
    if material_type in VENTILATION_MATERIALS:
        alerts.append(_alert("ventilation", "warning", "Ventilação necessária", "A emissão depende do material, temperatura e ambiente; o Printora não considera o uso seguro sem confirmação.", "Use a orientação do fabricante e confirme ventilação apropriada."))
    if spool["expires_at"] and _is_past(str(spool["expires_at"])):
        alerts.append(_alert("expired", "warning", "Validade informada vencida", "A data registrada para este lote já passou.", "Revise o estado do material antes de usar."))
    return alerts


def extract_spoolman_items(value: Any) -> list[dict[str, Any]]:
    candidates: list[list[dict[str, Any]]] = []

    def visit(item: Any, depth: int = 0) -> None:
        if depth > 7:
            return
        if isinstance(item, list):
            mapped = [
                entry
                for entry in item
                if isinstance(entry, dict) and entry.get("id") not in (None, "")
            ]
            if mapped:
                candidates.append(mapped)
            for entry in item:
                visit(entry, depth + 1)
        elif isinstance(item, dict):
            for nested in item.values():
                visit(nested, depth + 1)

    visit(value)
    if not candidates:
        return []
    return max(candidates, key=len)[:500]


def normalize_spoolman_item(item: dict[str, Any]) -> dict[str, Any]:
    filament = item.get("filament") if isinstance(item.get("filament"), dict) else {}
    vendor = filament.get("vendor") if isinstance(filament.get("vendor"), dict) else {}
    remaining = _number(item.get("remaining_weight"))
    used = _number(item.get("used_weight"))
    initial = _number(item.get("initial_weight"))
    if initial is None and remaining is not None and used is not None:
        initial = remaining + used
    material_type = _text(filament.get("material") or item.get("material") or "DESCONHECIDO").upper()
    color_hex = _text(filament.get("color_hex") or item.get("color_hex")) or None
    if color_hex and not color_hex.startswith("#"):
        color_hex = f"#{color_hex}"
    if color_hex and (len(color_hex) != 7 or any(char not in "#0123456789ABCDEFabcdef" for char in color_hex)):
        color_hex = None
    location = item.get("location")
    if isinstance(location, dict):
        location = location.get("name")
    return {
        "external_id": _text(item.get("id")),
        "name": _text(item.get("name") or filament.get("name") or f"Spool {item.get('id')}")[:120],
        "material_type": material_type[:40],
        "brand": _text(vendor.get("name") or filament.get("vendor_name"))[:80],
        "color_name": _text(filament.get("color_name") or item.get("color_name"))[:80],
        "color_hex": color_hex.upper() if color_hex else None,
        "lot_code": _text(item.get("lot_nr") or item.get("lot_code"))[:100],
        "initial_weight_g": initial,
        "remaining_weight_g": remaining,
        "location": _text(location)[:160],
        "storage_state": "unknown",
    }


def _alert(code: str, severity: str, title: str, detail: str, action: str) -> MaterialAlert:
    return MaterialAlert(code=code, severity=severity, title=title, detail=detail, action=action)


def _text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _number(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _is_past(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed < datetime.now(timezone.utc)
    except ValueError:
        return False
