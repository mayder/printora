from app.modules.operations.mesh_qualification import qualify_mesh
from app.modules.operations.mesh_qualification.repair import repair_mesh


OPEN_TETRA = b"""v 0 0 0
v 10 0 0
v 0 10 0
v 0 0 10
f 1 2 4
f 2 3 4
f 3 1 4
"""


def test_clean_is_deterministic_idempotent_and_preserves_source_checksum() -> None:
    dirty = b"v 0 0 0\nv 1 0 0\nv 0 1 0\nv 0 1 0\nf 1 2 3\nf 1 2 4\nf 1 1 2\n"

    first = repair_mesh(dirty, "obj", "clean", {"output_format": "obj"})
    second = repair_mesh(first.body, "obj", "clean", {"output_format": "obj"})

    assert first.body == second.body
    assert first.sha256 == second.sha256
    assert first.manifest["source_sha256"] != first.sha256
    assert first.manifest["output_triangles"] == 1


def test_orient_normals_makes_closed_volume_point_outward() -> None:
    inward = b"v 0 0 0\nv 10 0 0\nv 0 10 0\nv 0 0 10\nf 1 2 3\nf 1 4 2\nf 2 4 3\nf 3 4 1\n"

    repaired = repair_mesh(inward, "obj", "orient_normals", {"output_format": "obj"})
    report = qualify_mesh(repaired.body, "obj", "mm")

    assert report["checks"]["watertight"] is True
    assert report["checks"]["inverted_closed_volume"] is False
    assert report["checks"]["winding_conflict_count"] == 0


def test_close_holes_creates_new_version_without_changing_input() -> None:
    source = bytes(OPEN_TETRA)

    repaired = repair_mesh(source, "obj", "close_holes", {"maximum_hole_edges": 3, "output_format": "stl"})
    report = qualify_mesh(repaired.body, "stl", "mm")

    assert source == OPEN_TETRA
    assert report["checks"]["watertight"] is True
    assert repaired.manifest["source_triangles"] == 3
    assert repaired.manifest["output_triangles"] == 6


def test_remove_small_components_keeps_largest_when_threshold_removes_all() -> None:
    two = OPEN_TETRA + b"v 100 0 0\nv 101 0 0\nv 100 1 0\nf 5 6 7\n"

    repaired = repair_mesh(two, "obj", "remove_small_components", {"minimum_triangles": 10, "output_format": "obj"})
    report = qualify_mesh(repaired.body, "obj", "mm")

    assert report["checks"]["component_count"] == 1
    assert repaired.manifest["output_triangles"] == 3


def test_conversion_generates_reproducible_stl_and_3mf() -> None:
    stl = repair_mesh(OPEN_TETRA, "obj", "convert", {"output_format": "stl"})
    three_mf = repair_mesh(OPEN_TETRA, "obj", "convert", {"output_format": "3mf"})

    assert stl.body == repair_mesh(OPEN_TETRA, "obj", "convert", {"output_format": "stl"}).body
    assert three_mf.body == repair_mesh(OPEN_TETRA, "obj", "convert", {"output_format": "3mf"}).body
    assert qualify_mesh(stl.body, "stl", "mm")["triangle_count"] == 3
    assert qualify_mesh(three_mf.body, "3mf", "mm")["triangle_count"] == 3


def test_decimation_is_bounded_and_rejects_unsafe_parameters() -> None:
    try:
        repair_mesh(OPEN_TETRA, "obj", "decimate", {"target_ratio": 0.01})
    except ValueError as exc:
        assert "10%" in str(exc)
    else:
        raise AssertionError("unsafe decimation must be rejected")

    vertices = [f"v {x} {y} 0" for y in range(10) for x in range(10)]
    faces = []
    for y in range(9):
        for x in range(9):
            first = y * 10 + x + 1
            faces.extend((f"f {first} {first + 1} {first + 10}", f"f {first + 1} {first + 11} {first + 10}"))
    grid = ("\n".join([*vertices, *faces]) + "\n").encode()

    reduced = repair_mesh(grid, "obj", "decimate", {"target_ratio": 0.5, "output_format": "obj"})

    assert int(reduced.manifest["output_triangles"]) < int(reduced.manifest["source_triangles"])
