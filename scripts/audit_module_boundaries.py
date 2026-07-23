#!/usr/bin/env python3
"""Gera o inventário verificável das fronteiras do monólito modular."""

from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "backend" / "app"
SQL = ROOT / "backend" / "sql"
DEFAULT_JSON = ROOT / "docs" / "architecture" / "MODULE_INVENTORY.json"
DEFAULT_MARKDOWN = ROOT / "docs" / "architecture" / "MODULE_INVENTORY.md"


@dataclass(frozen=True)
class Boundary:
    key: str
    owner: str
    description: str
    prefixes: tuple[str, ...]


BOUNDARIES = (
    Boundary(
        "identity",
        "Identidade e permissões",
        "Autenticação, sessão, organizações, autorização e auditoria de acesso.",
        ("auth", "audit"),
    ),
    Boundary(
        "community",
        "Comunidade e projetos",
        "Catálogo social, projetos, biblioteca, descoberta, moderação e perfis públicos.",
        (
            "social_",
            "print_projects",
            "print_profiles",
            "external_library",
            "search_discovery",
        ),
    ),
    Boundary(
        "finance",
        "Finanças e pedidos",
        "Ledger, pedidos, pagamentos, reconciliação, risco e repasses.",
        ("finance_", "commerce_", "payment_"),
    ),
    Boundary(
        "operations",
        "Operação e agentes",
        "Impressoras, agentes, impressão, calibração, manutenção, setup e firmware.",
        (
            "agent_",
            "agents",
            "operation",
            "operational",
            "printer",
            "print_delivery",
            "print_history",
            "print_preflight",
            "calibration",
            "maintenance",
            "checklists",
            "gcode_",
            "slicing",
            "setup_",
            "setup",
            "can_monitor",
            "z_offset",
            "firmware",
        ),
    ),
    Boundary(
        "administration",
        "Administração",
        "Saúde, configuração, backup, relatórios, releases, suporte e operação do produto.",
        (
            "backups",
            "reports",
            "health",
            "config",
            "releases",
            "updates",
            "self_update",
            "snapshots",
            "host_audit",
            "install_diagnostics",
            "network_diagnostics",
            "remote_operations",
            "support",
            "system",
            "worker_admin",
            "technical_profiles",
            "frontend",
        ),
    ),
    Boundary(
        "integrations",
        "Integrações",
        "Adapters de Moonraker, descoberta, plugins e dependências externas.",
        ("moonraker", "discovery", "plugins"),
    ),
)

SHARED_MODULES = {
    "__init__",
    "database",
    "main",
    "object_storage",
    "worker",
    "upload_stream",
    "idempotency_middleware",
    "rate_limit_middleware",
}

CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[\"`\[]?([a-zA-Z0-9_]+)",
    re.IGNORECASE,
)


