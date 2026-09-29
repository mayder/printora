from __future__ import annotations

from app.modules.accessibility.contracts import (
    AccessibilityCapabilityContract,
    AccessibilityCatalogContract,
)


SUPPORTED_STATES = (
    "loading",
    "empty",
    "error",
    "success",
    "partial",
    "offline",
    "forbidden",
    "conflict",
)

CAPABILITIES = (
    (
        "conformidade-continua-com-wcag-e-testes-com-usuarios",
        "Conformidade contínua com WCAG e testes com usuários",
        "Matriz verificável de critérios, tecnologias assistivas, benefício e dano.",
        ("WCAG 2.2 AA", "Axe sem violações críticas/sérias", "validação manual representativa"),
    ),
    (
        "navegacao-integral-por-teclado-switch-e-voz",
        "Navegação integral por teclado, switch e voz",
        "Ordem de foco, atalhos e ações equivalentes sem depender de gesto ou ponteiro.",
        ("ordem de foco", "alvo mínimo", "ação sem hover ou gesto"),
    ),
    (
        "leitor-de-tela-com-semantica-e-anuncios-de-estado",
        "Leitor de tela com semântica e anúncios de estado",
        "Landmarks, nomes, descrições e regiões vivas comunicam contexto e resultado.",
        ("landmarks únicos", "nomes acessíveis", "status aria-live"),
    ),
    (
        "contraste-zoom-reducao-de-movimento-e-temas-adaptativos",
        "Contraste, zoom, redução de movimento e temas adaptativos",
        "Preferências visuais preservam tarefa, leitura e foco em diferentes contextos.",
        ("contraste AA", "zoom 400%", "prefers-reduced-motion"),
    ),
    (
        "legendas-transcricoes-e-audiodescricao-para-midia",
        "Legendas, transcrições e audiodescrição para mídia",
        "Toda mídia relevante possui alternativa sincronizada e identificável.",
        ("legendas", "transcrição", "audiodescrição"),
    ),
    (
        "linguagem-simples-e-modo-de-baixa-carga-cognitiva",
        "Linguagem simples e modo de baixa carga cognitiva",
        "Conteúdo direto, uma ação principal e menor densidade sem retirar informação.",
        ("frases diretas", "etapas curtas", "recuperação explícita"),
    ),
    (
        "visualizacao-3d-com-alternativa-textual-e-tatil-exportavel",
        "Visualização 3D com alternativa textual e tátil exportável",
        "Resumo textual e SVG/BRF tátil substituem a dependência exclusiva do canvas 3D.",
        ("descrição estrutural", "dimensões e orientação", "exportação tátil"),
    ),
    (
        "central-de-preferencias-acessiveis-sincronizada",
        "Central de preferências acessíveis sincronizada",
        "Uma preferência por conta sincroniza dispositivos com conflito explícito.",
        ("isolamento por usuário", "revisão otimista", "retry idempotente"),
    ),
)


def build_catalog() -> AccessibilityCatalogContract:
    capabilities = tuple(
        AccessibilityCapabilityContract(
            capability_id=f"CAP-09-{index:02d}",
            com_ids=tuple(
                f"COM-{item:04d}"
                for item in range(449 + (index - 1) * 7, 456 + (index - 1) * 7)
            ),
            screen_id=f"SCR-{64 + index:04d}",
            slug=slug,
            title=title,
            summary=summary,
            route=f"/community/accessibility/{slug}",
            evidence=evidence,
            supported_states=SUPPORTED_STATES,
        )
        for index, (slug, title, summary, evidence) in enumerate(CAPABILITIES, start=1)
    )
    _validate_catalog(capabilities)
    return AccessibilityCatalogContract(capabilities=capabilities)


def _validate_catalog(
    capabilities: tuple[AccessibilityCapabilityContract, ...],
) -> None:
    if len(capabilities) != 8:
        raise ValueError("catálogo deve conter oito capacidades")
    if len({item.slug for item in capabilities}) != len(capabilities):
        raise ValueError("slug de capacidade duplicado")
    com_ids = [com_id for item in capabilities for com_id in item.com_ids]
    if com_ids != [f"COM-{number:04d}" for number in range(449, 505)]:
        raise ValueError("rastreabilidade COM divergente")
    if [item.screen_id for item in capabilities] != [
        f"SCR-{number:04d}" for number in range(65, 73)
    ]:
        raise ValueError("rastreabilidade SCR divergente")

