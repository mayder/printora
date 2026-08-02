from __future__ import annotations

import math
import struct
from collections import defaultdict
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import BadZipFile, ZipFile
from xml.etree import ElementTree


MAX_TRIANGLES = 500_000
MAX_PREVIEW_TRIANGLES = 600
MAX_3MF_ENTRIES = 100
MAX_3MF_UNCOMPRESSED_BYTES = 50 * 1024 * 1024


def inspect_project_asset(file_name: str, body: bytes) -> dict[str, Any]:
    """Return bounded, deterministic geometry facts used by API and accessible UI."""
    suffix = Path(file_name).suffix.lower()
    try:
        if suffix == ".stl":
            vertices, triangles = _read_stl(body)
            source_unit = "mm"
        elif suffix == ".3mf":
            vertices, triangles, source_unit = _read_3mf(body)
        else:
            return _limited("Formato agrupado: inspecione cada STL ou 3MF separadamente.")
        if not vertices or not triangles:
            return _failed("O arquivo não contém uma malha 3D utilizável.")
        return _mesh_report(vertices, triangles, source_unit)
    except (BadZipFile, ElementTree.ParseError, UnicodeDecodeError, ValueError, struct.error) as exc:
        return _failed(str(exc) or "Não foi possível ler a geometria.")


def _read_stl(body: bytes) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    if len(body) >= 84:
        triangle_count = struct.unpack_from("<I", body, 80)[0]
        expected = 84 + triangle_count * 50
        if expected == len(body):
            if triangle_count > MAX_TRIANGLES:
                raise ValueError("A malha excede o limite seguro de triângulos.")
            vertices: list[tuple[float, float, float]] = []
            triangles: list[tuple[int, int, int]] = []
            for index in range(triangle_count):
                offset = 84 + index * 50 + 12
                base = len(vertices)
                vertices.extend(struct.unpack_from("<fff", body, offset + vertex * 12) for vertex in range(3))
                triangles.append((base, base + 1, base + 2))
            return vertices, triangles

    text = body.decode("utf-8", errors="strict")
    vertices = []
    triangles = []
    current: list[int] = []
    for raw_line in text.splitlines():
        parts = raw_line.strip().split()
        if len(parts) == 4 and parts[0].lower() == "vertex":
            vertex = tuple(float(value) for value in parts[1:])
            if not all(math.isfinite(value) for value in vertex):
                raise ValueError("A malha contém coordenadas inválidas.")
            vertices.append(vertex)  # type: ignore[arg-type]
            current.append(len(vertices) - 1)
            if len(current) == 3:
                triangles.append(tuple(current))  # type: ignore[arg-type]
                current = []
                if len(triangles) > MAX_TRIANGLES:
                    raise ValueError("A malha excede o limite seguro de triângulos.")
    return vertices, triangles


def _read_3mf(body: bytes) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]], str]:
    with ZipFile(BytesIO(body)) as archive:
        infos = archive.infolist()
        if len(infos) > MAX_3MF_ENTRIES or sum(info.file_size for info in infos) > MAX_3MF_UNCOMPRESSED_BYTES:
            raise ValueError("O pacote 3MF excede os limites seguros de inspeção.")
        model_names = [info.filename for info in infos if info.filename.lower().endswith(".model")]
        if not model_names:
            raise ValueError("O 3MF não contém um modelo reconhecível.")
        root = ElementTree.fromstring(archive.read(model_names[0]))
    unit = root.attrib.get("unit", "millimeter").lower()
    scale = {"micron": 0.001, "millimeter": 1.0, "centimeter": 10.0, "inch": 25.4, "foot": 304.8, "meter": 1000.0}.get(unit)
    if scale is None:
        raise ValueError("O 3MF declara uma unidade não suportada.")
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for element in root.iter():
        name = element.tag.rsplit("}", 1)[-1]
        if name == "vertex":
            vertex = tuple(float(element.attrib[axis]) * scale for axis in ("x", "y", "z"))
            if not all(math.isfinite(value) for value in vertex):
                raise ValueError("A malha contém coordenadas inválidas.")
            vertices.append(vertex)  # type: ignore[arg-type]
        elif name == "triangle":
            triangles.append(tuple(int(element.attrib[key]) for key in ("v1", "v2", "v3")))  # type: ignore[arg-type]
            if len(triangles) > MAX_TRIANGLES:
                raise ValueError("A malha excede o limite seguro de triângulos.")
    if any(index < 0 or index >= len(vertices) for triangle in triangles for index in triangle):
        raise ValueError("O 3MF referencia vértices inexistentes.")
    return vertices, triangles, unit


