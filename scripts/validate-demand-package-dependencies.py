#!/usr/bin/env python3
"""Bloqueia lacunas e dependências futuras no backlog comunitário."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEMANDS = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "DEMANDAS.md"
HEADING = re.compile(r"^## PKG-(\d+): (.+)$", re.MULTILINE)
PACKAGE_REF = re.compile(r"`PKG-(\d+)`")
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


def main() -> None:
    text = DEMANDS.read_text(encoding="utf-8")
    headings = list(HEADING.finditer(text))
    numbers = [int(match.group(1)) for match in headings]
    expected = list(range(101, 156))
    if numbers != expected:
        fail(f"sequência esperada PKG-101..PKG-155, encontrada {numbers}")
    if set(EXPECTED_DEPENDENCIES) != set(expected):
        fail("manifesto arquitetural de dependências está incompleto")

    for index, heading in enumerate(headings):
        package = int(heading.group(1))
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        section = text[heading.start() : end]
        if section.count("Dependências:") != 1:
            fail(f"PKG-{package} deve possuir uma seção Dependências")
        if section.count("Entrega isolada:") != 1:
            fail(f"PKG-{package} deve possuir uma seção Entrega isolada")
        if "nenhum pacote de ID maior é necessário" not in section:
            fail(f"PKG-{package} não declara independência de pacote futuro")
        if section.count("Lotes de capacidade:") != 1:
            fail(f"PKG-{package} deve possuir lotes de capacidade")
        if section.count("Critério de aceite:") != 1:
            fail(f"PKG-{package} deve possuir critérios de aceite")
        if section.count("Rollback:") != 1:
            fail(f"PKG-{package} deve possuir rollback")
        if section.count("Estado atual:") != 1:
            fail(f"PKG-{package} deve possuir estado atual")
        if "reexecução idempotente" not in section:
            fail(f"PKG-{package} não exige teste de reexecução idempotente")
        lots = re.findall(r"^(\d+)\. \*\*", section, re.MULTILINE)
        if lots != [str(value) for value in range(1, 11)]:
            fail(f"PKG-{package} deve possuir lotes numerados de 1 a 10")

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

    print("[demand-dependencies] 55 pacotes em ordem topológica, sem dependência futura")


if __name__ == "__main__":
    main()
