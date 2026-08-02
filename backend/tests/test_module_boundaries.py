from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "backend" / "app"
INVENTORY = ROOT / "docs" / "architecture" / "MODULE_INVENTORY.json"
FORBIDDEN_PURE_IMPORTS = {
    "fastapi",
    "sqlite3",
    "psycopg",
    "redis",
    "sqlalchemy",
    "starlette",
}
PURE_FILENAMES = {"application.py", "contracts.py", "domain.py", "ports.py", "security.py"}


def imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.partition(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.partition(".")[0])
    return roots


def test_generated_module_inventory_is_current_and_acyclic() -> None:
    subprocess.run(
        ["python3", "scripts/audit_module_boundaries.py", "--check"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(INVENTORY.read_text(encoding="utf-8"))
    assert payload["cycles"] == []
    assert payload["summary"]["routes"] >= 300
    assert payload["summary"]["tables"] >= 100
    assert all(row["owner"] for row in payload["modules"])
    material_tables = [row for row in payload["tables"] if str(row["table"]).startswith("material_")]
    assert material_tables and all(row["owner"] == "operations" for row in material_tables)


def test_versioned_http_and_realtime_contracts_are_current() -> None:
    subprocess.run(
        [sys.executable, "scripts/export_api_contracts.py", "--check"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )


def test_pure_module_layers_do_not_import_framework_or_database_drivers() -> None:
    pure_files = [
        path
        for path in (APP / "modules").rglob("*.py")
        if path.name in PURE_FILENAMES
    ] if (APP / "modules").is_dir() else []
    for path in pure_files:
        forbidden = imported_roots(path) & FORBIDDEN_PURE_IMPORTS
        assert not forbidden, f"{path.relative_to(ROOT)} importa {sorted(forbidden)}"


def test_module_registry_has_unique_versioned_owners_and_router_order() -> None:
    from app.modules import module_definitions, module_routers
    from app.routes import frontend

    definitions = module_definitions()
    assert {definition.key for definition in definitions} == {
        "identity",
        "finance",
        "community",
        "design_system",
        "accessibility",
        "operations",
        "administration",
        "integrations",
    }
    assert all(definition.owner for definition in definitions)
    assert all(definition.contract_version == "1.0.0" for definition in definitions)
    orders = [registration.order for definition in definitions for registration in definition.routers]
    assert len(orders) == 40
    assert len(orders) == len(set(orders))
    assert list(module_routers())[-1] is frontend.router


def test_current_adapters_implement_explicit_module_ports(tmp_path: Path) -> None:
    from app.backups import BackupRepository
    from app.modules.administration.ports import BackupRepositoryPort
    from app.modules.community.ports import CommunityRepositoryPort
    from app.modules.integrations.ports import MoonrakerGateway
    from app.moonraker import MoonrakerClient
    from app.social_catalog import SocialCatalogRepository

    assert isinstance(BackupRepository(tmp_path / "backup.db"), BackupRepositoryPort)
    assert isinstance(SocialCatalogRepository(tmp_path / "social.db"), CommunityRepositoryPort)
    assert isinstance(MoonrakerClient("http://127.0.0.1:7125"), MoonrakerGateway)
