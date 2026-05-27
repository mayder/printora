from __future__ import annotations

import os
import platform
import shutil
import socket
import subprocess
import sys
import tomllib
from pathlib import Path

from pydantic import BaseModel, Field

from app.config import Settings
from app.releases import installed_app_version
from app.self_update import SelfUpdateRepository, detect_update_environment


class InstallDiagnosticItem(BaseModel):
    key: str
    label: str
    status: str
    detail: str
    command: str | None = None


class InstallationDiagnosticsResponse(BaseModel):
    safe_mode: str = "read_only"
    summary: str
    platform: str
    environment: str
    installed_version: str
    hostname: str
    project_root: str
    data_dir: str
    database_path: str
    port: str
    counts: dict[str, int] = Field(default_factory=dict)
    items: list[InstallDiagnosticItem] = Field(default_factory=list)
    copy_text: str


def build_installation_diagnostics(settings: Settings, project_root: Path) -> InstallationDiagnosticsResponse:
    repository = SelfUpdateRepository(settings.database_path)
    environment = detect_update_environment()
    port = os.environ.get("PRINTORA_PORT", "8069")
    items = [
        _check_python(),
        _check_node(),
        _check_command("npm", "npm", "Instale Node.js LTS pelo instalador assistido do seu sistema."),
        _check_command("git", "Git", "Instale Git pelo instalador assistido do seu sistema."),
        _check_backend_package(project_root),
        _check_database(settings.database_path),
        _check_path("frontend_dist", "Frontend compilado", project_root / "frontend" / "dist" / "index.html", "Rode o instalador assistido ou recompile com PRINTORA_REBUILD_FRONTEND=1."),
        _check_port(port),
        _check_raspberry_throttling(),
        _check_update_lock(repository),
    ]
    counts = {
        "ok": sum(1 for item in items if item.status == "ok"),
        "warning": sum(1 for item in items if item.status == "warning"),
        "error": sum(1 for item in items if item.status == "error"),
    }
    summary = _build_summary(counts)
    response = InstallationDiagnosticsResponse(
        summary=summary,
        platform=platform.platform(),
        environment=environment,
        installed_version=installed_app_version(),
        hostname=socket.gethostname(),
        project_root=str(project_root),
        data_dir=str(settings.data_dir),
        database_path=str(settings.database_path),
        port=port,
        counts=counts,
        items=items,
        copy_text="",
    )
    response.copy_text = _format_copy_text(response)
    return response


def _check_python() -> InstallDiagnosticItem:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 11):
        return InstallDiagnosticItem(key="python", label="Python", status="ok", detail=f"Python {version} em uso.")
    return InstallDiagnosticItem(
        key="python",
        label="Python",
        status="error",
        detail=f"Python {version} em uso. O Printora precisa de Python 3.11+.",
        command=_install_command("python"),
    )


def _check_command(command_name: str, label: str, fallback_action: str) -> InstallDiagnosticItem:
    command_path = shutil.which(command_name)
    if not command_path:
        return InstallDiagnosticItem(
            key=command_name,
            label=label,
            status="error",
            detail=f"{label} não encontrado no PATH.",
            command=_install_command(command_name) or fallback_action,
        )
    version = _read_version(command_name)
    detail = f"{command_path}"
    if version:
        detail = f"{version} ({command_path})"
    return InstallDiagnosticItem(key=command_name, label=label, status="ok", detail=detail)


def _check_node() -> InstallDiagnosticItem:
    command_path = shutil.which("node")
    if not command_path:
        return InstallDiagnosticItem(
            key="node",
            label="Node.js",
            status="error",
            detail="Node.js não encontrado no PATH.",
            command=_install_command("node") or "Instale Node.js LTS pelo instalador assistido do seu sistema.",
        )
    version = _read_version("node") or "node encontrado"
    parsed_version = _parse_node_version(version)
    if parsed_version and parsed_version < (20, 19, 0):
        return InstallDiagnosticItem(
            key="node",
            label="Node.js",
            status="warning",
            detail=f"{version} ({command_path}). Vite recomenda Node 20.19+ ou 22.12+ para rebuild.",
            command="Use o instalador assistido; ele prepara Node isolado quando necessário.",
        )
    return InstallDiagnosticItem(key="node", label="Node.js", status="ok", detail=f"{version} ({command_path})")


