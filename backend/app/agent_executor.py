from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.agent_channel import agent_ws_manager
from app.agent_pairing import AgentPairingRepository
from app.modules.operations.application import (
    AgentJobFailedError as ApplicationAgentJobFailedError,
    AgentJobNotFoundError,
    AgentJobRejectedError,
    AgentJobService,
    AgentJobTimeoutError,
    AgentUnavailableError,
    timeout_detail,
)
from app.modules.operations.contracts import AgentJobRecord
from app.printers import PrinterRecord


DEFAULT_AGENT_TIMEOUT_SECONDS = 12.0


class AgentCommandExecutor:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.repository = AgentPairingRepository(database_path)
        self.service = AgentJobService(self.repository, agent_ws_manager)

    async def run(
        self,
        printer: PrinterRecord,
        *,
        job_type: str,
        payload: dict[str, Any] | None = None,
        timeout_seconds: float = DEFAULT_AGENT_TIMEOUT_SECONDS,
        require_online: bool = True,
    ) -> AgentJobRecord:
        try:
            return await self.service.run(
                printer,
                job_type=job_type,
                payload=payload,
                timeout_seconds=timeout_seconds,
                require_online=require_online,
            )
        except AgentUnavailableError as exc:
            raise HTTPException(status_code=409, detail=exc.message) from exc
        except AgentJobRejectedError as exc:
            raise HTTPException(status_code=400, detail=exc.message) from exc
        except AgentJobNotFoundError as exc:
            raise HTTPException(status_code=404, detail=exc.message) from exc
        except ApplicationAgentJobFailedError as exc:
            raise AgentJobFailedError(exc.job) from exc
        except AgentJobTimeoutError as exc:
            raise HTTPException(status_code=504, detail=timeout_detail(exc)) from exc


def unwrap_moonraker_result(value: Any) -> dict[str, Any]:
    if isinstance(value, dict) and isinstance(value.get("result"), dict):
        return value["result"]
    return value if isinstance(value, dict) else {}


class AgentJobFailedError(HTTPException):
    def __init__(self, job: AgentJobRecord) -> None:
        self.job = job
        super().__init__(status_code=502, detail=job.error_message or "job do agente falhou")


def _timeout_detail(job_status: str, websocket_delivered: bool) -> str:
    return timeout_detail(AgentJobTimeoutError(job_status, websocket_delivered))


def unwrap_moonraker_list(value: Any, key: str) -> list[str]:
    result = unwrap_moonraker_result(value)
    items = result.get(key)
    return [str(item) for item in items] if isinstance(items, list) else []
