from typing import Any, Literal

from pydantic import BaseModel

from app.snapshots import SnapshotDetail


PluginClassification = Literal[
    "necessario",
    "opcional",
    "legado_lixo_tecnico",
    "perigoso_remover_agora",
    "seguro_remover_depois_backup",
    "precisa_confirmacao",
]
PluginAction = Literal["manter", "investigar", "remover_depois_backup", "nao_remover_agora"]


class PluginAuditItem(BaseModel):
    name: str
    title: str
    detected: bool
    classification: PluginClassification
    version: str | None
    dirty: bool | None
    commits_behind: int | None
    risk: str
    recommendation: str
    action: PluginAction
    evidence: list[str]
    removal_gates: list[str]


class PluginAuditResponse(BaseModel):
    printer_id: int
    safe_mode: str
    source: str
    summary: str
    counts: dict[str, int]
    unknown_update_manager_components: list[str]
    items: list[PluginAuditItem]


PLUGIN_CATALOG: dict[str, dict[str, str]] = {
    "adaptive_meshing_purging": {
        "title": "KAMP / adaptive_meshing_purging",
        "classification": "opcional",
        "risk": "Baixo se não houver macro chamando adaptive mesh/purge.",
        "recommendation": "Manter se o fluxo de start print usa adaptive mesh/purge; remover só depois de backup e busca por referências.",
    },
    "klipper-toolchanger-easy": {
        "title": "KTC-Easy / StealthChanger",
        "classification": "perigoso_remover_agora",
        "risk": "Alto em impressoras com toolchanger, mesmo com apenas uma tool instalada.",
        "recommendation": "Manter enquanto macros/toolheads dependem de KTC-Easy; remover só em migração planejada.",
    },
    "led_effect": {
        "title": "LED Effect",
        "classification": "opcional",
        "risk": "Baixo para impressão, médio para macros de status visual.",
        "recommendation": "Manter se LEDs de status fazem parte do workflow; caso contrário pode ser limpo depois de backup.",
    },
    "crowsnest": {
        "title": "Crowsnest",
        "classification": "precisa_confirmacao",
        "risk": "Depende de câmera/webcam ativa.",
        "recommendation": "Se não existe câmera em uso, é candidato a remoção depois de backup e parada do serviço.",
    },
    "sonar": {
        "title": "Sonar",
        "classification": "legado_lixo_tecnico",
        "risk": "Costuma sobrar de webcam/monitoramento antigo e pode manter serviço desnecessário.",
        "recommendation": "Remover se não houver uso explícito em Moonraker, systemd ou navegação.",
    },
    "timelapse": {
        "title": "Timelapse",
        "classification": "precisa_confirmacao",
        "risk": "Depende de câmera e macros de timelapse.",
        "recommendation": "Se webcam está desativada, remover depois de confirmar que nenhum slicer/macro chama timelapse.",
    },
    "auto_speed": {
        "title": "Auto Speed",
        "classification": "legado_lixo_tecnico",
        "risk": "Pode deixar configurações antigas de velocidade sem uso real.",
        "recommendation": "Remover se não houver include, macro ou módulo Python ativo usando auto_speed.",
    },
    "tapchanger": {
        "title": "TapChanger antigo",
        "classification": "legado_lixo_tecnico",
        "risk": "Pode conflitar conceitualmente com StealthChanger/KTC-Easy se sobrou da montagem antiga.",
        "recommendation": "Remover apenas depois de confirmar que nenhuma macro/toolhead ainda importa TapChanger.",
    },
    "tmc_autotune": {
        "title": "TMC Autotune",
        "classification": "perigoso_remover_agora",
        "risk": "Pode estar ligado a configuração de drivers/steppers.",
        "recommendation": "Não remover sem auditoria de includes e seções TMC.",
    },
}


def build_plugin_audit(printer_id: int, latest_snapshot: SnapshotDetail | None) -> PluginAuditResponse:
    version_info = _extract_version_info(latest_snapshot)
    catalog_items = [_build_item(name, metadata, version_info.get(name)) for name, metadata in PLUGIN_CATALOG.items()]
    unknown_components = sorted(name for name in version_info if name not in PLUGIN_CATALOG and _looks_like_plugin(name))
    unknown_items = [_build_unknown_item(name, version_info[name]) for name in unknown_components]
    items = [*catalog_items, *unknown_items]
    detected_count = sum(1 for item in items if item.detected)
    risky_count = sum(1 for item in items if item.detected and item.classification in _RISKY_CLASSIFICATIONS)
    counts = {
        "detected": detected_count,
        "missing": sum(1 for item in catalog_items if not item.detected),
        "risky": risky_count,
        "unknown": len(unknown_components),
        "keep": sum(1 for item in items if item.detected and item.action == "manter"),
        "investigate": sum(1 for item in items if item.detected and item.action == "investigar"),
        "remove_after_backup": sum(1 for item in items if item.detected and item.action == "remover_depois_backup"),
        "do_not_remove_now": sum(1 for item in items if item.detected and item.action == "nao_remover_agora"),
    }
    source = f"latest_moonraker_snapshot:{latest_snapshot.id}" if latest_snapshot else "catalog_without_snapshot"
    summary = f"{detected_count} plugins/mods detectados; {risky_count} exigem confirmação antes de remover."
    return PluginAuditResponse(
        printer_id=printer_id,
        safe_mode="read_only_no_host_commands",
        source=source,
        summary=summary,
        counts=counts,
        unknown_update_manager_components=unknown_components,
        items=items,
    )