def _mesh_report(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
    source_unit: str,
) -> dict[str, Any]:
    minimum = [min(vertex[axis] for vertex in vertices) for axis in range(3)]
    maximum = [max(vertex[axis] for vertex in vertices) for axis in range(3)]
    dimensions = [maximum[axis] - minimum[axis] for axis in range(3)]
    degenerate = 0
    overhang = 0
    vertex_triangles: dict[tuple[float, float, float], list[int]] = defaultdict(list)
    for triangle_index, triangle in enumerate(triangles):
        a, b, c = (vertices[index] for index in triangle)
        normal = _cross(_subtract(b, a), _subtract(c, a))
        magnitude = math.sqrt(sum(value * value for value in normal))
        if magnitude <= 1e-9:
            degenerate += 1
        elif normal[2] / magnitude < -0.70710678:
            overhang += 1
        for vertex in (a, b, c):
            vertex_triangles[_quantize(vertex)].append(triangle_index)
    shells = _component_count(len(triangles), vertex_triangles)
    return {
        "status": "ready",
        "format": "mesh",
        "source_unit": source_unit,
        "display_unit": "mm",
        "triangle_count": len(triangles),
        "vertex_count": len(vertices),
        "dimensions_mm": {"x": round(dimensions[0], 3), "y": round(dimensions[1], 3), "z": round(dimensions[2], 3)},
        "bounds_mm": {"min": [round(value, 3) for value in minimum], "max": [round(value, 3) for value in maximum]},
        "shell_count": shells,
        "possible_islands": max(shells - 1, 0),
        "degenerate_triangles": degenerate,
        "downward_overhang_triangles": overhang,
        "downward_overhang_ratio": round(overhang / len(triangles), 4),
        "preview_supported": True,
        "preview_triangles": _preview_triangles(vertices, triangles),
        "warnings": _warnings(shells, degenerate, overhang, len(triangles)),
    }


def _preview_triangles(
    vertices: list[tuple[float, float, float]],
    triangles: list[tuple[int, int, int]],
) -> list[list[list[float]]]:
    step = max(1, math.ceil(len(triangles) / MAX_PREVIEW_TRIANGLES))
    return [
        [[round(value, 4) for value in vertices[index]] for index in triangle]
        for triangle in triangles[::step][:MAX_PREVIEW_TRIANGLES]
    ]


def _component_count(triangle_count: int, vertex_triangles: dict[tuple[float, float, float], list[int]]) -> int:
    parent = list(range(triangle_count))

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for indexes in vertex_triangles.values():
        anchor = indexes[0]
        for index in indexes[1:]:
            union(anchor, index)
    return len({find(index) for index in range(triangle_count)})


def _warnings(shells: int, degenerate: int, overhang: int, total: int) -> list[str]:
    warnings: list[str] = []
    if shells > 1:
        warnings.append(f"Foram encontrados {shells} grupos de geometria; confirme se são peças separadas.")
    if degenerate:
        warnings.append(f"A malha contém {degenerate} triângulos sem área.")
    if total and overhang / total >= 0.1:
        warnings.append("Há superfícies voltadas para baixo; revise a orientação e os suportes no fatiador.")
    return warnings


def _subtract(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return left[0] - right[0], left[1] - right[1], left[2] - right[2]


def _cross(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _quantize(vertex: tuple[float, float, float]) -> tuple[float, float, float]:
    return tuple(round(value, 6) for value in vertex)  # type: ignore[return-value]


def _limited(message: str) -> dict[str, Any]:
    return {"status": "limited", "preview_supported": False, "warnings": [message]}


def _failed(message: str) -> dict[str, Any]:
    return {"status": "failed", "preview_supported": False, "warnings": [message]}
