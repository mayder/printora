package agent

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func TestRedactingWriterHidesSecrets(t *testing.T) {
	var out strings.Builder
	writer := RedactingWriter{Writer: &out}
	_, err := writer.Write([]byte("token ptr_agent_secret credential ptr_pair_pair session ptr_sess_abc"))
	if err != nil {
		t.Fatal(err)
	}
	text := out.String()
	if strings.Contains(text, "secret") || strings.Contains(text, "ptr_pair_pair") || strings.Contains(text, "ptr_sess_abc") {
		t.Fatalf("secret leaked: %s", text)
	}
}

func TestCredentialRequiresRestrictedPermission(t *testing.T) {
	if os.Getenv("GOOS") == "windows" {
		t.Skip("permission bits are platform dependent")
	}
	path := filepath.Join(t.TempDir(), "credential")
	if err := os.WriteFile(path, []byte("ptr_agent_ok"), 0o644); err != nil {
		t.Fatal(err)
	}
	if _, err := ReadCredential(path); err == nil {
		t.Fatal("expected insecure permission error")
	}
	if err := os.Chmod(path, 0o600); err != nil {
		t.Fatal(err)
	}
	credential, err := ReadCredential(path)
	if err != nil {
		t.Fatal(err)
	}
	if credential != "ptr_agent_ok" {
		t.Fatalf("unexpected credential %q", credential)
	}
}

func TestMoonrakerSnapshotIsReadOnly(t *testing.T) {
	var methods []string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		methods = append(methods, r.Method+" "+r.URL.Path)
		_ = json.NewEncoder(w).Encode(map[string]any{"result": "ok"})
	}))
	defer server.Close()
	client := NewMoonrakerClient(server.URL, time.Second)
	snapshot := client.Snapshot(context.Background())
	if snapshot["safe_mode"] != "read_only" {
		t.Fatalf("unexpected safe mode: %v", snapshot["safe_mode"])
	}
	for _, method := range methods {
		if !strings.HasPrefix(method, "GET ") {
			t.Fatalf("non read-only method used: %s", method)
		}
	}
}

