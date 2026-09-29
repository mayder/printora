from __future__ import annotations

import hashlib
import json
import math
import struct
from collections import defaultdict, deque
from dataclasses import dataclass
from io import BytesIO
from typing import Any, Literal
from zipfile import ZIP_DEFLATED, ZipFile

from .geometry import TriangleMesh, parse_mesh


RepairOperation = Literal["clean", "orient_normals", "close_holes", "remove_small_components", "decimate", "scale", "convert"]
OutputFormat = Literal["stl", "3mf", "obj"]


@dataclass(frozen=True)
class MeshRepairResult:
    body: bytes
    file_format: OutputFormat
    sha256: str
    manifest: dict[str, object]
    unit: str


def repair_mesh(
    body: bytes,
    file_format: str,
    operation: RepairOperation,
    parameters: dict[str, object] | None = None,
    unit: str = "unknown",
) -> MeshRepairResult:
    source = parse_mesh(body, file_format)
    safe_parameters = dict(parameters or {})
    output_format = _output_format(safe_parameters)
    output_unit = "mm" if operation == "scale" else unit
    if output_format == "3mf" and output_unit.lower() not in {"mm", "millimeter", "millimetre"}:
        raise ValueError("Confirme a unidade em milímetros antes de criar um arquivo 3MF.")
    repaired = _apply(source, operation, safe_parameters)
    output = serialize_mesh(repaired, output_format)
    checksum = hashlib.sha256(output).hexdigest()
    return MeshRepairResult(
        body=output,
        file_format=output_format,
        sha256=checksum,
        unit=output_unit,
        manifest={
            "schema": "printora.mesh-repair/v1",
            "operation": operation,
            "parameters": safe_parameters,
            "source_format": file_format.lower(),
            "output_format": output_format,
            "source_unit": unit,
            "unit": output_unit,
            "source_sha256": hashlib.sha256(body).hexdigest(),
            "output_sha256": checksum,
            "source_vertices": len(source.vertices),
            "source_triangles": len(source.triangles),
            "output_vertices": len(repaired.vertices),
            "output_triangles": len(repaired.triangles),
        },
    )


def serialize_mesh(mesh: TriangleMesh, file_format: OutputFormat) -> bytes:
    if file_format == "stl":
        return _serialize_stl(mesh)
    if file_format == "3mf":
        return _serialize_3mf(mesh)
    if file_format == "obj":
        return _serialize_obj(mesh)
    raise ValueError("Formato de saída não permitido.")


def _apply(mesh: TriangleMesh, operation: RepairOperation, parameters: dict[str, object]) -> TriangleMesh:
    if operation == "clean":
        return _clean(mesh, _positive_float(parameters.get("weld_tolerance"), 1e-6, maximum=1.0))
    if operation == "orient_normals":
        return _orient_normals(_clean(mesh, 1e-6))
    if operation == "close_holes":
        maximum = _positive_int(parameters.get("maximum_hole_edges"), 32, maximum=256)
        return _close_holes(_clean(mesh, 1e-6), maximum)
    if operation == "remove_small_components":
        minimum = _positive_int(parameters.get("minimum_triangles"), 4, maximum=100_000)
        return _remove_small_components(_clean(mesh, 1e-6), minimum)
    if operation == "decimate":
        ratio = _positive_float(parameters.get("target_ratio"), 0.75, maximum=0.95)
        if ratio < 0.1:
            raise ValueError("A redução deve preservar pelo menos 10% da malha.")
        return _decimate(_clean(mesh, 1e-6), ratio)
    if operation == "scale":
        factor = _positive_float(parameters.get("scale_factor"), 0.0, maximum=1_000.0)
        if factor < 0.001:
            raise ValueError("O fator de escala está fora do limite seguro.")
        if parameters.get("known_axis") not in {"x", "y", "z"}:
            raise ValueError("Escolha o eixo correspondente à medida conhecida.")
        _positive_float(parameters.get("known_dimension_mm"), 0.0, maximum=2_000.0)
        return TriangleMesh(
            tuple(tuple(value * factor for value in vertex) for vertex in mesh.vertices),
            mesh.triangles,
        )
    if operation == "convert":
        return mesh
    raise ValueError("Operação de reparo não permitida.")


def _clean(mesh: TriangleMesh, tolerance: float) -> TriangleMesh:
    vertices, remap = _weld_vertices(mesh.vertices, tolerance)
    triangles: list[tuple[int, int, int]] = []
    seen: set[tuple[int, int, int]] = set()
    for source in mesh.triangles:
        face = tuple(remap[index] for index in source)
        key = tuple(sorted(face))
        if len(set(face)) < 3 or key in seen or _triangle_area(vertices, face) <= tolerance * tolerance:
            continue
        seen.add(key)
        triangles.append(face)  # type: ignore[arg-type]
    return _compact(vertices, triangles)


