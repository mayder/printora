#!/usr/bin/env python3
"""Bloqueia lacunas e dependências futuras no backlog comunitário."""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMANDS = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "DEMANDAS.md"
COMMUNITY = ROOT / "docs" / "community"
ARCHITECTURE = (
    Path(sys.argv[2]).resolve()
    if len(sys.argv) > 2
    else COMMUNITY / "PACKAGE_ARCHITECTURE.csv"
)
STANDARD = COMMUNITY / "PACKAGE_EXECUTION_STANDARD.md"
BACKLOG = COMMUNITY / "COMMUNITY_BACKLOG.csv"
SCREENS = COMMUNITY / "COMMUNITY_SCREENS.csv"
SUMMARY = COMMUNITY / "SUMMARY.json"
HEADING = re.compile(r"^## PKG-(\d+): (.+)$", re.MULTILINE)
PACKAGE_REF = re.compile(r"`PKG-(\d+)`")
PRIORITY = re.compile(r"^Prioridade social: (P[0-4])\.$", re.MULTILINE)
CAPABILITY_RANGE = re.compile(
    r"- capacidades: `CAP-(\d{2})-(\d{2})` a `CAP-(\d{2})-(\d{2})`;"
)
REQUIREMENT_RANGE = re.compile(
    r"- requisitos: `COM-(\d{4})` a `COM-(\d{4})` — (\d+) itens;"
)
SCREEN_RANGE = re.compile(
    r"- telas: `SCR-(\d{4})` a `SCR-(\d{4})` — (\d+) famílias;"
)
OWNERS = {
    "identity",
    "community",
    "finance",
    "operations",
    "administration",
    "integrations",
    "shared",
}
FRONTEND_AREAS = {
    "platform",
    "account",
    "administration",
    "moderation",
    "community",
    "impact",
    "manufacturing",
    "learning",
    "operations",
    "projects",
    "communications",
    "discovery",
    "integrations",
    "creator",
    "commerce",
}
RISK_PROFILES = {"high", "critical"}
LENSES = {"produto", "tela", "mobile", "acessibilidade", "confiança", "impacto", "qualidade"}
EXPECTED_DEPENDENCIES: dict[int, tuple[int, ...]] = {
    101: (),
    102: (101,),
    103: (101, 102),
    104: (101, 102, 103),
    105: (104,),
    106: (101, 104, 105),
    107: (104, 105, 106),
    108: (104, 105, 106, 107),
    109: (101, 102, 107),
    110: (101, 102, 103, 104, 105, 108, 109),
    111: (104, 105, 106, 107, 108),
    112: (104, 105, 106, 107, 108, 109, 110),
    113: (106, 111),
    114: (106, 111, 113),
    115: (104, 105, 106, 107, 108, 113, 114),
    116: (102, 103, 104, 105, 106, 107, 108, 111, 113, 114, 115),
    117: (103, 104, 105, 106, 107, 108, 109, 111, 113, 114, 115),
    118: (102, 103, 106, 107, 109, 110, 111),
    119: (112, 113, 115, 118),
    120: (106, 111, 113, 114, 115),
    121: (106, 113, 114, 115, 120),
    122: (104, 105, 108, 109, 110),
    123: (104, 105, 107, 108, 122),
    124: (107, 108, 109, 122, 123),
    125: (101, 102, 103, 105, 107, 108, 109, 122, 124),
    126: (109, 118, 124, 125),
    127: (104, 105, 107, 108, 125),
    128: (111, 113, 114, 125, 127),
    129: (101, 102, 103, 111, 128),
    130: (111, 113, 128, 129),
    131: (111, 113, 114, 128, 129, 130),
    132: (104, 111, 113, 131),
    133: (113, 114, 124, 132),
    134: (104, 113, 115, 124, 132, 133),
    135: (122, 123, 124, 125, 128, 132),
    136: (104, 105, 107, 108, 122, 123, 124),
    137: (112, 115, 124, 136),
    138: (107, 108, 122, 123, 124, 125, 126, 127, 135, 136, 137),
    139: (105, 107, 108, 122, 124, 125, 126, 127, 128, 138),
    140: (105, 106, 107, 108, 122, 123, 138, 139),
    141: (104, 105, 106, 107, 108, 111, 113, 127, 128, 129, 132),
    142: (104, 105, 108, 128, 131, 132),
    143: (104, 105, 108, 142),
    144: (122, 125, 127, 128, 129, 135, 138, 139, 140),
    145: (106, 108, 122, 123, 124, 125, 126, 138, 139, 140),
    146: (104, 105, 107, 108, 122, 124, 135, 136, 145),
    147: (104, 105, 107, 108, 111, 113, 115, 122, 128, 132, 144, 145, 146),
    148: (104, 105, 108, 122, 144, 146, 147),
    149: (104, 105, 108, 113, 115, 132, 134, 147),
    150: (107, 108, 112, 124, 135, 145, 146, 147),
    151: (104, 105, 107, 108, 122, 124, 144, 145, 146, 147, 149),
    152: (108, 109, 113, 118, 119, 122, 124, 125, 126, 127, 128, 129, 135, 142, 143),
    153: (102, 103, 104, 105, 111, 113, 127, 128, 129, 141),
    154: (104, 105, 106, 107, 108, 111, 113, 126, 131, 132, 141, 143),
    155: (102, 103, 104, 105, 109, 127, 132, 141, 153, 154),
}


