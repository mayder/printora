package agent

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"
)

func TestKlipperRuntimeAlertMessagesKeepsWarningsAndCriticalErrors(t *testing.T) {
	payload := map[string]any{
		"result": map[string]any{
			"gcode_store": []any{
				map[string]any{"message": "B:21.2 /0.0 T0:216.3 /220.0"},
				map[string]any{"message": "MCU 'mcu' has deprecated code (it is missing feature 'i2c_transfer'). Recompiling and flashing is recommended."},
				map[string]any{"message": "!! Lost communication with MCU 'head'"},
				map[string]any{"message": "MCU 'mcu' has deprecated code (it is missing feature 'i2c_transfer'). Recompiling and flashing is recommended."},
			},
		},
	}

	alerts := klipperRuntimeAlertMessages(payload)

	if len(alerts) != 2 {
		t.Fatalf("unexpected alerts: %#v", alerts)
	}
	joined := strings.Join(alerts, "\n")
	if !strings.Contains(joined, "i2c_transfer") {
		t.Fatalf("missing deprecated MCU warning: %#v", alerts)
	}
	if !strings.Contains(joined, "Lost communication") {
		t.Fatalf("missing critical MCU alert: %#v", alerts)
	}
}

func TestKlipperRuntimeAlertMessagesRedactsSensitiveContext(t *testing.T) {
	payload := map[string]any{
		"result": map[string]any{
			"gcode_store": []any{
				map[string]any{
					"message": "!! Internal error on command: token=secret-value at https://host.local/log in /home/pi/printer_data/logs/klippy.log",
				},
			},
		},
	}

	joined := strings.Join(klipperRuntimeAlertMessages(payload), "\n")
	for _, sensitive := range []string{"secret-value", "https://host.local", "/home/pi/"} {
		if strings.Contains(joined, sensitive) {
			t.Fatalf("sensitive context leaked in runtime alert: %s", joined)
		}
	}
	if !strings.Contains(joined, "token=<redacted>") {
		t.Fatalf("missing secret redaction marker: %s", joined)
	}
}

func TestMoonrakerStatusCollectsOnlySanitizedRuntimeAlerts(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/server/gcode_store" {
			if r.URL.Query().Get("count") != "200" {
				t.Fatalf("unexpected gcode store limit: %s", r.URL.RawQuery)
			}
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"gcode_store": []any{
				map[string]any{"message": "normal console output"},
				map[string]any{"message": "Klipper warning\nMCU 'mcu' has deprecated code (it is missing feature 'STEPPER_STEP_BOTH_EDGE')."},
			}}})
			return
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{}})
	}))
	defer server.Close()

	payload := NewMoonrakerClient(server.URL, time.Second).Status(context.Background())
	alerts, ok := payload["runtime_alerts"].([]string)
	if !ok || len(alerts) != 1 {
		t.Fatalf("unexpected runtime alerts: %#v", payload["runtime_alerts"])
	}
	if strings.Contains(strings.Join(alerts, "\n"), "normal console output") {
		t.Fatalf("unrelated console output leaked: %#v", alerts)
	}
	if payload["runtime_alerts_state"] != "loaded" {
		t.Fatalf("unexpected collection state: %#v", payload["runtime_alerts_state"])
	}
}

func TestMoonrakerStatusMarksRuntimeAlertsUnavailableWithoutFailingStatus(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/server/gcode_store" {
			http.Error(w, "unavailable", http.StatusServiceUnavailable)
			return
		}
		_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{}})
	}))
	defer server.Close()

	payload := NewMoonrakerClient(server.URL, time.Second).Status(context.Background())
	alerts, ok := payload["runtime_alerts"].([]string)
	if !ok || len(alerts) != 0 {
		t.Fatalf("runtime alert failure must return an empty list: %#v", payload["runtime_alerts"])
	}
	if payload["runtime_alerts_state"] != "unavailable" {
		t.Fatalf("unexpected collection state: %#v", payload["runtime_alerts_state"])
	}
}
