from __future__ import annotations

from app.modules.design_system.contracts import (
    DesignCapabilityContract,
    DesignSystemCatalogContract,
    DesignSystemPermissionsContract,
    DesignTokenContract,
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
        "design-system-documentado-com-tokens-semanticos",
        "Design system documentado com tokens semânticos",
        "Tokens de cor, espaço, tipografia, raio, sombra, movimento e foco com propósito explícito.",
    ),
    (
        "hierarquia-visual-consistente-entre-social-e-operacao",
        "Hierarquia visual consistente entre social e operação",
        "Cabeçalhos, ações e conteúdo crítico mantêm a mesma ordem de leitura em todos os contextos.",
    ),
    (
        "componentes-responsivos-para-cards-tabelas-e-galerias",
        "Componentes responsivos para cards, tabelas e galerias",
        "Coleções mudam de apresentação sem perder conteúdo, ação principal ou navegação por teclado.",
    ),
    (
        "densidade-ajustavel-para-oficina-leitura-e-administracao",
        "Densidade ajustável para oficina, leitura e administração",
        "Três densidades semânticas preservam toque, legibilidade e informação prioritária.",
    ),
    (
        "padroes-de-formulario-longo-com-salvamento-e-revisao",
        "Padrões de formulário longo com salvamento e revisão",
        "Rascunho local versionado, revisão explícita e recuperação após falha sem duplicar efeitos.",
    ),
    (
        "estados-loading-vazio-erro-parcial-e-offline-coerentes",
        "Estados loading, vazio, erro, parcial e offline coerentes",
        "Estados recuperáveis explicam origem, impacto e próxima ação sem depender apenas de cor.",
    ),
    (
        "microinteracoes-com-feedback-e-reducao-de-movimento",
        "Microinterações com feedback e redução de movimento",
        "Feedback curto, foco visível e movimento opcional respeitam preferências de acessibilidade.",
    ),
    (
        "laboratorio-visual-com-regressao-desktop-e-mobile",
        "Laboratório visual com regressão desktop e mobile",
        "Matriz executável valida temas, larguras, estados e densidades antes da publicação.",
    ),
)

SEMANTIC_TOKENS = (
    DesignTokenContract(name="--ds-space-1", value="0.25rem", purpose="Espaço mínimo entre elementos relacionados."),
    DesignTokenContract(name="--ds-space-3", value="0.75rem", purpose="Espaço interno padrão de controles e cards."),
    DesignTokenContract(name="--ds-space-6", value="1.5rem", purpose="Separação entre grupos de conteúdo."),
    DesignTokenContract(name="--ds-radius-control", value="0.5rem", purpose="Raio de inputs, botões e seletores."),
    DesignTokenContract(name="--ds-radius-panel", value="0.75rem", purpose="Raio de superfícies agrupadoras."),
    DesignTokenContract(name="--ds-focus-ring", value="0 0 0 3px", purpose="Geometria do foco visível de teclado."),
    DesignTokenContract(name="--ds-motion-fast", value="120ms", purpose="Feedback de controles sem bloquear interação."),
    DesignTokenContract(name="--ds-motion-standard", value="160ms", purpose="Transição curta entre estados visuais."),
)


def build_catalog() -> DesignSystemCatalogContract:
    capabilities = tuple(
        DesignCapabilityContract(
            capability_id=f"CAP-18-{index:02d}",
            com_ids=tuple(f"COM-{item:04d}" for item in range(953 + (index - 1) * 7, 960 + (index - 1) * 7)),
            screen_id=f"SCR-{136 + index:04d}",
            slug=slug,
            title=title,
            summary=summary,
            route=f"/community/design_system/{slug}",
            tokens=SEMANTIC_TOKENS if index == 1 else (),
            supported_states=SUPPORTED_STATES,
        )
        for index, (slug, title, summary) in enumerate(CAPABILITIES, start=1)
    )
    _validate_catalog(capabilities)
    return DesignSystemCatalogContract(
        permissions=DesignSystemPermissionsContract(),
        capabilities=capabilities,
    )


def _validate_catalog(capabilities: tuple[DesignCapabilityContract, ...]) -> None:
    if len(capabilities) != 8:
        raise ValueError("catálogo deve conter oito capacidades")
    if len({item.slug for item in capabilities}) != len(capabilities):
        raise ValueError("slug de capacidade duplicado")
    com_ids = [com_id for item in capabilities for com_id in item.com_ids]
    if com_ids != [f"COM-{number:04d}" for number in range(953, 1009)]:
        raise ValueError("rastreabilidade COM divergente")
    if [item.screen_id for item in capabilities] != [
        f"SCR-{number:04d}" for number in range(137, 145)
    ]:
        raise ValueError("rastreabilidade SCR divergente")
