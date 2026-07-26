#!/usr/bin/env python3
"""Exercita falhas estruturais que o gate comunitário deve bloquear."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate-demand-package-dependencies.py"
DEMANDS = ROOT / "DEMANDAS.md"
ARCHITECTURE = ROOT / "docs" / "community" / "PACKAGE_ARCHITECTURE.csv"


def run(demands: Path, architecture: Path, expected: str) -> None:
    result = subprocess.run(
        ["python3", str(VALIDATOR), str(demands), str(architecture)],
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


def demand_cases(
    demands: str,
    architecture: str,
) -> dict[str, tuple[str, str, str]]:
    return {
        "future.md": (
            demands.replace(
                "- Pacotes comunitários: nenhum.",
                "- Pacotes comunitários: `PKG-155`.",
                1,
            ),
            architecture,
            "manifesto arquitetural exige",
        ),
        "missing.md": (
            demands.replace(
                "- Pacotes comunitários: `PKG-101`.",
                "- Pacotes comunitários: nenhum.",
                1,
            ),
            architecture,
            "manifesto arquitetural exige",
        ),
        "coverage.md": (
            demands.replace(
                "- requisitos: `COM-0953` a `COM-1008` — 56 itens;",
                "- requisitos: `COM-0954` a `COM-1008` — 55 itens;",
                1,
            ),
            architecture,
            "exatamente 56 requisitos",
        ),
        "screen.md": (
            demands.replace(
                "- telas: `SCR-0137` a `SCR-0144` — 8 famílias;",
                "- telas: `SCR-0138` a `SCR-0144` — 7 famílias;",
                1,
            ),
            architecture,
            "exatamente oito telas",
        ),
        "index.md": (
            demands.replace(
                "- PKG-101 [P1]:",
                "- PKG-101 [P0]:",
                1,
            ),
            architecture,
            "índice de implementação diverge",
        ),
    }


def architecture_cases(
    demands: str,
    architecture: str,
) -> dict[str, tuple[str, str, str]]:
    return {
        "owner.md": (
            demands,
            architecture.replace(
                ",shared,administration,platform,high",
                ",unknown,administration,platform,high",
                1,
            ),
            "owner inválido",
        ),
        "domain.md": (
            demands,
            architecture.replace(
                "PKG-102,accessibility,",
                "PKG-102,design_system,",
                1,
            ),
            "domain_key duplicado",
        ),
        "package.md": (
            demands,
            architecture.replace(
                "PKG-155,future_interfaces,shared,community|operations,platform,critical\n",
                "",
                1,
            ),
            "não cobre exatamente",
        ),
    }


def main() -> None:
    demands = DEMANDS.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    cases = demand_cases(demands, architecture)
    cases.update(architecture_cases(demands, architecture))
    with tempfile.TemporaryDirectory(prefix="printora-demand-validator-") as directory:
        root = Path(directory)
        for name, (demand_text, architecture_text, expected) in cases.items():
            demand_path = root / name
            architecture_path = root / f"{name}.csv"
            demand_path.write_text(demand_text, encoding="utf-8")
            architecture_path.write_text(architecture_text, encoding="utf-8")
            run(demand_path, architecture_path, expected)
    print("[demand-dependencies-test] cenários negativos bloqueados")


if __name__ == "__main__":
    main()
