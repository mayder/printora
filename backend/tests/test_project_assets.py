from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from app.modules.community.project_assets import inspect_project_asset


def test_inspects_ascii_stl_with_accessible_dimensions_and_mesh_preview() -> None:
    body = b"""solid example
facet normal 0 0 1
outer loop
vertex 0 0 0
vertex 20 0 0
vertex 0 30 10
endloop
endfacet
endsolid
"""

    report = inspect_project_asset("example.stl", body)

    assert report["status"] == "ready"
    assert report["dimensions_mm"] == {"x": 20.0, "y": 30.0, "z": 10.0}
    assert report["triangle_count"] == 1
    assert report["preview_triangles"] == [[[0.0, 0.0, 0.0], [20.0, 0.0, 0.0], [0.0, 30.0, 10.0]]]


def test_inspects_3mf_and_converts_inches_to_millimeters() -> None:
    model = b"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="inch" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources><object id="1" type="model"><mesh>
    <vertices><vertex x="0" y="0" z="0"/><vertex x="1" y="0" z="0"/><vertex x="0" y="1" z="0"/></vertices>
    <triangles><triangle v1="0" v2="1" v3="2"/></triangles>
  </mesh></object></resources>
</model>"""
    stream = BytesIO()
    with ZipFile(stream, "w", ZIP_DEFLATED) as archive:
        archive.writestr("3D/3dmodel.model", model)

    report = inspect_project_asset("example.3mf", stream.getvalue())

    assert report["status"] == "ready"
    assert report["dimensions_mm"] == {"x": 25.4, "y": 25.4, "z": 0.0}
    assert report["source_unit"] == "inch"


def test_rejects_invalid_geometry_without_raising_or_blocking_other_files() -> None:
    report = inspect_project_asset("broken.stl", b"solid broken\nendsolid\n")

    assert report["status"] == "failed"
    assert report["preview_supported"] is False
    assert report["warnings"]


def test_bundle_format_uses_limited_fallback_instead_of_parsing_untrusted_archive() -> None:
    report = inspect_project_asset("parts.zip", b"not-opened-here")

    assert report["status"] == "limited"
    assert report["preview_supported"] is False