def _build_unknown_item(name: str, repo: dict[str, Any]) -> PluginAuditItem:
    return PluginAuditItem(
        name=name,
        title=f"Componente fora do catálogo: {name}",
        detected=True,
        classification="precisa_confirmacao",
        version=_version(repo),
        dirty=repo.get("is_dirty"),
        commits_behind=repo.get("commits_behind_count"),
        risk="Componente detectado no Update Manager, mas ainda sem política local no catálogo.",
        recommendation="Investigar uso real antes de manter, atualizar ou remover.",
        action="investigar",
        evidence=_evidence(name, repo),
        removal_gates=[
            "Classificar o componente no catálogo antes de qualquer remoção.",
            "Buscar referências em includes, macros, moonraker.conf e systemd.",
            "Criar backup antes de qualquer alteração futura.",
        ],
    )


_RISKY_CLASSIFICATIONS = {"perigoso_remover_agora", "legado_lixo_tecnico", "precisa_confirmacao"}


def _extract_version_info(latest_snapshot: SnapshotDetail | None) -> dict[str, dict[str, Any]]:
    if latest_snapshot is None:
        return {}
    update_status = latest_snapshot.payload.get("update_status")
    if not isinstance(update_status, dict):
        return {}
    version_info = update_status.get("version_info")
    if not isinstance(version_info, dict):
        return {}
    return {name: repo for name, repo in version_info.items() if isinstance(repo, dict)}


def _build_item(name: str, metadata: dict[str, str], repo: dict[str, Any] | None) -> PluginAuditItem:
    classification = metadata["classification"]
    return PluginAuditItem(
        name=name,
        title=metadata["title"],
        detected=repo is not None,
        classification=classification,
        version=_version(repo),
        dirty=repo.get("is_dirty") if repo else None,
        commits_behind=repo.get("commits_behind_count") if repo else None,
        risk=metadata["risk"],
        recommendation=metadata["recommendation"],
        action=_action(classification),
        evidence=_evidence(name, repo),
        removal_gates=_removal_gates(classification),
    )


def _version(repo: dict[str, Any] | None) -> str | None:
    if not repo:
        return None
    version = repo.get("full_version_string") or repo.get("version")
    return str(version) if version is not None else None


def _action(classification: str) -> PluginAction:
    if classification in {"necessario", "perigoso_remover_agora"}:
        return "nao_remover_agora"
    if classification == "opcional":
        return "manter"
    if classification == "seguro_remover_depois_backup":
        return "remover_depois_backup"
    return "investigar"


def _evidence(name: str, repo: dict[str, Any] | None) -> list[str]:
    if repo is None:
        return ["Não apareceu no version_info do último snapshot Moonraker/Update Manager."]
    evidence = [f"Componente {name} apareceu no version_info do Update Manager."]
    version = _version(repo)
    if version:
        evidence.append(f"Versão detectada: {version}.")
    if repo.get("is_dirty") is True:
        evidence.append("Repositório marcado como dirty.")
    behind = repo.get("commits_behind_count")
    if isinstance(behind, int) and behind > 0:
        evidence.append(f"{behind} commit(s) atrás do remoto.")
    warnings = repo.get("warnings") or []
    anomalies = repo.get("anomalies") or []
    for value in [*warnings, *anomalies]:
        evidence.append(str(value))
    return evidence


def _removal_gates(classification: str) -> list[str]:
    common = [
        "Criar backup antes de qualquer remoção.",
        "Buscar referências em includes, macros, moonraker.conf e systemd.",
        "Validar Klipper/Moonraker ready após mudança em manutenção futura.",
    ]
    if classification == "perigoso_remover_agora":
        return ["Não remover neste fluxo.", *common]
    if classification in {"legado_lixo_tecnico", "precisa_confirmacao", "seguro_remover_depois_backup"}:
        return common
    if classification == "opcional":
        return ["Manter por padrão; remover apenas se o usuário confirmar que não usa.", *common]
    return ["Manter."]


def _looks_like_plugin(name: str) -> bool:
    ignored = {"klipper", "moonraker", "mainsail", "mainsail-config", "system", "client"}
    if name in ignored:
        return False
    return True
