"""Cliente HTTP mínimo e defensivo para o gateway Tripo do Printora."""

from __future__ import annotations

import ipaddress
import json
import secrets
import socket
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


API_ROOT = "https://api.tripo3d.ai/v2/openapi"
MAX_JSON_BYTES = 1024 * 1024
MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_DOWNLOAD_BYTES = 500 * 1024 * 1024
FINAL_STATUSES = {"success", "failed", "banned", "expired", "cancelled", "unknown"}


class TripoClient:
    def __init__(self, api_key: str, *, timeout_seconds: float = 60.0) -> None:
        if (
            not api_key.startswith("tsk_")
            or len(api_key) > 240
            or any(character.isspace() or character == "\0" for character in api_key)
        ):
            raise ValueError("credencial Tripo inválida")
        self._api_key = api_key
        self._timeout_seconds = max(5.0, min(timeout_seconds, 120.0))

    def upload_image(self, path: Path) -> str:
        size = path.stat().st_size
        if size <= 0 or size > MAX_UPLOAD_BYTES:
            raise ValueError("foto fora do limite do provedor")
        content_type = "image/jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "image/png"
        boundary = f"printora-{secrets.token_hex(16)}"
        prefix = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="input{path.suffix.lower()}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode()
        body = prefix + path.read_bytes() + f"\r\n--{boundary}--\r\n".encode()
        payload = self._request_json(
            f"{API_ROOT}/upload/sts",
            method="POST",
            body=body,
            content_type=f"multipart/form-data; boundary={boundary}",
        )
        token = str(payload.get("image_token", ""))
        if not token or len(token) > 160:
            raise RuntimeError("upload do provedor não retornou identificador")
        return token

    def create_multiview_task(self, tokens: list[tuple[str, str]], model_version: str) -> str:
        if len(tokens) != 4:
            raise ValueError("o provedor exige quatro vistas")
        payload = self._request_json(
            f"{API_ROOT}/task",
            method="POST",
            body=json.dumps({
                "type": "multiview_to_model",
                "model_version": model_version,
                "files": [{"type": file_type, "file_token": token} for file_type, token in tokens],
                "texture": False,
                "pbr": False,
            }, separators=(",", ":")).encode(),
            content_type="application/json",
        )
        task_id = str(payload.get("task_id", ""))
        if not task_id or len(task_id) > 160:
            raise RuntimeError("provedor não retornou identificador da tarefa")
        return task_id

    def get_task(self, task_id: str) -> dict[str, object]:
        safe_id = urllib.parse.quote(task_id, safe="")
        return self._request_json(f"{API_ROOT}/task/{safe_id}", method="GET")

    def download_model(self, url: str, target: Path) -> None:
        _require_public_https(url)
        request = urllib.request.Request(url, headers={"User-Agent": "Printora-Reconstruction/1"})
        try:
            opener = urllib.request.build_opener(_SafeRedirectHandler())
            with opener.open(request, timeout=self._timeout_seconds) as response:
                final_url = response.geturl()
                _require_public_https(final_url)
                declared = response.headers.get("Content-Length")
                if declared and int(declared) > MAX_DOWNLOAD_BYTES:
                    raise RuntimeError("modelo do provedor excede o limite")
                total = 0
                with target.open("wb") as output:
                    while chunk := response.read(64 * 1024):
                        total += len(chunk)
                        if total > MAX_DOWNLOAD_BYTES:
                            raise RuntimeError("modelo do provedor excede o limite")
                        output.write(chunk)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError("falha de comunicação com o provedor") from exc
        if not target.is_file() or target.stat().st_size == 0:
            raise RuntimeError("provedor retornou modelo vazio")

    def _request_json(
        self,
        url: str,
        *,
        method: str,
        body: bytes | None = None,
        content_type: str | None = None,
    ) -> dict[str, object]:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Accept": "application/json",
            "User-Agent": "Printora-Reconstruction/1",
        }
        if content_type:
            headers["Content-Type"] = content_type
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                raw = response.read(MAX_JSON_BYTES + 1)
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"provedor recusou a operação ({exc.code})") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise RuntimeError("falha de comunicação com o provedor") from exc
        if len(raw) > MAX_JSON_BYTES:
            raise RuntimeError("resposta do provedor excede o limite")
        parsed = json.loads(raw)
        if not isinstance(parsed, dict) or parsed.get("code") != 0 or not isinstance(parsed.get("data"), dict):
            raise RuntimeError("resposta incompatível do provedor")
        return parsed["data"]


class _SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        _require_public_https(new_url)
        return super().redirect_request(request, file_pointer, code, message, headers, new_url)


def _require_public_https(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise RuntimeError("endereço de download inválido")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise RuntimeError("endereço de download indisponível") from exc
    if not addresses:
        raise RuntimeError("endereço de download indisponível")
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise RuntimeError("endereço de download privado recusado")
