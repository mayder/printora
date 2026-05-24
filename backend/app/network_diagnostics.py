from __future__ import annotations

import asyncio
import os
import pty
import re
import select
import socket
import subprocess
import tempfile
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse, urlunparse

import httpx

from app.printers import PrinterRecord, PrinterSshAccess


SSH_SCRIPT = r"""
set +e
printf 'SECTION host\n'
printf 'hostname='; hostname 2>&1
printf 'uptime='; uptime 2>&1
printf '\nSECTION moonraker_local\n'
curl -fsS -o /dev/null -w 'http_code=%{http_code} time_total=%{time_total}\n' http://127.0.0.1:7125/server/info 2>&1
printf '\nSECTION wifi\n'
if command -v iw >/dev/null 2>&1; then iw dev wlan0 link 2>&1; else printf 'iw_unavailable\n'; fi
printf '\nSECTION ip_addr\n'
if command -v ip >/dev/null 2>&1; then ip -br addr 2>&1; else printf 'ip_unavailable\n'; fi
"""


@dataclass(frozen=True)
class HttpProbe:
    ok: bool
    url: str
    status_code: int | None
    total_ms: float | None
    error: str | None = None


async def build_network_diagnostics(
    printer: PrinterRecord,
    ssh_access: PrinterSshAccess | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    parsed = urlparse(printer.moonraker_url)
    host = parsed.hostname or ""
    dns_ms, addresses, dns_error = await asyncio.to_thread(_resolve_host, host)
    ping = await asyncio.to_thread(_ping_host, host)
    configured_probe = await _http_probe(printer.moonraker_url, timeout_seconds)
    direct_probe = None
    direct_address = next((address for address in addresses if ":" not in address), addresses[0] if addresses else None)
    if direct_address:
        direct_url = urlunparse(parsed._replace(netloc=_replace_netloc(parsed.netloc, direct_address)))
        direct_probe = await _http_probe(direct_url, timeout_seconds)

    ssh_probe = await asyncio.to_thread(_ssh_probe, ssh_access, timeout_seconds) if ssh_access else None
    recommendation = _recommendation(host, dns_ms, configured_probe, direct_probe, ssh_probe)
    return {
        "safe_mode": "read_only",
        "printer_id": printer.id,
        "moonraker_url": printer.moonraker_url,
        "host": host,
        "dns": {
            "ok": dns_error is None,
            "duration_ms": dns_ms,
            "addresses": addresses,
            "error": dns_error,
        },
        "ping": ping,
        "configured_http": configured_probe.__dict__,
        "direct_ip_http": direct_probe.__dict__ if direct_probe else None,
        "ssh": ssh_probe,
        "recommendation": recommendation,
    }


async def _http_probe(url: str, timeout_seconds: float) -> HttpProbe:
    started_at = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(f"{url.rstrip('/')}/server/info")
        return HttpProbe(
            ok=response.is_success,
            url=url,
            status_code=response.status_code,
            total_ms=(time.perf_counter() - started_at) * 1000,
        )
    except httpx.HTTPError as exc:
        return HttpProbe(
            ok=False,
            url=url,
            status_code=None,
            total_ms=(time.perf_counter() - started_at) * 1000,
            error=str(exc),
        )


def _resolve_host(host: str) -> tuple[float | None, list[str], str | None]:
    if not host:
        return None, [], "host vazio"
    started_at = time.perf_counter()
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError as exc:
        return (time.perf_counter() - started_at) * 1000, [], str(exc)
    addresses = []
    for record in records:
        address = record[4][0]
        if address not in addresses:
            addresses.append(address)
    return (time.perf_counter() - started_at) * 1000, addresses, None


def _ping_host(host: str) -> dict[str, Any]:
    if not host:
        return {"ok": False, "error": "host vazio"}
    try:
        completed = subprocess.run(
            ["ping", "-c", "5", "-W", "2", host],
            check=False,
            capture_output=True,
            text=True,
            timeout=12,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}
    output = f"{completed.stdout}\n{completed.stderr}".strip()
    packet_loss = _match_float(output, r"(\d+(?:\.\d+)?)%\s+packet loss")
    rtt = _match_text(output, r"rtt min/avg/max/(?:mdev|stddev) = ([^\n]+)")
    return {
        "ok": completed.returncode == 0,
        "packet_loss_percent": packet_loss,
        "rtt": rtt,
        "output": "\n".join(output.splitlines()[-4:]),
    }


def _ssh_probe(ssh_access: PrinterSshAccess | None, timeout_seconds: float) -> dict[str, Any] | None:
    if ssh_access is None:
        return None
    target = f"{ssh_access.username}@{ssh_access.host}"
    command = [
        "ssh",
        "-p",
        str(ssh_access.port),
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=5",
        target,
        "bash -s",
    ]
    if ssh_access.credential:
        output, exit_code, error = _run_ssh_with_optional_password(command, SSH_SCRIPT, ssh_access.credential, timeout_seconds)
    else:
        output, exit_code, error = _run_batch_ssh(command, SSH_SCRIPT, timeout_seconds)
    if error is None and exit_code != 0:
        error = _ssh_error_message(output)
    sections = _split_sections(output)
    local_time = _match_float(sections.get("moonraker_local", ""), r"time_total=(\d+(?:\.\d+)?)")
    if local_time is not None:
        local_time *= 1000
    return {
        "configured": True,
        "ok": exit_code == 0 and error is None,
        "target": target,
        "exit_code": exit_code,
        "error": error,
        "moonraker_local_ms": local_time,
        "hostname": _match_text(sections.get("host", ""), r"hostname=(.+)"),
        "wifi": _summarize_wifi(sections.get("wifi", "")),
        "addresses": sections.get("ip_addr", "").splitlines()[:8],
    }


def _ssh_error_message(output: str) -> str:
    if "Permission denied" in output:
        return "SSH não autenticou. Re-salve a credencial da impressora ou configure chave SSH no Android."
    if "Host key verification failed" in output:
        return "Host key SSH não foi aceito pelo Android."
    return "\n".join(output.splitlines()[-3:]) or "SSH retornou erro."


def _run_batch_ssh(command: list[str], script: str, timeout_seconds: float) -> tuple[str, int | None, str | None]:
    try:
        completed = subprocess.run(
            [*command[:1], "-o", "BatchMode=yes", *command[1:]],
            input=script,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "", None, str(exc)
    return f"{completed.stdout}\n{completed.stderr}", completed.returncode, None


def _run_ssh_with_optional_password(
    command: list[str],
    script: str,
    credential: str,
    timeout_seconds: float,
) -> tuple[str, int | None, str | None]:
    askpass = tempfile.NamedTemporaryFile("w", delete=False)
    try:
        askpass.write("#!/bin/sh\nprintf '%s\\n' \"$PRINTORA_SSH_PASSWORD\"\n")
        askpass.close()
        os.chmod(askpass.name, 0o700)
        env = {
            **os.environ,
            "DISPLAY": os.environ.get("DISPLAY", ":0"),
            "SSH_ASKPASS": askpass.name,
            "SSH_ASKPASS_REQUIRE": "force",
            "PRINTORA_SSH_PASSWORD": credential,
        }
        askpass_command = [
            "setsid",
            *command[:1],
            "-o",
            "PreferredAuthentications=password",
            "-o",
            "PubkeyAuthentication=no",
            *command[1:],
        ]
        completed = subprocess.run(
            askpass_command,
            input=script,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
        return f"{completed.stdout}\n{completed.stderr}", completed.returncode, None
    except (OSError, subprocess.TimeoutExpired) as exc:
        fallback_output, fallback_code, fallback_error = _run_ssh_with_pty(command, script, credential, timeout_seconds)
        if fallback_error:
            return fallback_output, fallback_code, str(exc)
        return fallback_output, fallback_code, fallback_error
    finally:
        try:
            os.unlink(askpass.name)
        except OSError:
            pass


def _run_ssh_with_pty(
    command: list[str],
    script: str,
    credential: str,
    timeout_seconds: float,
) -> tuple[str, int | None, str | None]:
    master_fd, slave_fd = pty.openpty()
    process = subprocess.Popen(command, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd, text=False)
    os.close(slave_fd)
    output = bytearray()
    sent_password = False
    sent_script = False
    sent_password_at: float | None = None
    deadline = time.monotonic() + timeout_seconds
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master_fd], [], [], 0.2)
            if ready:
                try:
                    chunk = os.read(master_fd, 4096)
                except OSError:
                    break
                if not chunk:
                    break
                output.extend(chunk)
                text = output.decode(errors="replace").lower()
                if not sent_password and "password:" in text:
                    os.write(master_fd, f"{credential}\n".encode())
                    sent_password = True
                    sent_password_at = time.monotonic()
                    time.sleep(0.2)
                if sent_password and not sent_script and _password_rejected(text):
                    break
                if sent_password and not sent_script and _can_send_script(text, sent_password_at):
                    os.write(master_fd, _script_payload(script))
                    sent_script = True
            elif sent_password and not sent_script and _can_send_script(output.decode(errors="replace").lower(), sent_password_at):
                os.write(master_fd, _script_payload(script))
                sent_script = True
            if process.poll() is not None:
                break
        if process.poll() is None:
            process.kill()
            return output.decode(errors="replace"), None, "timeout"
        return output.decode(errors="replace"), process.returncode, None
    finally:
        os.close(master_fd)


def _script_payload(script: str) -> bytes:
    return f"{script}\nprintf '\\nSECTION printora_done\\nexit_code='$?\\n\nexit\n".encode()


def _password_rejected(text: str) -> bool:
    return "permission denied" in text or "no more authentication methods" in text


def _can_send_script(text: str, sent_password_at: float | None) -> bool:
    if sent_password_at is None or _password_rejected(text):
        return False
    return "last login" in text or "section " in text or time.monotonic() - sent_password_at >= 0.5


def _split_sections(output: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"preamble": []}
    current = "preamble"
    for line in output.splitlines():
        if line.startswith("SECTION "):
            current = line.removeprefix("SECTION ").strip()
            sections[current] = []
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items()}


