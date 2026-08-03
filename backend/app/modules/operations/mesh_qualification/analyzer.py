from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

from .geometry import TriangleMesh, parse_mesh
from .spatial import count_self_intersections, estimate_minimum_thickness


KNOWN_UNITS = {"mm", "millimeter", "millimetre"}


def qualify_mesh(body: bytes, file_format: str, unit: str) -> dict[str, Any]:
    """Return deterministic facts; missing mandatory checks always block approval."""
    try:
        mesh = parse_mesh(body, file_format)
    except (KeyError, IndexError, TypeError, UnicodeDecodeError, ValueError) as exc:
        return _failed(str(exc) or "Não foi possível ler a malha.")
    return _analyze(mesh, file_format.lower(), unit.lower().strip())


def _analyze(mesh: TriangleMesh, file_format: str, unit: str) -> dict[str, Any]:
    minimum = [min(vertex[axis] for vertex in mesh.vertices) for axis in range(3)]
    maximum = [max(vertex[axis] for vertex in mesh.vertices) for axis in range(3)]
    dimensions = [maximum[axis] - minimum[axis] for axis in range(3)]
    tolerance = max(max(dimensions) * 1e-8, 1e-7)
    welded, faces = _weld(mesh, tolerance)
    valid_faces: list[tuple[int, int, int]] = []
    degenerate = 0
    for face in faces:
        a, b, c = (welded[index] for index in face)
        if len(set(face)) < 3 or _area_twice(a, b, c) <= tolerance * tolerance:
            degenerate += 1
        else:
            valid_faces.append(face)
    edges: dict[tuple[int, int], list[int]] = defaultdict(list)
    face_vertices: dict[int, list[int]] = defaultdict(list)
    for face_index, face in enumerate(valid_faces):
        for start, end in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            edges[tuple(sorted((start, end)))].append(1 if start < end else -1)
            face_vertices[start].append(face_index)
            face_vertices[end].append(face_index)
    boundary_edges = [edge for edge, uses in edges.items() if len(uses) == 1]
    non_manifold_edges = sum(1 for uses in edges.values() if len(uses) > 2)
    winding_conflicts = sum(1 for uses in edges.values() if len(uses) == 2 and uses[0] == uses[1])
    components = _component_count(len(valid_faces), face_vertices)
    hole_count = _boundary_component_count(boundary_edges)
    watertight = bool(valid_faces) and not boundary_edges and not non_manifold_edges
    signed_volume = sum(_signed_tetrahedron_volume(*(welded[index] for index in face)) for face in valid_faces)
    self_intersections = count_self_intersections(welded, valid_faces, tolerance)
    minimum_thickness = (
        estimate_minimum_thickness(welded, valid_faces, tolerance, signed_volume)
        if watertight and not winding_conflicts else None
    )
    unit_known = unit in KNOWN_UNITS
    normals_inverted = watertight and signed_volume < 0
    blockers = _blockers(
        unit_known=unit_known,
        watertight=watertight,
        non_manifold_edges=non_manifold_edges,
        winding_conflicts=winding_conflicts,
        degenerate=degenerate,
        components=components,
        normals_inverted=normals_inverted,
        self_intersections=self_intersections,
    )
    checks = {
        "watertight": watertight,
        "manifold": non_manifold_edges == 0,
        "boundary_edge_count": len(boundary_edges),
        "hole_count": hole_count,
        "non_manifold_edge_count": non_manifold_edges,
        "winding_conflict_count": winding_conflicts,
        "inverted_closed_volume": normals_inverted,
        "component_count": components,
        "degenerate_triangle_count": degenerate,
        "self_intersection_count": self_intersections if self_intersections is not None else "limit_exceeded",
        "minimum_thickness_estimate": round(minimum_thickness, 4) if minimum_thickness is not None else "not_available",
    }
    return _report(mesh, file_format, unit, unit_known, welded, minimum, maximum, dimensions, checks, blockers)