def python_files() -> list[Path]:
    return sorted(
        path
        for path in APP.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def relative_module(path: Path) -> str:
    relative = path.relative_to(APP).with_suffix("")
    return ".".join(relative.parts)


def basename(module: str) -> str:
    return module.rsplit(".", maxsplit=1)[-1]


def boundary_for(module: str) -> str:
    if module in {"modules", "modules.assembly", "modules.registry"} or module.startswith("modules.platform"):
        return "shared"
    if module.startswith("modules."):
        module_boundary = module.split(".", maxsplit=2)[1]
        if module_boundary in {boundary.key for boundary in BOUNDARIES}:
            return module_boundary
    name = basename(module)
    if name in SHARED_MODULES or module.startswith("firmware."):
        return "shared" if name in SHARED_MODULES else "operations"
    matches = [
        boundary.key
        for boundary in BOUNDARIES
        if any(name == prefix or name.startswith(prefix) for prefix in boundary.prefixes)
    ]
    if len(matches) != 1:
        raise ValueError(f"ownership inválido para {module}: {matches or 'sem owner'}")
    return matches[0]


def app_imports(tree: ast.AST) -> set[str]:
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("app."):
                    imports.add(alias.name.removeprefix("app."))
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "app":
                imports.update(alias.name for alias in node.names)
            elif node.module.startswith("app."):
                imports.add(node.module.removeprefix("app."))
    return imports


def public_contracts(tree: ast.Module) -> list[str]:
    contracts: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        bases = {
            base.id if isinstance(base, ast.Name) else base.attr
            for base in node.bases
            if isinstance(base, (ast.Name, ast.Attribute))
        }
        if bases & {"BaseModel", "TypedDict", "Protocol", "Enum", "StrEnum"}:
            contracts.append(node.name)
    return contracts


def route_contracts(tree: ast.AST) -> list[dict[str, str]]:
    routes: list[dict[str, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            method = decorator.func.attr.upper()
            if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "WEBSOCKET"}:
                continue
            path = "<dynamic>"
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                path = str(decorator.args[0].value)
            routes.append({"method": method, "path": path, "handler": node.name})
    return routes


def strongly_connected_components(graph: dict[str, set[str]]) -> list[list[str]]:
    index = 0
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    components: list[list[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in graph.get(node, set()):
            if target not in graph:
                continue
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] != indices[node]:
            return
        component: list[str] = []
        while stack:
            member = stack.pop()
            on_stack.remove(member)
            component.append(member)
            if member == node:
                break
        if len(component) > 1:
            components.append(sorted(component))

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    return sorted(components)


def sql_tables() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in sorted(SQL.glob("*.sql")):
        content = path.read_text(encoding="utf-8")
        for table in CREATE_TABLE.findall(content):
            try:
                owner = boundary_for(table)
            except ValueError:
                owner = infer_table_owner(table)
            rows.append({"table": table, "owner": owner, "script": path.name})
    return rows


def infer_table_owner(table: str) -> str:
    if table.startswith(("auth_", "organization", "audit_")):
        return "identity"
    if table.startswith(("social_", "community", "library", "print_project")):
        return "community"
    if table.startswith(("finance_", "commerce_", "payment_")):
        return "finance"
    if table.startswith(("agent", "printer", "print_", "calibration", "maintenance")):
        return "operations"
    return "administration"


def build_inventory() -> dict[str, object]:
    modules: list[dict[str, object]] = []
    graph: dict[str, set[str]] = {}
    route_total = 0
    contract_total = 0
    for path in python_files():
        module = relative_module(path)
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imports = app_imports(tree)
        routes = route_contracts(tree)
        contracts = public_contracts(tree)
        graph[module] = imports
        route_total += len(routes)
        contract_total += len(contracts)
        modules.append(
            {
                "module": module,
                "owner": boundary_for(module),
                "lines": len(path.read_text(encoding="utf-8").splitlines()),
                "imports": sorted(imports),
                "routes": routes,
                "contracts": contracts,
            }
        )
    tables = sql_tables()
    ownership = Counter(str(row["owner"]) for row in modules)
    return {
        "schema_version": 1,
        "boundaries": [boundary.__dict__ for boundary in BOUNDARIES],
        "summary": {
            "modules": len(modules),
            "routes": route_total,
            "contracts": contract_total,
            "tables": len(tables),
            "cycles": len(strongly_connected_components(graph)),
            "modules_by_owner": dict(sorted(ownership.items())),
        },
        "cycles": strongly_connected_components(graph),
        "modules": modules,
        "tables": tables,
    }


def markdown(inventory: dict[str, object]) -> str:
    summary = inventory["summary"]
    assert isinstance(summary, dict)
    boundaries = inventory["boundaries"]
    modules = inventory["modules"]
    tables = inventory["tables"]
    assert isinstance(boundaries, list) and isinstance(modules, list) and isinstance(tables, list)
    lines = [
        "# Inventário De Módulos E Contratos",
        "",
        "> Gerado por `scripts/audit_module_boundaries.py`; não editar manualmente.",
        "",
        "## Resumo",
        "",
        f"- módulos Python: {summary['modules']};",
        f"- endpoints HTTP/WebSocket: {summary['routes']};",
        f"- contratos tipados: {summary['contracts']};",
        f"- tabelas declaradas em SQL: {summary['tables']};",
        f"- ciclos de import detectados: {summary['cycles']}.",
        "",
        "## Fronteiras E Owners",
        "",
        "| Fronteira | Owner | Responsabilidade | Módulos | Tabelas |",
        "|---|---|---|---:|---:|",
    ]
    module_counts = Counter(str(row["owner"]) for row in modules if isinstance(row, dict))
    table_counts = Counter(str(row["owner"]) for row in tables if isinstance(row, dict))
    for boundary in boundaries:
        assert isinstance(boundary, dict)
        key = str(boundary["key"])
        lines.append(
            f"| `{key}` | {boundary['owner']} | {boundary['description']} | "
            f"{module_counts[key]} | {table_counts[key]} |"
        )
    lines.extend(
        [
            "| `shared` | Plataforma | Bootstrap e persistência transversal durante a extração. | "
            f"{module_counts['shared']} | {table_counts['shared']} |",
            "",
            "## Arquivos Críticos",
            "",
            "| Módulo | Owner | Linhas | Rotas | Contratos |",
            "|---|---|---:|---:|---:|",
        ]
    )
    critical = sorted(
        (row for row in modules if isinstance(row, dict) and int(row["lines"]) >= 400),
        key=lambda row: (-int(row["lines"]), str(row["module"])),
    )
    for row in critical:
        lines.append(
            f"| `{row['module']}` | `{row['owner']}` | {row['lines']} | "
            f"{len(row['routes'])} | {len(row['contracts'])} |"
        )
    lines.extend(["", "## Ciclos De Import", ""])
    cycles = inventory["cycles"]
    assert isinstance(cycles, list)
    if cycles:
        for cycle in cycles:
            lines.append("- " + " -> ".join(f"`{member}`" for member in cycle))
    else:
        lines.append("Nenhum ciclo entre módulos Python foi detectado.")
    lines.extend(
        [
            "",
            "## Contrato De Evolução",
            "",
            "- cada módulo possui um único owner;",
            "- API importa application/contract, nunca infrastructure interna de outro módulo;",
            "- domínio e contratos não importam FastAPI, SQLite, PostgreSQL, Redis, storage ou UI;",
            "- adapters cloud e local implementam ports compartilhadas, sem fallback cruzado;",
            "- toda alteração pública preserva compatibilidade N/N-1 ou versiona o contrato;",
            "- arquivos críticos acima do limite devem ser divididos ao serem alterados.",
            "",
        ]
    )
    return "\n".join(lines)


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise SystemExit(f"inventário divergente: execute {Path(__file__).relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--json", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MARKDOWN)
    args = parser.parse_args()
    inventory = build_inventory()
    json_content = json.dumps(inventory, ensure_ascii=False, indent=2) + "\n"
    markdown_content = markdown(inventory)
    write_or_check(args.json, json_content, args.check)
    write_or_check(args.markdown, markdown_content, args.check)
    print(json.dumps(inventory["summary"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
