from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from io import BytesIO
from xml.etree import ElementTree
from zipfile import BadZipFile, ZipFile


MAX_MESH_BYTES = 500 * 1024 * 1024
MAX_VERTICES = 1_500_000
MAX_TRIANGLES = 500_000


@dataclass(frozen=True)
class TriangleMesh:
    vertices: tuple[tuple[float, float, float], ...]
    triangles: tuple[tuple[int, int, int], ...]


def parse_mesh(body: bytes, file_format: str) -> TriangleMesh:
    if not body or len(body) > MAX_MESH_BYTES:
        raise ValueError("O arquivo está vazio ou excede o limite seguro.")
    readers = {"stl": _read_stl, "obj": _read_obj, "ply": _read_ply, "glb": _read_glb, "3mf": _read_3mf}
    reader = readers.get(file_format.lower())
    if reader is None:
        raise ValueError("Este formato de malha ainda não pode ser qualificado.")
    mesh = reader(body)
    if not mesh.vertices or not mesh.triangles:
        raise ValueError("O arquivo não contém uma superfície 3D utilizável.")
    if len(mesh.vertices) > MAX_VERTICES or len(mesh.triangles) > MAX_TRIANGLES:
        raise ValueError("A malha excede o limite seguro de análise.")
    if any(not all(math.isfinite(value) for value in vertex) for vertex in mesh.vertices):
        raise ValueError("A malha contém coordenadas inválidas.")
    if any(index < 0 or index >= len(mesh.vertices) for face in mesh.triangles for index in face):
        raise ValueError("A malha referencia vértices inexistentes.")
    return mesh


def _read_obj(body: bytes) -> TriangleMesh:
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for raw_line in body.decode("utf-8", errors="strict").splitlines():
        parts = raw_line.strip().split()
        if len(parts) >= 4 and parts[0] == "v":
            vertices.append(tuple(float(value) for value in parts[1:4]))  # type: ignore[arg-type]
        elif len(parts) >= 4 and parts[0] == "f":
            indexes = [_obj_index(value, len(vertices)) for value in parts[1:]]
            for offset in range(1, len(indexes) - 1):
                triangles.append((indexes[0], indexes[offset], indexes[offset + 1]))
    return TriangleMesh(tuple(vertices), tuple(triangles))


def _read_3mf(body: bytes) -> TriangleMesh:
    try:
        with ZipFile(BytesIO(body)) as archive:
            entries = archive.infolist()
            if len(entries) > 100 or sum(entry.file_size for entry in entries) > MAX_MESH_BYTES:
                raise ValueError("O pacote 3MF excede os limites seguros.")
            models = [entry.filename for entry in entries if entry.filename.lower().endswith(".model")]
            if not models:
                raise ValueError("O 3MF não contém um modelo reconhecível.")
            root = ElementTree.fromstring(archive.read(models[0]))
    except (BadZipFile, ElementTree.ParseError) as exc:
        raise ValueError("O pacote 3MF está danificado.") from exc
    unit = root.attrib.get("unit", "millimeter").lower()
    scale = {"micron": 0.001, "millimeter": 1.0, "centimeter": 10.0, "inch": 25.4, "foot": 304.8, "meter": 1000.0}.get(unit)
    if scale is None:
        raise ValueError("O 3MF declara uma unidade não suportada.")
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for element in root.iter():
        name = element.tag.rsplit("}", 1)[-1]
        if name == "vertex":
            vertices.append(tuple(float(element.attrib[axis]) * scale for axis in ("x", "y", "z")))  # type: ignore[arg-type]
        elif name == "triangle":
            triangles.append(tuple(int(element.attrib[key]) for key in ("v1", "v2", "v3")))  # type: ignore[arg-type]
    return TriangleMesh(tuple(vertices), tuple(triangles))


def _obj_index(value: str, vertex_count: int) -> int:
    raw = int(value.split("/", 1)[0])
    if raw == 0:
        raise ValueError("O OBJ contém um índice de vértice inválido.")
    return raw - 1 if raw > 0 else vertex_count + raw


def _read_stl(body: bytes) -> TriangleMesh:
    if len(body) >= 84:
        count = struct.unpack_from("<I", body, 80)[0]
        if 84 + count * 50 == len(body):
            vertices: list[tuple[float, float, float]] = []
            triangles: list[tuple[int, int, int]] = []
            for face_index in range(count):
                offset = 84 + face_index * 50 + 12
                base = len(vertices)
                vertices.extend(struct.unpack_from("<fff", body, offset + item * 12) for item in range(3))
                triangles.append((base, base + 1, base + 2))
            return TriangleMesh(tuple(vertices), tuple(triangles))
    vertices = []
    triangles = []
    current: list[int] = []
    for raw_line in body.decode("utf-8", errors="strict").splitlines():
        parts = raw_line.strip().split()
        if len(parts) == 4 and parts[0].lower() == "vertex":
            vertices.append(tuple(float(value) for value in parts[1:]))  # type: ignore[arg-type]
            current.append(len(vertices) - 1)
            if len(current) == 3:
                triangles.append(tuple(current))  # type: ignore[arg-type]
                current = []
    return TriangleMesh(tuple(vertices), tuple(triangles))


