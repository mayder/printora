#!/usr/bin/env python3
"""Valida o portfólio ativo e suas dependências técnicas explícitas."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMANDS = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "DEMANDAS.md"
COMMUNITY = ROOT / "docs" / "community"
ARCHITECTURE = (
    Path(sys.argv[2]).resolve()
    if len(sys.argv) > 2
    else COMMUNITY / "PACKAGE_ARCHITECTURE.csv"
)
PORTFOLIO = (
    Path(sys.argv[3]).resolve()
    if len(sys.argv) > 3
    else COMMUNITY / "PACKAGE_PORTFOLIO.csv"
)
STANDARD = COMMUNITY / "PACKAGE_EXECUTION_STANDARD.md"

HEADING = re.compile(r"^## PKG-(\d{3}): (.+)$", re.MULTILINE)
PACKAGE_REF = re.compile(r"`PKG-(\d{3})`")
PRIORITY = re.compile(r"^Prioridade: (P[0-4])\.$", re.MULTILINE)
STATUS_VALUES = {"active", "completed", "merged", "deferred", "cancelled"}
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


def fail(message: str) -> None:
    print(f"[demand-dependencies] ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_package_id(value: str, context: str) -> int:
    match = re.fullmatch(r"PKG-(\d{3})", value)
    if not match:
        fail(f"{context} possui package_id inválido: {value}")
    return int(match.group(1))


def parse_refs(value: str, context: str) -> list[int]:
    if not value:
        return []
    refs: list[int] = []
    for item in value.split("|"):
        refs.append(parse_package_id(item, context))
    if len(refs) != len(set(refs)):
        fail(f"{context} possui dependência duplicada")
    return refs


def validate_portfolio() -> dict[int, dict[str, str]]:
    rows = read_csv(PORTFOLIO)
    required = {"package_id", "status", "target_package", "decision"}
    if not rows or set(rows[0]) != required:
        fail("PACKAGE_PORTFOLIO.csv possui colunas divergentes")

    portfolio: dict[int, dict[str, str]] = {}
    for row in rows:
        package = parse_package_id(row["package_id"], "portfólio")
        if package in portfolio:
            fail(f"PKG-{package} duplicado no portfólio")
        status = row["status"]
        if status not in STATUS_VALUES:
            fail(f"PKG-{package} possui status inválido: {status}")
        if not row["decision"].strip():
            fail(f"PKG-{package} não possui decisão registrada")
        target = row["target_package"]
        if status == "merged":
            if not target:
                fail(f"PKG-{package} fundido não declara destino")
            parse_package_id(target, f"PKG-{package}")
        elif target:
            fail(f"PKG-{package} não fundido declara destino")
        portfolio[package] = row

    expected = list(range(101, 156))
    if sorted(portfolio) != expected:
        fail(f"portfólio deve cobrir PKG-101..PKG-155: {sorted(portfolio)}")

    merge_targets = {
        package
        for package, row in portfolio.items()
        if row["status"] in {"active", "completed"}
    }
    for package, row in portfolio.items():
        if row["status"] != "merged":
            continue
        target = parse_package_id(row["target_package"], f"PKG-{package}")
        if target not in merge_targets:
            fail(f"PKG-{package} foi fundido em pacote indisponível: PKG-{target}")
    return portfolio


def validate_architecture(
    expected_packages: list[int],
) -> tuple[dict[int, dict[str, str]], dict[int, list[int]]]:
    rows = read_csv(ARCHITECTURE)
    required = {
        "package_id",
        "domain_key",
        "primary_backend_owner",
        "backend_collaborators",
        "frontend_area",
        "risk_profile",
        "dependencies",
    }
    if not rows or set(rows[0]) != required:
        fail("PACKAGE_ARCHITECTURE.csv possui colunas divergentes")

    packages: dict[int, dict[str, str]] = {}
    dependencies: dict[int, list[int]] = {}
    domain_keys: set[str] = set()
    for row in rows:
        package = parse_package_id(row["package_id"], "matriz arquitetural")
        if package in packages:
            fail(f"PKG-{package} duplicado na matriz")
        domain_key = row["domain_key"]
        if not re.fullmatch(r"[a-z][a-z0-9_]*", domain_key):
            fail(f"PKG-{package} possui domain_key inválido")
        if domain_key in domain_keys:
            fail(f"domain_key duplicado na matriz: {domain_key}")
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
        dependencies[package] = parse_refs(
            row["dependencies"], f"PKG-{package} na matriz"
        )
        domain_keys.add(domain_key)

    if sorted(packages) != expected_packages:
        fail(
            "matriz arquitetural não cobre exatamente os pacotes ativos: "
            f"esperado={expected_packages}, atual={sorted(packages)}"
        )
    return packages, dependencies


def validate_standard(text: str) -> None:
    required_references = {
        "docs/community/PACKAGE_ARCHITECTURE.csv",
        "docs/community/PACKAGE_EXECUTION_STANDARD.md",
        "docs/community/PACKAGE_MODELING_REVIEW.md",
        "docs/community/PACKAGE_PORTFOLIO.csv",
    }
    first_heading = HEADING.search(text)
    preamble = text[: first_heading.start()] if first_heading else text
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
        "## Testes Por Perfil De Risco",
        "## Compatibilidade E Proteção Do Legado",
        "## Definition Of Done Do Pacote",
        "## Handoff Para Outra Janela",
    }
    absent = sorted(value for value in required_headings if value not in standard)
    if absent:
        fail(f"padrão de execução incompleto: {absent}")


def parse_document_dependencies(package: int, section: str) -> list[int]:
    dependencies = section.split("Dependências:", 1)[1].split(
        "Escopo incluído:", 1
    )[0]
    lines = [
        line
        for line in dependencies.splitlines()
        if line.startswith("- Pacotes concluídos:")
        or line.startswith("- Pacotes ativos:")
    ]
    if len(lines) != 2:
        fail(
            f"PKG-{package} deve declarar dependências concluídas e ativas separadamente"
        )
    refs: list[int] = []
    for line in lines:
        refs.extend(int(value) for value in PACKAGE_REF.findall(line))
    if len(refs) != len(set(refs)):
        fail(f"PKG-{package} possui dependência duplicada")
    return refs


def validate_package_structure(package: int, section: str) -> str:
    required_sections = (
        "Valor para o usuário:",
        "Dependências:",
        "Escopo incluído:",
        "Fora do escopo:",
        "Lotes:",
        "Critério de aceite:",
        "Rollback:",
        "Estado atual:",
    )
    for label in required_sections:
        if section.count(label) != 1:
            fail(f"PKG-{package} deve possuir uma seção {label}")
    if "reexecução idempotente" not in section:
        fail(f"PKG-{package} não exige reexecução idempotente")
    lots = [int(value) for value in re.findall(r"^(\d+)\. \*\*", section, re.MULTILINE)]
    if len(lots) < 3 or lots != list(range(1, len(lots) + 1)):
        fail(f"PKG-{package} possui lotes inválidos: {lots}")
    match = PRIORITY.search(section)
    if not match:
        fail(f"PKG-{package} não declara prioridade")
    return match.group(1)


def validate_indexes(
    text: str, headings: list[re.Match[str]], priorities: dict[int, str]
) -> None:
    try:
        order = text.split("## Ordem Ativa De Implementação", 1)[1].split(
            "## Portfólio Reavaliado", 1
        )[0]
    except IndexError:
        fail("DEMANDAS.md não possui índice ativo delimitado")
    rows = re.findall(r"^- PKG-(\d{3}) \[(P[0-4])\]: (.+)$", order, re.MULTILINE)
    expected = [
        (match.group(1), priorities[int(match.group(1))], match.group(2))
        for match in headings
    ]
    if rows != expected:
        fail("ordem ativa diverge das seções dos pacotes")


def validate_dependencies(
    package: int,
    index: int,
    active_order: list[int],
    document_refs: list[int],
    expected_refs: list[int],
    portfolio: dict[int, dict[str, str]],
) -> None:
    if document_refs != expected_refs:
        fail(
            f"PKG-{package} possui dependências {document_refs}; "
            f"matriz arquitetural exige {expected_refs}"
        )
    for dependency in document_refs:
        status = portfolio[dependency]["status"]
        if status == "completed":
            continue
        if status != "active":
            fail(
                f"PKG-{package} depende de PKG-{dependency} com status {status}"
            )
        if dependency not in active_order[:index]:
            fail(
                f"PKG-{package} depende de pacote ativo ausente ou posterior: "
                f"PKG-{dependency}"
            )


def main() -> None:
    text = DEMANDS.read_text(encoding="utf-8")
    portfolio = validate_portfolio()
    expected_active = [
        package for package, row in portfolio.items() if row["status"] == "active"
    ]
    headings = list(HEADING.finditer(text))
    active_order = [int(match.group(1)) for match in headings]
    if set(active_order) != set(expected_active) or len(active_order) != len(
        set(active_order)
    ):
        fail(
            "DEMANDAS.md deve conter exatamente os pacotes ativos: "
            f"esperado={expected_active}, atual={active_order}"
        )

    _, architecture_dependencies = validate_architecture(expected_active)
    validate_standard(text)
    priorities: dict[int, str] = {}
    for index, heading in enumerate(headings):
        package = int(heading.group(1))
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.start() : end]
        priorities[package] = validate_package_structure(package, section)
        document_refs = parse_document_dependencies(package, section)
        validate_dependencies(
            package,
            index,
            active_order,
            document_refs,
            architecture_dependencies[package],
            portfolio,
        )
    validate_indexes(text, headings, priorities)

    print(
        "[demand-dependencies] "
        f"{len(active_order)} pacotes ativos em ordem topológica explícita; "
        "portfólio PKG-101..PKG-155 rastreado"
    )


if __name__ == "__main__":
    main()