func TestAPIClientUsesBearerCredential(t *testing.T) {
	var auth string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		auth = r.Header.Get("Authorization")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"accepted":true}`))
	}))
	defer server.Close()
	client := NewAPIClient(server.URL, "ptr_agent_test", time.Second)
	if err := client.Heartbeat(context.Background(), HeartbeatPayload{AgentVersion: Version, Platform: Platform(), Capabilities: map[string]any{}}); err != nil {
		t.Fatal(err)
	}
	if auth != "Bearer ptr_agent_test" {
		t.Fatalf("unexpected auth header %q", auth)
	}
}

func TestAPIClientPollsAndCompletesJobs(t *testing.T) {
	var sawAck bool
	var sawResult bool
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("Authorization") != "Bearer ptr_agent_test" {
			t.Fatalf("unexpected auth header %q", r.Header.Get("Authorization"))
		}
		switch r.URL.Path {
		case "/api/agent/jobs/next":
			_ = json.NewEncoder(w).Encode(AgentJobsResponse{
				ProtocolVersion: ProtocolVersion,
				Jobs: []AgentJob{{
					ID:            10,
					CorrelationID: "job-go-001",
					JobType:       "ping",
					Payload:       map[string]any{},
					Status:        "pending",
				}},
			})
		case "/api/agent/jobs/10/ack":
			sawAck = true
			w.WriteHeader(http.StatusOK)
		case "/api/agent/jobs/10/result":
			sawResult = true
			var payload AgentJobResultPayload
			if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
				t.Fatal(err)
			}
			if payload.CorrelationID != "job-go-001" || payload.Result["pong"] != true {
				t.Fatalf("unexpected result payload: %#v", payload)
			}
			w.WriteHeader(http.StatusOK)
		default:
			t.Fatalf("unexpected path %s", r.URL.Path)
		}
	}))
	defer server.Close()
	runner := &Runner{
		Config:    DefaultConfig(),
		API:       NewAPIClient(server.URL, "ptr_agent_test", time.Second),
		Moonraker: NewMoonrakerClient(server.URL, time.Second),
		Logger:    discardLogger(),
	}
	if err := runner.PollJobsOnce(context.Background()); err != nil {
		t.Fatal(err)
	}
	if !sawAck || !sawResult {
		t.Fatalf("expected ack and result, ack=%v result=%v", sawAck, sawResult)
	}
}

func TestWebSocketURLUsesSecureScheme(t *testing.T) {
	got, err := websocketURL("https://printora.example.com/base")
	if err != nil {
		t.Fatal(err)
	}
	if got != "wss://printora.example.com/api/agent/ws" {
		t.Fatalf("unexpected websocket url %q", got)
	}
}

func TestAgentUpdateAppliesValidatedBinary(t *testing.T) {
	tmpDir := t.TempDir()
	binaryPath := filepath.Join(tmpDir, "printora-agent")
	if err := os.WriteFile(binaryPath, []byte("old-binary"), 0o700); err != nil {
		t.Fatal(err)
	}
	newBinary := []byte("new-binary")
	sum := sha256.Sum256(newBinary)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/manifest":
			_ = json.NewEncoder(w).Encode(UpdateManifest{
				ManifestVersion:    1,
				MinimumVersion:     Version,
				RecommendedVersion: "0.1.1",
				ProtocolMin:        ProtocolVersion,
				ProtocolMax:        ProtocolVersion,
				AutoUpdate:         true,
				Releases: []UpdateRelease{{
					Platform:    Platform(),
					Version:     "0.1.1",
					URL:         "http://" + r.Host + "/binary",
					SHA256:      fmt.Sprintf("%x", sum),
					ProtocolMin: ProtocolVersion,
					ProtocolMax: ProtocolVersion,
				}},
			})
		case "/binary":
			_, _ = w.Write(newBinary)
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()
	runner := updateTestRunner(tmpDir, binaryPath, server.URL+"/manifest")
	result := runner.CheckAgentUpdate(context.Background())
	if result.Status != "applied" {
		t.Fatalf("expected applied, got %#v", result)
	}
	updated, err := os.ReadFile(binaryPath)
	if err != nil {
		t.Fatal(err)
	}
	if string(updated) != "new-binary" {
		t.Fatalf("binary not replaced: %q", updated)
	}
}

func TestAgentUpdateRejectsInvalidHash(t *testing.T) {
	tmpDir := t.TempDir()
	binaryPath := filepath.Join(tmpDir, "printora-agent")
	if err := os.WriteFile(binaryPath, []byte("old-binary"), 0o700); err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/manifest" {
			_ = json.NewEncoder(w).Encode(UpdateManifest{
				ManifestVersion:    1,
				RecommendedVersion: "0.1.1",
				ProtocolMin:        ProtocolVersion,
				ProtocolMax:        ProtocolVersion,
				AutoUpdate:         true,
				Releases: []UpdateRelease{{
					Platform:    Platform(),
					Version:     "0.1.1",
					URL:         "http://" + r.Host + "/binary",
					SHA256:      "bad",
					ProtocolMin: ProtocolVersion,
					ProtocolMax: ProtocolVersion,
				}},
			})
			return
		}
		_, _ = w.Write([]byte("new-binary"))
	}))
	defer server.Close()
	runner := updateTestRunner(tmpDir, binaryPath, server.URL+"/manifest")
	result := runner.CheckAgentUpdate(context.Background())
	if result.Status != "failed" || !strings.Contains(result.Detail, "sha256") {
		t.Fatalf("expected hash failure, got %#v", result)
	}
	current, _ := os.ReadFile(binaryPath)
	if string(current) != "old-binary" {
		t.Fatalf("binary changed after hash failure: %q", current)
	}
}

func TestAgentUpdateRollsBackWhenHealthFails(t *testing.T) {
	tmpDir := t.TempDir()
	binaryPath := filepath.Join(tmpDir, "printora-agent")
	if err := os.WriteFile(binaryPath, []byte("old-binary"), 0o700); err != nil {
		t.Fatal(err)
	}
	newBinary := []byte("new-binary")
	sum := sha256.Sum256(newBinary)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/manifest" {
			_ = json.NewEncoder(w).Encode(UpdateManifest{
				ManifestVersion:    1,
				RecommendedVersion: "0.1.1",
				ProtocolMin:        ProtocolVersion,
				ProtocolMax:        ProtocolVersion,
				AutoUpdate:         true,
				Releases: []UpdateRelease{{
					Platform:    Platform(),
					Version:     "0.1.1",
					URL:         "http://" + r.Host + "/binary",
					SHA256:      fmt.Sprintf("%x", sum),
					ProtocolMin: ProtocolVersion,
					ProtocolMax: ProtocolVersion,
				}},
			})
			return
		}
		_, _ = w.Write(newBinary)
	}))
	defer server.Close()
	runner := updateTestRunner(tmpDir, binaryPath, server.URL+"/manifest")
	runner.Config.UpdateHealthCommand = []string{"false"}
	result := runner.CheckAgentUpdate(context.Background())
	if result.Status != "rolled_back" {
		t.Fatalf("expected rollback, got %#v", result)
	}
	current, _ := os.ReadFile(binaryPath)
	if string(current) != "old-binary" {
		t.Fatalf("rollback did not restore binary: %q", current)
	}
}

func TestAgentUpdateBlocksServerBlockedVersion(t *testing.T) {
	_, result := selectUpdateRelease(UpdateManifest{
		BlockedVersions: []string{Version},
		ProtocolMin:     ProtocolVersion,
		ProtocolMax:     ProtocolVersion,
	}, Platform(), Version)
	if result.Status != "blocked" {
		t.Fatalf("expected blocked, got %#v", result)
	}
}

func TestQueuePersistsAndTrims(t *testing.T) {
	queue := NewQueue(filepath.Join(t.TempDir(), "queue.jsonl"))
	for i := 0; i < 205; i++ {
		if err := queue.Append(QueueItem{Type: "heartbeat", Payload: map[string]any{"i": i}}); err != nil {
			t.Fatal(err)
		}
	}
	items, err := queue.Load()
	if err != nil {
		t.Fatal(err)
	}
	if len(items) != 200 {
		t.Fatalf("expected trimmed queue, got %d", len(items))
	}
}

func updateTestRunner(tmpDir string, binaryPath string, manifestURL string) *Runner {
	cfg := DefaultConfig()
	cfg.UpdateManifestURL = manifestURL
	cfg.UpdateStagingDir = filepath.Join(tmpDir, "updates")
	cfg.UpdateStateFile = filepath.Join(tmpDir, "update-state.json")
	cfg.AgentBinaryPath = binaryPath
	cfg.AllowServiceRestart = false
	return &Runner{
		Config:    cfg,
		API:       NewAPIClient("http://127.0.0.1", "ptr_agent_test", time.Second),
		Moonraker: NewMoonrakerClient("http://127.0.0.1:1", time.Second),
		Logger:    discardLogger(),
	}
}