def _check_backend_package(project_root: Path) -> InstallDiagnosticItem:
    project_version = _read_backend_pyproject_version(project_root)
    installed_version = installed_app_version()
    if not project_version:
        return InstallDiagnosticItem(
            key="backend_package",
            label="Backend instalado",
            status="warning",
            detail="Não foi possível ler backend/pyproject.toml.",
        )
    if project_version != installed_version:
        return InstallDiagnosticItem(
            key="backend_package",
            label="Backend instalado",
            status="warning",
            detail=f"Projeto está em {project_version}, mas a venv reporta {installed_version}.",
            command="Rode o instalador assistido para reinstalar o backend local.",
        )
    return InstallDiagnosticItem(
        key="backend_package",
        label="Backend instalado",
        status="ok",
        detail=f"Versão {installed_version} alinhada com backend/pyproject.toml.",
    )


def _check_database(database_path: Path) -> InstallDiagnosticItem:
    if database_path.exists():
        return InstallDiagnosticItem(key="database", label="Banco local", status="ok", detail=str(database_path))
    return InstallDiagnosticItem(
        key="database",
        label="Banco local",
        status="warning",
        detail=f"Banco ainda não encontrado em {database_path}. Ele será criado quando o backend inicializar.",
        command="Reinicie o Printora pelo instalador ou runner da plataforma.",
    )


def _check_path(key: str, label: str, path: Path, action: str) -> InstallDiagnosticItem:
    if path.exists():
        return InstallDiagnosticItem(key=key, label=label, status="ok", detail=str(path))
    return InstallDiagnosticItem(key=key, label=label, status="warning", detail=f"Arquivo ausente: {path}", command=action)


def _check_port(port: str) -> InstallDiagnosticItem:
    if not port.isdigit():
        return InstallDiagnosticItem(key="port", label="Porta", status="warning", detail=f"Porta configurada inválida ou incomum: {port}")
    if port == "8069":
        return InstallDiagnosticItem(key="port", label="Porta", status="ok", detail="Porta padrão 8069 em uso.")
    return InstallDiagnosticItem(
        key="port",
        label="Porta",
        status="warning",
        detail=f"Porta atual {port}. O padrão público do Printora é 8069.",
        command="Defina PRINTORA_PORT=8069 e reinicie o Printora.",
    )


