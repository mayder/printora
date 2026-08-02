#!/usr/bin/env python3
"""Exercita falhas estruturais bloqueadas pelo gate do portfólio ativo."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-demand-package-dependencies.py"
DEMANDS = ROOT / "DEMANDAS.md"
ARCHITECTURE = ROOT / "docs" / "community" / "PACKAGE_ARCHITECTURE.csv"
PORTFOLIO = ROOT / "docs" / "community" / "PACKAGE_PORTFOLIO.csv"


def run(
    demands: Path,
    architecture: Path,
    portfolio: Path,
    expected: str,
) -> None:
    result = subprocess.run(
        [
            "python3",
            str(VALIDATOR),
            str(demands),
            str(architecture),
            str(portfolio),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 1 or expected not in result.stderr:
        raise AssertionError(
            f"falha esperada não ocorreu: exit={result.returncode}, "
            f"stderr={result.stderr!r}"
        )


def main() -> None:
    demands = DEMANDS.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    portfolio = PORTFOLIO.read_text(encoding="utf-8")
    cases = {
        "missing-active": (
            demands.replace(
                "## PKG-142: Integrações e descoberta técnica",
                "## IDEA-142: Integrações e descoberta técnica",
                1,
            ),
            architecture,
            portfolio,
            "exatamente os pacotes ativos",
        ),
        "dependency-drift": (
            demands.replace(
                "- Pacotes ativos: `PKG-114`, `PKG-128`.",
                "- Pacotes ativos: `PKG-128`.",
                1,
            ),
            architecture,
            portfolio,
            "matriz arquitetural exige",
        ),
        "dependency-after": (
            demands.replace(
                "- Pacotes ativos: nenhum.",
                "- Pacotes ativos: `PKG-142`.",
                1,
            ),
            architecture.replace(
                "integrations,operations,high,PKG-104",
                "integrations,operations,high,PKG-104|PKG-142",
                1,
            ),
            portfolio,
            "pacote ativo ausente ou posterior",
        ),
        "owner": (
            demands,
            architecture.replace(
                "PKG-114,materials_quality,operations,",
                "PKG-114,materials_quality,unknown,",
                1,
            ),
            portfolio,
            "owner inválido",
        ),
        "merged-target": (
            demands,
            architecture,
            portfolio.replace(
                "PKG-105,merged,PKG-104,",
                "PKG-105,merged,PKG-109,",
                1,
            ),
            "fundido em pacote indisponível",
        ),
        "missing-acceptance": (
            demands.replace("Critério de aceite:", "Aceite:", 1),
            architecture,
            portfolio,
            "deve possuir uma seção Critério de aceite:",
        ),
    }

    with tempfile.TemporaryDirectory(prefix="printora-demand-validator-") as directory:
        root = Path(directory)
        for name, (demand_text, architecture_text, portfolio_text, expected) in cases.items():
            demand_path = root / f"{name}.md"
            architecture_path = root / f"{name}-architecture.csv"
            portfolio_path = root / f"{name}-portfolio.csv"
            demand_path.write_text(demand_text, encoding="utf-8")
            architecture_path.write_text(architecture_text, encoding="utf-8")
            portfolio_path.write_text(portfolio_text, encoding="utf-8")
            run(demand_path, architecture_path, portfolio_path, expected)
    print("[demand-dependencies-test] cenários negativos bloqueados")


if __name__ == "__main__":
    main()