def _replace_netloc(netloc: str, address: str) -> str:
    if ":" not in netloc:
        return address
    port = netloc.rsplit(":", 1)[1]
    return f"{address}:{port}"


def _summarize_wifi(output: str) -> dict[str, Any]:
    return {
        "connected": "not connected" not in output.lower() and bool(output.strip()),
        "ssid": _match_text(output, r"SSID:\s*(.+)"),
        "signal": _match_text(output, r"signal:\s*(.+)"),
        "tx_bitrate": _match_text(output, r"tx bitrate:\s*(.+)"),
        "raw": "\n".join(output.splitlines()[:10]),
    }


def _recommendation(
    host: str,
    dns_ms: float | None,
    configured_probe: HttpProbe,
    direct_probe: HttpProbe | None,
    ssh_probe: dict[str, Any] | None,
) -> str:
    if host.endswith(".local") and dns_ms is not None and dns_ms >= 1_000 and direct_probe and direct_probe.ok:
        return "O gargalo principal é resolução .local/mDNS no Android. Fixe o IP da Raspberry no roteador e considere cache local de host no Printora."
    if ssh_probe and ssh_probe.get("moonraker_local_ms") and ssh_probe["moonraker_local_ms"] < 300 and configured_probe.total_ms and configured_probe.total_ms >= 1_500:
        return "Moonraker está rápido na Raspberry; a lentidão está no caminho Android/rede/DNS."
    if not configured_probe.ok:
        return "O Printora não conseguiu consultar o Moonraker pela URL cadastrada."
    return "Rede operacional. Manter monitoramento se houver picos."


def _match_float(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text)
    return float(match.group(1)) if match else None


def _match_text(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None