def _check_raspberry_throttling() -> InstallDiagnosticItem:
    is_raspberry = _is_raspberry_host()
    vcgencmd_path = shutil.which("vcgencmd")
    if not vcgencmd_path:
        if is_raspberry:
            return InstallDiagnosticItem(
                key="raspberry_throttling",
                label="Energia Raspberry",
                status="warning",
                detail="Raspberry detectada, mas vcgencmd não está disponível para consultar throttling.",
                command="Instale raspberrypi-utils ou rode vcgencmd get_throttled no host.",
            )
        return InstallDiagnosticItem(
            key="raspberry_throttling",
            label="Energia Raspberry",
            status="ok",
            detail="Host não identificado como Raspberry Pi; check de throttling não aplicável.",
        )
    try:
        result = subprocess.run(
            [vcgencmd_path, "get_throttled"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return InstallDiagnosticItem(
            key="raspberry_throttling",
            label="Energia Raspberry",
            status="warning",
            detail=f"Falha ao consultar vcgencmd get_throttled: {exc}",
            command="Rode vcgencmd get_throttled no host e verifique fonte/cabo se houver undervoltage.",
        )
    output = (result.stdout or result.stderr).strip()
    status, detail = _parse_raspberry_throttling(output)
    return InstallDiagnosticItem(
        key="raspberry_throttling",
        label="Energia Raspberry",
        status=status,
        detail=detail,
        command=None if status == "ok" else "Verifique fonte USB-C, cabo, carga térmica e rode vcgencmd get_throttled novamente.",
    )


def _check_update_lock(repository: SelfUpdateRepository) -> InstallDiagnosticItem:
    running_updates = repository.count_running_updates()
    if running_updates == 0:
        return InstallDiagnosticItem(key="updates", label="Updates locais", status="ok", detail="Nenhum update em execução.")
    return InstallDiagnosticItem(
        key="updates",
        label="Updates locais",
        status="warning",
        detail=f"{running_updates} update(s) ainda marcado(s) como em execução.",
        command="Use Configurações > Histórico de updates > Reconciliar travados.",
    )


def _is_raspberry_host() -> bool:
    candidates = [
        Path("/proc/device-tree/model"),
        Path("/sys/firmware/devicetree/base/model"),
    ]
    for path in candidates:
        try:
            model = path.read_text(errors="ignore").lower()
        except OSError:
            continue
        if "raspberry pi" in model:
            return True
    return False


def _parse_raspberry_throttling(output: str) -> tuple[str, str]:
    raw = output.strip()
    prefix = "throttled="
    value_text = raw.split(prefix, 1)[1] if prefix in raw else raw
    try:
        value = int(value_text.strip(), 16)
    except ValueError:
        return "warning", f"Resposta inesperada de vcgencmd get_throttled: {raw or 'vazia'}"
    current_flags = [
        label
        for bit, label in (
            (0, "undervoltage atual"),
            (1, "frequência limitada agora"),
            (2, "throttled agora"),
            (3, "limite térmico ativo"),
        )
        if value & (1 << bit)
    ]
    historical_flags = [
        label
        for bit, label in (
            (16, "undervoltage já ocorreu"),
            (17, "frequência já foi limitada"),
            (18, "throttling já ocorreu"),
            (19, "limite térmico já ocorreu"),
        )
        if value & (1 << bit)
    ]
    if current_flags:
        return "error", f"Raspberry com throttling ativo ({raw}): {', '.join(current_flags)}."
    if historical_flags:
        return "warning", f"Raspberry já registrou throttling ({raw}): {', '.join(historical_flags)}."
    return "ok", f"Raspberry sem throttling detectado ({raw or 'throttled=0x0'})."


def _read_version(command_name: str) -> str | None:
    try:
        result = subprocess.run(
            [command_name, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0] if output else None


def _parse_node_version(raw_version: str) -> tuple[int, int, int] | None:
    value = raw_version.strip().split()[0].lstrip("v")
    parts = value.split(".")
    if len(parts) < 2:
        return None
    try:
        major = int(parts[0])
        minor = int(parts[1])
        patch = int(parts[2]) if len(parts) > 2 else 0
    except ValueError:
        return None
    return major, minor, patch


def _read_backend_pyproject_version(project_root: Path) -> str | None:
    pyproject_path = project_root / "backend" / "pyproject.toml"
    try:
        pyproject = tomllib.loads(pyproject_path.read_text())
    except (OSError, tomllib.TOMLDecodeError):
        return None
    version = pyproject.get("project", {}).get("version")
    return version if isinstance(version, str) else None


def _install_command(command_name: str) -> str | None:
    environment = detect_update_environment()
    if environment == "windows":
        mapping = {
            "python": "winget install --id Python.Python.3.13 -e",
            "node": "winget install --id OpenJS.NodeJS.LTS -e",
            "npm": "winget install --id OpenJS.NodeJS.LTS -e",
            "git": "winget install --id Git.Git -e",
        }
        return mapping.get(command_name)
    if environment == "android_termux":
        mapping = {
            "python": "pkg install python",
            "node": "pkg install nodejs",
            "npm": "pkg install nodejs",
            "git": "pkg install git",
        }
        return mapping.get(command_name)
    if platform.system() == "Darwin":
        mapping = {
            "python": "brew install python",
            "node": "brew install node",
            "npm": "brew install node",
            "git": "brew install git",
        }
        return mapping.get(command_name)
    mapping = {
        "python": "sudo apt-get install -y python3 python3-venv python3-pip",
        "node": "sudo apt-get install -y nodejs npm",
        "npm": "sudo apt-get install -y nodejs npm",
        "git": "sudo apt-get install -y git",
    }
    return mapping.get(command_name)


def _build_summary(counts: dict[str, int]) -> str:
    if counts["error"]:
        return "Instalação com dependências obrigatórias ausentes."
    if counts["warning"]:
        return "Instalação funcional com pontos para revisar."
    return "Instalação sem problemas detectados."


def _format_copy_text(response: InstallationDiagnosticsResponse) -> str:
    lines = [
        "Diagnóstico de instalação do Printora",
        f"Resumo: {response.summary}",
        f"Versão: {response.installed_version}",
        f"Ambiente: {response.environment}",
        f"Plataforma: {response.platform}",
        f"Host: {response.hostname}",
        f"Porta: {response.port}",
        f"Projeto: {response.project_root}",
        f"Dados: {response.data_dir}",
        f"Banco: {response.database_path}",
        "",
        "Checks:",
    ]
    for item in response.items:
        lines.append(f"- {item.label}: {item.status} - {item.detail}")
        if item.command:
            lines.append(f"  Ação sugerida: {item.command}")
    return "\n".join(lines)