def _read_ply(body: bytes) -> TriangleMesh:
    marker = b"end_header\n"
    header_end = body.find(marker)
    marker_size = len(marker)
    if header_end < 0:
        marker = b"end_header\r\n"
        header_end = body.find(marker)
        marker_size = len(marker)
    if header_end < 0:
        raise ValueError("O PLY não possui um cabeçalho válido.")
    header = body[:header_end].decode("ascii", errors="strict").splitlines()
    if "format ascii 1.0" not in header:
        raise ValueError("Somente PLY ASCII pode ser qualificado nesta versão.")
    vertex_count = _ply_element_count(header, "vertex")
    face_count = _ply_element_count(header, "face")
    lines = body[header_end + marker_size:].decode("utf-8", errors="strict").splitlines()
    if len(lines) < vertex_count + face_count:
        raise ValueError("O PLY terminou antes da geometria declarada.")
    vertices = [tuple(float(value) for value in lines[index].split()[:3]) for index in range(vertex_count)]
    triangles: list[tuple[int, int, int]] = []
    for line in lines[vertex_count:vertex_count + face_count]:
        values = [int(value) for value in line.split()]
        indexes = values[1:1 + values[0]]
        for offset in range(1, len(indexes) - 1):
            triangles.append((indexes[0], indexes[offset], indexes[offset + 1]))
    return TriangleMesh(tuple(vertices), tuple(triangles))  # type: ignore[arg-type]


def _ply_element_count(header: list[str], name: str) -> int:
    prefix = f"element {name} "
    for line in header:
        if line.startswith(prefix):
            return int(line[len(prefix):])
    return 0


def _read_glb(body: bytes) -> TriangleMesh:
    if len(body) < 20 or body[:4] != b"glTF" or struct.unpack_from("<I", body, 4)[0] != 2:
        raise ValueError("O GLB não possui um cabeçalho válido.")
    declared_size = struct.unpack_from("<I", body, 8)[0]
    if declared_size != len(body):
        raise ValueError("O GLB está incompleto.")
    chunks: dict[int, bytes] = {}
    offset = 12
    while offset + 8 <= len(body):
        size, kind = struct.unpack_from("<II", body, offset)
        offset += 8
        chunks[kind] = body[offset:offset + size]
        offset += size
    try:
        document = json.loads(chunks[0x4E4F534A].decode("utf-8"))
        binary = chunks[0x004E4942]
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("O GLB não contém geometria incorporada válida.") from exc
    vertices: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    for mesh in document.get("meshes", []):
        for primitive in mesh.get("primitives", []):
            if primitive.get("mode", 4) != 4 or "POSITION" not in primitive.get("attributes", {}):
                continue
            local = _glb_accessor(document, binary, primitive["attributes"]["POSITION"])
            if any(len(item) != 3 for item in local):
                raise ValueError("O GLB possui posições incompatíveis.")
            indexes = (
                [int(item[0]) for item in _glb_accessor(document, binary, primitive["indices"])]
                if "indices" in primitive else list(range(len(local)))
            )
            base = len(vertices)
            vertices.extend(tuple(float(value) for value in item) for item in local)  # type: ignore[arg-type]
            for index in range(0, len(indexes) - 2, 3):
                triangles.append(tuple(base + value for value in indexes[index:index + 3]))  # type: ignore[arg-type]
    return TriangleMesh(tuple(vertices), tuple(triangles))


def _glb_accessor(document: dict[str, object], binary: bytes, accessor_index: int) -> list[tuple[float, ...]]:
    accessors = document.get("accessors")
    views = document.get("bufferViews")
    if not isinstance(accessors, list) or not isinstance(views, list):
        raise ValueError("O GLB não descreve seus buffers.")
    accessor = accessors[accessor_index]
    if not isinstance(accessor, dict) or "bufferView" not in accessor or accessor.get("sparse") is not None:
        raise ValueError("O GLB usa um tipo de buffer ainda não suportado.")
    view = views[int(accessor["bufferView"])]
    if not isinstance(view, dict) or int(view.get("buffer", 0)) != 0:
        raise ValueError("O GLB usa um buffer externo não permitido.")
    component = int(accessor["componentType"])
    formats = {5121: ("B", 1), 5123: ("H", 2), 5125: ("I", 4), 5126: ("f", 4)}
    if component not in formats:
        raise ValueError("O GLB usa um componente numérico não suportado.")
    count_by_type = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
    width = count_by_type.get(str(accessor["type"]))
    if width is None:
        raise ValueError("O GLB usa um accessor não suportado.")
    code, component_size = formats[component]
    item_size = component_size * width
    stride = int(view.get("byteStride", item_size))
    start = int(view.get("byteOffset", 0)) + int(accessor.get("byteOffset", 0))
    count = int(accessor["count"])
    if count < 0 or start < 0 or (count and start + (count - 1) * stride + item_size > len(binary)):
        raise ValueError("O GLB referencia dados fora do arquivo.")
    return [struct.unpack_from(f"<{width}{code}", binary, start + index * stride) for index in range(count)]
