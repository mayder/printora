from app.klipper_runtime_alerts import classify_runtime_alerts, runtime_alert_payload


def test_runtime_alert_payload_reads_agent_contract() -> None:
    messages, state = runtime_alert_payload(
        {
            "runtime_alerts": [
                "  Klipper warning\nMCU 'mcu' has deprecated code  ",
                "",
                None,
            ],
            "runtime_alerts_state": "loaded",
        }
    )

    assert messages == ["Klipper warning MCU 'mcu' has deprecated code"]
    assert state == "loaded"


def test_runtime_alert_classifier_covers_mcu_warning_and_critical_families() -> None:
    alerts = classify_runtime_alerts(
        [
            "MCU 'mcu' has deprecated code (it is missing feature 'STEPPER_STEP_BOTH_EDGE').",
            "!! ADC out of range",
            "MCU Protocol error",
            "!! Unknown command: TEST_ONLY",
        ]
    )

    assert [alert.severity for alert in alerts] == ["warning", "blocker", "blocker", "blocker"]
    assert [alert.title for alert in alerts] == [
        "Firmware da MCU desatualizado",
        "Falha crítica de temperatura",
        "Incompatibilidade entre Klipper e MCU",
        "Erro crítico do Klipper",
    ]
    assert len({alert.key for alert in alerts}) == 4


def test_runtime_alert_classifier_ignores_normal_console_output_and_deduplicates() -> None:
    warning = "Klipper warning MCU 'mcu' has deprecated code"
    alerts = classify_runtime_alerts(["B:21.2 /0.0 T0:216.3 /220.0", warning, warning])

    assert len(alerts) == 1
    assert alerts[0].severity == "warning"