def _orient_normals(mesh: TriangleMesh) -> TriangleMesh:
    edge_faces: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    for face_index, face in enumerate(mesh.triangles):
        for start, end in _face_edges(face):
            edge_faces[tuple(sorted((start, end)))].append((face_index, 1 if start < end else -1))
    flip: dict[int, bool] = {}
    components: list[list[int]] = []
    for seed in range(len(mesh.triangles)):
        if seed in flip:
            continue
        flip[seed] = False
        component: list[int] = []
        pending = deque([seed])
        while pending:
            face_index = pending.popleft()
            component.append(face_index)
            for start, end in _face_edges(mesh.triangles[face_index]):
                uses = edge_faces[tuple(sorted((start, end)))]
                if len(uses) != 2:
                    continue
                current_sign = (1 if start < end else -1) * (-1 if flip[face_index] else 1)
                other_index, other_sign = uses[0] if uses[1][0] == face_index else uses[1]
                expected_flip = other_sign == current_sign
                if other_index not in flip:
                    flip[other_index] = expected_flip
                    pending.append(other_index)
        components.append(component)
    faces = [_flipped(face) if flip[index] else face for index, face in enumerate(mesh.triangles)]
    for component in components:
        if _signed_volume(mesh.vertices, [faces[index] for index in component]) < 0:
            for index in component:
                faces[index] = _flipped(faces[index])
    return TriangleMesh(mesh.vertices, tuple(faces))


def _close_holes(mesh: TriangleMesh, maximum_edges: int) -> TriangleMesh:
    oriented: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    for face in mesh.triangles:
        for edge in _face_edges(face):
            oriented[tuple(sorted(edge))].append(edge)
    boundary = {uses[0] for uses in oriented.values() if len(uses) == 1}
    loops = _boundary_loops(boundary)
    vertices = list(mesh.vertices)
    faces = list(mesh.triangles)
    for loop in loops:
        if len(loop) < 3 or len(loop) > maximum_edges:
            continue
        center = tuple(sum(vertices[index][axis] for index in loop) / len(loop) for axis in range(3))
        center_index = len(vertices)
        vertices.append(center)  # type: ignore[arg-type]
        for index, start in enumerate(loop):
            end = loop[(index + 1) % len(loop)]
            faces.append((end, start, center_index))
    return _orient_normals(TriangleMesh(tuple(vertices), tuple(faces)))


def _remove_small_components(mesh: TriangleMesh, minimum_triangles: int) -> TriangleMesh:
    components = _face_components(mesh)
    selected = [component for component in components if len(component) >= minimum_triangles]
    if not selected and components:
        selected = [max(components, key=lambda item: (len(item), -min(item)))]
    indexes = {index for component in selected for index in component}
    return _compact(list(mesh.vertices), [face for index, face in enumerate(mesh.triangles) if index in indexes])


def _decimate(mesh: TriangleMesh, target_ratio: float) -> TriangleMesh:
    if len(mesh.triangles) < 8:
        return mesh
    minimum = [min(vertex[axis] for vertex in mesh.vertices) for axis in range(3)]
    maximum = [max(vertex[axis] for vertex in mesh.vertices) for axis in range(3)]
    longest = max(maximum[axis] - minimum[axis] for axis in range(3))
    target_vertices = max(4, math.ceil(len(mesh.vertices) * target_ratio))
    cluster_size = max(longest / math.sqrt(target_vertices), 1e-7)
    vertices, remap = _cluster_vertices(mesh.vertices, minimum, cluster_size)
    candidate = _clean(TriangleMesh(tuple(vertices), tuple(tuple(remap[index] for index in face) for face in mesh.triangles)), 1e-8)
    if _is_watertight(mesh) and not _is_watertight(candidate):
        raise ValueError("A redução abriria a superfície; use uma redução menor.")
    return candidate


def _weld_vertices(vertices: tuple[tuple[float, float, float], ...], tolerance: float):
    output: list[tuple[float, float, float]] = []
    indexes: dict[tuple[int, int, int], int] = {}
    remap: list[int] = []
    for vertex in vertices:
        key = tuple(round(value / tolerance) for value in vertex)
        if key not in indexes:
            indexes[key] = len(output)
            output.append(vertex)
        remap.append(indexes[key])
    return output, remap


def _cluster_vertices(vertices, minimum, size):
    sums: dict[tuple[int, int, int], list[float]] = {}
    counts: dict[tuple[int, int, int], int] = defaultdict(int)
    keys = [tuple(math.floor((vertex[axis] - minimum[axis]) / size) for axis in range(3)) for vertex in vertices]
    for key, vertex in zip(keys, vertices, strict=True):
        sums.setdefault(key, [0.0, 0.0, 0.0])
        counts[key] += 1
        for axis in range(3):
            sums[key][axis] += vertex[axis]
    ordered = sorted(sums)
    indexes = {key: index for index, key in enumerate(ordered)}
    output = [tuple(sums[key][axis] / counts[key] for axis in range(3)) for key in ordered]
    return output, [indexes[key] for key in keys]


def _compact(vertices, faces) -> TriangleMesh:
    used = sorted({index for face in faces for index in face})
    remap = {old: new for new, old in enumerate(used)}
    return TriangleMesh(tuple(vertices[index] for index in used), tuple(tuple(remap[index] for index in face) for face in faces))  # type: ignore[arg-type]