def fail(message: str) -> None:
    print(f"[demand-dependencies] ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_architecture(expected_packages: list[int]) -> dict[int, dict[str, str]]:
    rows = read_csv(ARCHITECTURE)
    required_fields = {
        "package_id",
        "domain_key",
        "primary_backend_owner",
        "backend_collaborators",
        "frontend_area",
        "risk_profile",
    }
    if not rows or set(rows[0]) != required_fields:
        fail("PACKAGE_ARCHITECTURE.csv possui colunas divergentes")

    packages: dict[int, dict[str, str]] = {}
    domain_keys: set[str] = set()
    for row in rows:
        match = re.fullmatch(r"PKG-(\d{3})", row["package_id"])
        if not match:
            fail(f"package_id inválido na matriz: {row['package_id']}")
        package = int(match.group(1))
        if package in packages:
            fail(f"PKG-{package} duplicado na matriz")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", row["domain_key"]):
            fail(f"PKG-{package} possui domain_key inválido")
        if row["domain_key"] in domain_keys:
            fail(f"domain_key duplicado na matriz: {row['domain_key']}")
        if row["primary_backend_owner"] not in OWNERS:
            fail(f"PKG-{package} possui owner inválido")
        collaborators = row["backend_collaborators"].split("|")
        if any(value not in OWNERS for value in collaborators):
            fail(f"PKG-{package} possui colaborador inválido")
        if len(collaborators) != len(set(collaborators)):
            fail(f"PKG-{package} possui colaborador duplicado")
        if row["primary_backend_owner"] in collaborators:
            fail(f"PKG-{package} repete owner como colaborador")
        if row["frontend_area"] not in FRONTEND_AREAS:
            fail(f"PKG-{package} possui área frontend inválida")
        if row["risk_profile"] not in RISK_PROFILES:
            fail(f"PKG-{package} possui perfil de risco inválido")
        packages[package] = row
        domain_keys.add(row["domain_key"])

    if sorted(packages) != expected_packages:
        fail("matriz arquitetural não cobre exatamente PKG-101..PKG-155")
    return packages


def validate_generated_sources() -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    backlog = read_csv(BACKLOG)
    screens = read_csv(SCREENS)
    expected_com = [f"COM-{value:04d}" for value in range(1, 3081)]
    expected_scr = [f"SCR-{value:04d}" for value in range(1, 441)]
    expected_cap = {
        f"CAP-{domain:02d}-{feature:02d}"
        for domain in range(1, 56)
        for feature in range(1, 9)
    }
    if [row["id"] for row in backlog] != expected_com:
        fail("COMMUNITY_BACKLOG.csv possui lacuna, duplicidade ou ordem inválida")
    if [row["id"] for row in screens] != expected_scr:
        fail("COMMUNITY_SCREENS.csv possui lacuna, duplicidade ou ordem inválida")

    capability_counts = Counter(row["capability_id"] for row in backlog)
    if set(capability_counts) != expected_cap or set(capability_counts.values()) != {7}:
        fail("cada capacidade deve possuir exatamente sete requisitos")
    for capability in expected_cap:
        lenses = {row["lens"] for row in backlog if row["capability_id"] == capability}
        if lenses != LENSES:
            fail(f"{capability} possui lentes divergentes: {sorted(lenses)}")

    screen_capabilities = [row["capability_id"] for row in screens]
    if set(screen_capabilities) != expected_cap or len(screen_capabilities) != len(
        set(screen_capabilities)
    ):
        fail("cada capacidade deve possuir exatamente uma família de tela")

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    priorities = Counter(row["priority"] for row in backlog)
    expected_summary = {
        "domains": 55,
        "capabilities": 440,
        "atomic_items": 3080,
        "screen_families": 440,
        "screen_states": 1320,
        "priorities": dict(sorted(priorities.items())),
    }
    if summary != expected_summary:
        fail("SUMMARY.json diverge das fontes CSV")
    return backlog, screens


def require_match(pattern: re.Pattern[str], section: str, message: str) -> re.Match[str]:
    match = pattern.search(section)
    if not match:
        fail(message)
    return match


def validate_standard(text: str) -> None:
    required_references = {
        "docs/community/PACKAGE_ARCHITECTURE.csv",
        "docs/community/PACKAGE_EXECUTION_STANDARD.md",
        "docs/community/PACKAGE_MODELING_REVIEW.md",
    }
    preamble = text.split("## PKG-101:", 1)[0]
    missing = sorted(value for value in required_references if value not in preamble)
    if missing:
        fail(f"DEMANDAS.md não referencia fontes bloqueantes: {missing}")

    standard = STANDARD.read_text(encoding="utf-8")
    required_headings = {
        "## Definition Of Ready",
        "## Modelagem De Domínio",
        "## Backend",
        "## Banco E Persistência",
        "## Frontend",
        "## Integrações, Jobs E IA",
        "## Testes Por Perfil De Risco",
        "## Compatibilidade E Proteção Do Legado",
        "## Definition Of Done Do Pacote",
        "## Handoff Para Outra Janela",
    }
    absent = sorted(value for value in required_headings if value not in standard)
    if absent:
        fail(f"padrão de execução incompleto: {absent}")


def validate_indexes(text: str, metadata: dict[int, tuple[str, str]]) -> None:
    order = text.split("## Ordem Recomendada De Implementação", 1)[1].split(
        "## Índice Por Prioridade Social", 1
    )[0]
    order_rows = re.findall(
        r"^- PKG-(\d{3}) \[(P[0-4])\]: (.+)$", order, re.MULTILINE
    )
    expected_order = [
        (str(package), metadata[package][1], metadata[package][0])
        for package in range(101, 156)
    ]
    if order_rows != expected_order:
        fail("índice de implementação diverge dos pacotes")

    priority_index = text.split("## Índice Por Prioridade Social", 1)[1].split(
        "## Política De Backlog", 1
    )[0]
    indexed: list[int] = []
    for priority in (f"P{value}" for value in range(5)):
        section = priority_index.split(f"### {priority}", 1)
        if len(section) != 2:
            fail(f"índice social não possui seção {priority}")
        content = section[1].split("### ", 1)[0]
        rows = re.findall(r"^- PKG-(\d{3}): (.+)$", content, re.MULTILINE)
        expected = [
            (str(package), title)
            for package, (title, package_priority) in metadata.items()
            if package_priority == priority
        ]
        if rows != expected:
            fail(f"índice social {priority} diverge dos pacotes")
        indexed.extend(int(package) for package, _ in rows)
    if sorted(indexed) != list(range(101, 156)) or len(indexed) != len(set(indexed)):
        fail("índice social possui lacuna ou pacote duplicado")


def validate_package_structure(package: int, section: str) -> None:
    required_sections = (
        "Dependências:",
        "Entrega isolada:",
        "Lotes de capacidade:",
        "Critério de aceite:",
        "Rollback:",
        "Estado atual:",
    )
    for label in required_sections:
        if section.count(label) != 1:
            fail(f"PKG-{package} deve possuir uma seção {label}")
    if "nenhum pacote de ID maior é necessário" not in section:
        fail(f"PKG-{package} não declara independência de pacote futuro")
    if "reexecução idempotente" not in section:
        fail(f"PKG-{package} não exige teste de reexecução idempotente")
    lots = re.findall(r"^(\d+)\. \*\*", section, re.MULTILINE)
    if lots != [str(value) for value in range(1, 11)]:
        fail(f"PKG-{package} deve possuir lotes numerados de 1 a 10")


def parse_package_coverage(
    package: int, section: str
) -> tuple[str, list[str], list[str], list[str]]:
    priority = require_match(
        PRIORITY, section, f"PKG-{package} não declara prioridade social"
    ).group(1)
    capability = require_match(
        CAPABILITY_RANGE, section, f"PKG-{package} não declara capacidades"
    )
    requirement = require_match(
        REQUIREMENT_RANGE, section, f"PKG-{package} não declara requisitos"
    )
    screen = require_match(SCREEN_RANGE, section, f"PKG-{package} não declara telas")
    cap_domain_start, cap_start, cap_domain_end, cap_end = map(int, capability.groups())
    if cap_domain_start != cap_domain_end or (cap_start, cap_end) != (1, 8):
        fail(f"PKG-{package} deve cobrir oito capacidades da mesma frente")
    capabilities = [
        f"CAP-{cap_domain_start:02d}-{value:02d}"
        for value in range(cap_start, cap_end + 1)
    ]
    requirement_start, requirement_end, requirement_count = map(int, requirement.groups())
    requirements = [
        f"COM-{value:04d}" for value in range(requirement_start, requirement_end + 1)
    ]
    if len(requirements) != requirement_count or requirement_count != 56:
        fail(f"PKG-{package} deve cobrir exatamente 56 requisitos")
    screen_start, screen_end, screen_count = map(int, screen.groups())
    screens = [f"SCR-{value:04d}" for value in range(screen_start, screen_end + 1)]
    if len(screens) != screen_count or screen_count != 8:
        fail(f"PKG-{package} deve cobrir exatamente oito telas")
    return priority, capabilities, requirements, screens


def validate_package_sources(
    package: int,
    title: str,
    priority: str,
    capabilities: list[str],
    requirements: list[str],
    package_screens: list[str],
    architecture: dict[int, dict[str, str]],
    backlog: list[dict[str, str]],
    screens: list[dict[str, str]],
) -> None:
    requirement_start = int(requirements[0].removeprefix("COM-"))
    requirement_end = int(requirements[-1].removeprefix("COM-"))
    screen_start = int(package_screens[0].removeprefix("SCR-"))
    screen_end = int(package_screens[-1].removeprefix("SCR-"))
    backlog_slice = backlog[requirement_start - 1 : requirement_end]
    screen_slice = screens[screen_start - 1 : screen_end]
    checks = (
        ({item["id"] for item in backlog_slice}, set(requirements), "faixa COM"),
        (
            {item["capability_id"] for item in backlog_slice},
            set(capabilities),
            "capacidades",
        ),
        ({item["id"] for item in screen_slice}, set(package_screens), "faixa SCR"),
        (
            {item["capability_id"] for item in screen_slice},
            set(capabilities),
            "capacidades das telas",
        ),
    )
    for actual, expected, label in checks:
        if actual != expected:
            fail(f"PKG-{package} possui {label} divergente da fonte")
    domain_names = {item["domain"] for item in backlog_slice}
    if {item["domain_key"] for item in backlog_slice} != {
        architecture[package]["domain_key"]
    }:
        fail(f"PKG-{package} diverge do domain_key da matriz")
    if domain_names != {title} or {item["domain"] for item in screen_slice} != domain_names:
        fail(f"PKG-{package} diverge do nome da frente")
    if {item["priority"] for item in backlog_slice} != {priority}:
        fail(f"PKG-{package} diverge da prioridade da fonte")


def validate_package_dependencies(
    package: int, index: int, numbers: list[int], section: str
) -> None:
    dependencies = section.split("Dependências:", 1)[1].split("Entrega isolada:", 1)[0]
    if "- Base consolidada: `PKG-01` a `PKG-100`." not in dependencies:
        fail(f"PKG-{package} não referencia a base consolidada")
    community_lines = [
        line for line in dependencies.splitlines() if line.startswith("- Pacotes comunitários:")
    ]
    if len(community_lines) != 1:
        fail(f"PKG-{package} deve declarar uma linha de dependências comunitárias")
    refs = [int(value) for value in PACKAGE_REF.findall(community_lines[0])]
    if len(refs) != len(set(refs)):
        fail(f"PKG-{package} possui dependência duplicada")
    expected_refs = list(EXPECTED_DEPENDENCIES[package])
    if refs != expected_refs:
        fail(
            f"PKG-{package} possui dependências {refs}; "
            f"manifesto arquitetural exige {expected_refs}"
        )
    future = [value for value in refs if value >= package]
    if future:
        fail(f"PKG-{package} depende de pacote atual/futuro: {future}")
    missing = [value for value in refs if value not in numbers[:index]]
    if missing:
        fail(f"PKG-{package} referencia pacote comunitário inexistente: {missing}")


def validate_complete_coverage(
    capabilities: list[str], requirements: list[str], screens: list[str]
) -> None:
    expected_requirements = {f"COM-{value:04d}" for value in range(1, 3081)}
    expected_screens = {f"SCR-{value:04d}" for value in range(1, 441)}
    expected_capabilities = {
        f"CAP-{domain:02d}-{feature:02d}"
        for domain in range(1, 56)
        for feature in range(1, 9)
    }
    assignments = (
        (capabilities, expected_capabilities, "capacidades"),
        (requirements, expected_requirements, "requisitos"),
        (screens, expected_screens, "telas"),
    )
    for actual, expected, label in assignments:
        if len(actual) != len(set(actual)) or set(actual) != expected:
            fail(f"pacotes possuem lacuna ou sobreposição de {label}")


def main() -> None:
    text = DEMANDS.read_text(encoding="utf-8")
    headings = list(HEADING.finditer(text))
    numbers = [int(match.group(1)) for match in headings]
    expected = list(range(101, 156))
    if numbers != expected:
        fail(f"sequência esperada PKG-101..PKG-155, encontrada {numbers}")
    if set(EXPECTED_DEPENDENCIES) != set(expected):
        fail("manifesto arquitetural de dependências está incompleto")
    architecture = validate_architecture(expected)
    backlog, source_screens = validate_generated_sources()
    validate_standard(text)
    assigned: tuple[list[str], list[str], list[str]] = ([], [], [])
    metadata: dict[int, tuple[str, str]] = {}
    for index, heading in enumerate(headings):
        package = int(heading.group(1))
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.start() : end]
        validate_package_structure(package, section)
        priority, capabilities, requirements, screens = parse_package_coverage(
            package, section
        )
        validate_package_sources(
            package,
            heading.group(2),
            priority,
            capabilities,
            requirements,
            screens,
            architecture,
            backlog,
            source_screens,
        )
        validate_package_dependencies(package, index, numbers, section)
        for target, values in zip(assigned, (capabilities, requirements, screens)):
            target.extend(values)
        metadata[package] = (heading.group(2), priority)
    validate_complete_coverage(*assigned)
    validate_indexes(text, metadata)

    print(
        "[demand-dependencies] 55 pacotes, 440 capacidades, 3080 requisitos e "
        "440 telas em ordem topológica, com ownership e sem dependência futura"
    )


if __name__ == "__main__":
    main()
