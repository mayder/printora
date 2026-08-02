package agent

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"
)

func TestSpoolmanInventoryUsesReadOnlyMoonrakerProxy(t *testing.T) {
	var proxyMethod string
	var proxyPath string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/server/spoolman/status":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"spoolman_connected": true}})
		case "/server/spoolman/proxy":
			proxyMethod = r.URL.Query().Get("request_method")
			proxyPath = r.URL.Query().Get("path")
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"response": []any{
				map[string]any{"id": 17, "remaining_weight": 620},
			}}})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	payload := NewMoonrakerClient(server.URL, time.Second).SpoolmanInventory(context.Background())

	if payload["safe_mode"] != "read_only" || payload["spools"] == nil {
		t.Fatalf("unexpected spoolman payload: %#v", payload)
	}
	if proxyMethod != "GET" || proxyPath != "/v1/spool" {
		t.Fatalf("unexpected proxy request method=%q path=%q", proxyMethod, proxyPath)
	}
}
