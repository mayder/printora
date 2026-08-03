import json
import struct

from app.modules.operations.mesh_qualification import qualify_mesh


TETRAHEDRON = b"""v 0 0 0
v 10 0 0
v 0 10 0
v 0 0 10
f 1 3 2
f 1 2 4
f 2 3 4
f 3 1 4
"""


def test_closed_obj_reports_topology_but_waits_for_mandatory_checks() -> None:
    report = qualify_mesh(TETRAHEDRON, "obj", "mm")

    assert report["status"] == "not_qualified"
    assert report["checks"]["watertight"] is True
    assert report["checks"]["manifold"] is True
    assert report["checks"]["component_count"] == 1
    assert report["dimensions"] == {"x": 10.0, "y": 10.0, "z": 10.0}
    assert report["mandatory_checks_complete"] is False
    assert any("espessura" in message.lower() for message in report["blockers"])


def test_open_unknown_scale_mesh_is_blocked_with_human_explanation() -> None:
    report = qualify_mesh(b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n", "obj", "unknown")

    assert report["status"] == "not_qualified"
    assert report["checks"]["boundary_edge_count"] == 3
    assert report["checks"]["hole_count"] == 1
    assert any("unidade" in message.lower() for message in report["blockers"])
    assert any("aberta" in message.lower() for message in report["blockers"])


def test_duplicate_coordinates_are_welded_before_manifold_analysis() -> None:
    ascii_stl = b"""solid tetra
facet normal 0 0 -1
outer loop
vertex 0 0 0
vertex 0 10 0
vertex 10 0 0
endloop
endfacet
facet normal 0 -1 0
outer loop
vertex 0 0 0
vertex 10 0 0
vertex 0 0 10
endloop
endfacet
facet normal 1 1 1
outer loop
vertex 10 0 0
vertex 0 10 0
vertex 0 0 10
endloop
endfacet
facet normal -1 0 0
outer loop
vertex 0 10 0
vertex 0 0 0
vertex 0 0 10
endloop
endfacet
endsolid
"""
    report = qualify_mesh(ascii_stl, "stl", "mm")

    assert report["welded_vertex_count"] == 4
    assert report["checks"]["watertight"] is True


def test_ascii_ply_and_embedded_glb_are_parsed_without_external_resources() -> None:
    ply = b"ply\nformat ascii 1.0\nelement vertex 3\nproperty float x\nproperty float y\nproperty float z\nelement face 1\nproperty list uchar int vertex_indices\nend_header\n0 0 0\n1 0 0\n0 1 0\n3 0 1 2\n"
    assert qualify_mesh(ply, "ply", "mm")["triangle_count"] == 1

    binary = struct.pack("<9f3H", 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 2)
    binary += b"\0" * ((4 - len(binary) % 4) % 4)
    document = json.dumps({
        "asset": {"version": "2.0"}, "buffers": [{"byteLength": len(binary)}],
        "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36}, {"buffer": 0, "byteOffset": 36, "byteLength": 6}],
        "accessors": [{"bufferView": 0, "componentType": 5126, "count": 3, "type": "VEC3"}, {"bufferView": 1, "componentType": 5123, "count": 3, "type": "SCALAR"}],
        "meshes": [{"primitives": [{"attributes": {"POSITION": 0}, "indices": 1}]}],
    }, separators=(",", ":")).encode()
    document += b" " * ((4 - len(document) % 4) % 4)
    glb = b"glTF" + struct.pack("<II", 2, 12 + 8 + len(document) + 8 + len(binary))
    glb += struct.pack("<II", len(document), 0x4E4F534A) + document
    glb += struct.pack("<II", len(binary), 0x004E4942) + binary

    assert qualify_mesh(glb, "glb", "mm")["triangle_count"] == 1


def test_malformed_or_external_glb_fails_closed() -> None:
    report = qualify_mesh(b"not-a-glb", "glb", "unknown")

    assert report["status"] == "failed"
    assert report["mandatory_checks_complete"] is False