def _report(mesh, file_format, unit, unit_known, welded, minimum, maximum, dimensions, checks, blockers) -> dict[str, Any]:
    return {
        "schema": "printora.mesh-qualification/v1",
        "status": "not_qualified",
        "file_format": file_format,
        "source_unit": unit or "unknown",
        "display_unit": "mm" if unit_known else "unknown",
        "vertex_count": len(mesh.vertices),
        "welded_vertex_count": len(welded),
        "triangle_count": len(mesh.triangles),
        "dimensions": {"x": round(dimensions[0], 4), "y": round(dimensions[1], 4), "z": round(dimensions[2], 4)},
        "bounds": {"min": [round(value, 4) for value in minimum], "max": [round(value, 4) for value in maximum]},
        "checks": checks,
        "mandatory_checks_complete": False,
        "blockers": blockers + ["A espessura estimada ainda precisa ser comparada com a impressora e o perfil."],
        "next_action": "Revise os pontos indicados antes de aprovar ou baixar para impressão.",
    }


def _weld(mesh: TriangleMesh, tolerance: float) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
    vertices: list[tuple[float, float, float]] = []
    indexes: dict[tuple[int, int, int], int] = {}
    remap: list[int] = []
    for vertex in mesh.vertices:
        key = tuple(round(value / tolerance) for value in vertex)
        if key not in indexes:
            indexes[key] = len(vertices)
            vertices.append(vertex)
        remap.append(indexes[key])
    return vertices, [tuple(remap[index] for index in face) for face in mesh.triangles]  # type: ignore[return-value]


def _area_twice(a: tuple[float, float, float], b: tuple[float, float, float], c: tuple[float, float, float]) -> float:
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
    return math.sqrt(sum(value * value for value in cross))


def _signed_tetrahedron_volume(a, b, c) -> float:
    return (
        a[0] * (b[1] * c[2] - b[2] * c[1])
        - a[1] * (b[0] * c[2] - b[2] * c[0])
        + a[2] * (b[0] * c[1] - b[1] * c[0])
    ) / 6.0


def _component_count(face_count: int, face_vertices: dict[int, list[int]]) -> int:
    if face_count == 0:
        return 0
    parent = list(range(face_count))

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    for faces in face_vertices.values():
        root = find(faces[0])
        for face in faces[1:]:
            parent[find(face)] = root
    return len({find(value) for value in range(face_count)})


def _boundary_component_count(edges: list[tuple[int, int]]) -> int:
    if not edges:
        return 0
    graph: dict[int, set[int]] = defaultdict(set)
    for left, right in edges:
        graph[left].add(right)
        graph[right].add(left)
    remaining = set(graph)
    count = 0
    while remaining:
        count += 1
        pending = [remaining.pop()]
        while pending:
            for neighbor in graph[pending.pop()]:
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    pending.append(neighbor)
    return count


def _blockers(*, unit_known: bool, watertight: bool, non_manifold_edges: int, winding_conflicts: int, degenerate: int, components: int, normals_inverted: bool, self_intersections: int | None) -> list[str]:
    blockers: list[str] = []
    if not unit_known:
        blockers.append("Confirme a unidade e uma medida conhecida do objeto.")
    if not watertight:
        blockers.append("A superfície está aberta e precisa ter seus buracos revisados.")
    if non_manifold_edges:
        blockers.append("Há junções que não formam uma superfície imprimível.")
    if winding_conflicts:
        blockers.append("Há superfícies apontando para direções incompatíveis.")
    if normals_inverted:
        blockers.append("A superfície fechada está orientada para dentro e precisa ser corrigida.")
    if self_intersections is None:
        blockers.append("A malha é complexa demais para conferir todos os cruzamentos com segurança.")
    elif self_intersections:
        blockers.append(f"Foram encontrados {self_intersections} cruzamentos internos na superfície.")
    if degenerate:
        blockers.append("Há triângulos sem área que precisam ser limpos.")
    if components > 1:
        blockers.append(f"Foram encontrados {components} grupos separados; confirme quais pertencem ao objeto.")
    return blockers


def _failed(message: str) -> dict[str, Any]:
    return {
        "schema": "printora.mesh-qualification/v1",
        "status": "failed",
        "mandatory_checks_complete": False,
        "blockers": [message],
        "next_action": "Use novamente a malha original ou gere outra reconstrução.",
    }