def _face_components(mesh: TriangleMesh) -> list[list[int]]:
    vertex_faces: dict[int, list[int]] = defaultdict(list)
    for index, face in enumerate(mesh.triangles):
        for vertex in face:
            vertex_faces[vertex].append(index)
    remaining = set(range(len(mesh.triangles)))
    components: list[list[int]] = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        pending = [seed]
        component: list[int] = []
        while pending:
            index = pending.pop()
            component.append(index)
            for vertex in mesh.triangles[index]:
                for neighbor in vertex_faces[vertex]:
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        pending.append(neighbor)
        components.append(sorted(component))
    return components


def _boundary_loops(edges: set[tuple[int, int]]) -> list[list[int]]:
    remaining = set(edges)
    loops: list[list[int]] = []
    while remaining:
        first = min(remaining)
        remaining.remove(first)
        loop = [first[0], first[1]]
        while loop[-1] != loop[0]:
            candidates = sorted(edge for edge in remaining if edge[0] == loop[-1])
            if not candidates:
                loop = []
                break
            edge = candidates[0]
            remaining.remove(edge)
            loop.append(edge[1])
        if loop:
            loops.append(loop[:-1])
    return loops


def _is_watertight(mesh: TriangleMesh) -> bool:
    uses: dict[tuple[int, int], int] = defaultdict(int)
    for face in mesh.triangles:
        for edge in _face_edges(face):
            uses[tuple(sorted(edge))] += 1
    return bool(uses) and all(count == 2 for count in uses.values())


def _triangle_area(vertices, face) -> float:
    a, b, c = (vertices[index] for index in face)
    ab = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    ac = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (ab[1] * ac[2] - ab[2] * ac[1], ab[2] * ac[0] - ab[0] * ac[2], ab[0] * ac[1] - ab[1] * ac[0])
    return math.sqrt(sum(value * value for value in cross))


def _signed_volume(vertices, faces) -> float:
    volume = 0.0
    for face in faces:
        a, b, c = (vertices[index] for index in face)
        volume += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0]) + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    return volume


def _serialize_obj(mesh: TriangleMesh) -> bytes:
    lines = [*(f"v {x:.9g} {y:.9g} {z:.9g}" for x, y, z in mesh.vertices), *(f"f {a + 1} {b + 1} {c + 1}" for a, b, c in mesh.triangles)]
    return ("\n".join(lines) + "\n").encode()


def _serialize_stl(mesh: TriangleMesh) -> bytes:
    output = bytearray(b"Printora deterministic mesh repair".ljust(80, b"\0"))
    output.extend(struct.pack("<I", len(mesh.triangles)))
    for face in mesh.triangles:
        a, b, c = (mesh.vertices[index] for index in face)
        output.extend(struct.pack("<3f", *_normal(a, b, c)))
        for vertex in (a, b, c):
            output.extend(struct.pack("<3f", *vertex))
        output.extend(b"\0\0")
    return bytes(output)


def _serialize_3mf(mesh: TriangleMesh) -> bytes:
    vertices = "".join(f'<vertex x="{x:.9g}" y="{y:.9g}" z="{z:.9g}"/>' for x, y, z in mesh.vertices)
    triangles = "".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in mesh.triangles)
    model = f'<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources><object id="1" type="model"><mesh><vertices>{vertices}</vertices><triangles>{triangles}</triangles></mesh></object></resources><build><item objectid="1"/></build></model>'
    content_types = '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>'
    relationships = '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>'
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        for name, value in (("[Content_Types].xml", content_types), ("_rels/.rels", relationships), ("3D/3dmodel.model", model)):
            info = __import__("zipfile").ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, value.encode())
    return stream.getvalue()


def _normal(a, b, c):
    left = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    right = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
    cross = (left[1] * right[2] - left[2] * right[1], left[2] * right[0] - left[0] * right[2], left[0] * right[1] - left[1] * right[0])
    magnitude = math.sqrt(sum(value * value for value in cross))
    return tuple(value / magnitude for value in cross) if magnitude else (0.0, 0.0, 0.0)


def _face_edges(face):
    return (face[0], face[1]), (face[1], face[2]), (face[2], face[0])


def _flipped(face):
    return face[0], face[2], face[1]


def _output_format(parameters: dict[str, object]) -> OutputFormat:
    value = str(parameters.get("output_format", "stl")).lower()
    if value not in {"stl", "3mf", "obj"}:
        raise ValueError("Escolha STL, 3MF ou OBJ para a saída.")
    return value  # type: ignore[return-value]


def _positive_int(value: object, default: int, *, maximum: int) -> int:
    parsed = default if value is None else int(value)
    if parsed <= 0 or parsed > maximum:
        raise ValueError("Parâmetro inteiro fora do limite seguro.")
    return parsed


def _positive_float(value: object, default: float, *, maximum: float) -> float:
    parsed = default if value is None else float(value)
    if not math.isfinite(parsed) or parsed <= 0 or parsed > maximum:
        raise ValueError("Parâmetro numérico fora do limite seguro.")
    return parsed
