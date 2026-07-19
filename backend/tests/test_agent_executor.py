from app.agent_executor import _timeout_detail


def test_agent_timeout_detail_reports_polling_delivery_gap() -> None:
    detail = _timeout_detail("pending", websocket_delivered=False)

    assert "polling" in detail
    assert "WebSocket" in detail


def test_agent_timeout_detail_reports_in_progress_job() -> None:
    detail = _timeout_detail("in_progress", websocket_delivered=True)

    assert detail == "timeout aguardando o agente concluir o job"
