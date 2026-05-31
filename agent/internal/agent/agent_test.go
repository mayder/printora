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
	"sync/atomic"
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

func TestReconnectFallbackRepeatsHeartbeatAndPolling(t *testing.T) {
	var heartbeats int32
	var polls int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/agent/heartbeat":
			atomic.AddInt32(&heartbeats, 1)
			w.WriteHeader(http.StatusOK)
		case "/api/agent/snapshots":
			w.WriteHeader(http.StatusOK)
		case "/api/agent/jobs/next":
			atomic.AddInt32(&polls, 1)
			_ = json.NewEncoder(w).Encode(AgentJobsResponse{ProtocolVersion: ProtocolVersion, Jobs: []AgentJob{}})
		case "/server/info", "/printer/info", "/printer/objects/query", "/machine/update/status":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"state": "ready"}})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()
	cfg := DefaultConfig()
	cfg.APIBaseURL = server.URL
	cfg.MoonrakerURL = server.URL
	cfg.QueueFile = filepath.Join(t.TempDir(), "queue.jsonl")
	cfg.IntervalSeconds = 1
	cfg.TimeoutSeconds = 1
	cfg.UpdateEnabled = false
	runner := &Runner{
		Config:    cfg,
		API:       NewAPIClient(server.URL, "ptr_agent_test", time.Second),
		Moonraker: NewMoonrakerClient(server.URL, time.Second),
		Logger:    discardLogger(),
	}
	runner.runReconnectFallback(context.Background(), 1100*time.Millisecond)
	if atomic.LoadInt32(&heartbeats) < 2 {
		t.Fatalf("expected repeated heartbeat fallback, got %d", heartbeats)
	}
	if atomic.LoadInt32(&polls) < 2 {
		t.Fatalf("expected repeated polling fallback, got %d", polls)
	}
}

func TestReconnectBackoffIsCapped(t *testing.T) {
	backoff := minReconnectBackoff
	for i := 0; i < 20; i++ {
		backoff = nextReconnectBackoff(backoff)
	}
	if backoff != maxReconnectBackoff {
		t.Fatalf("expected capped backoff %s, got %s", maxReconnectBackoff, backoff)
	}
}

func TestAgentHandlesRemoteReadOnlyJobWithSanitization(t *testing.T) {
	var sawResult bool
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/agent/jobs/next":
			_ = json.NewEncoder(w).Encode(AgentJobsResponse{
				ProtocolVersion: ProtocolVersion,
				Jobs: []AgentJob{{
					ID:            11,
					CorrelationID: "remote-health-001",
					JobType:       "remote_health",
					Payload:       map[string]any{},
					Status:        "pending",
				}},
			})
		case "/api/agent/jobs/11/ack":
			w.WriteHeader(http.StatusOK)
		case "/api/agent/jobs/11/result":
			sawResult = true
			var payload AgentJobResultPayload
			if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
				t.Fatal(err)
			}
			if payload.CorrelationID != "remote-health-001" || payload.Result["kind"] != "health" {
				t.Fatalf("unexpected remote result: %#v", payload)
			}
			if strings.Contains(string(mustJSON(payload.Result)), "secret-value") {
				t.Fatalf("sensitive value leaked: %#v", payload.Result)
			}
			w.WriteHeader(http.StatusOK)
		case "/server/info", "/printer/info", "/printer/objects/query":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"api_token": "secret-value", "state": "ready"}})
		case "/machine/update/status":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"version": "ok"}})
		default:
			http.NotFound(w, r)
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
	if !sawResult {
		t.Fatal("expected remote result")
	}
}

func TestAgentHandlesRemoteMutationPreflightAndExecute(t *testing.T) {
	var sawExecute bool
	var sawResult bool
	var jobServed bool
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/agent/jobs/next":
			if jobServed {
				_ = json.NewEncoder(w).Encode(AgentJobsResponse{ProtocolVersion: ProtocolVersion, Jobs: []AgentJob{}})
				return
			}
			jobServed = true
			_ = json.NewEncoder(w).Encode(AgentJobsResponse{
				ProtocolVersion: ProtocolVersion,
				Jobs: []AgentJob{{
					ID:            12,
					CorrelationID: "remote-execute-001",
					JobType:       "remote_mutation_execute",
					Payload:       map[string]any{"command_preview": []any{"M106 S64"}, "rollback_plan": []any{"M107"}},
					Status:        "pending",
				}},
			})
		case "/api/agent/jobs/12/ack":
			w.WriteHeader(http.StatusOK)
		case "/api/agent/jobs/12/result":
			sawResult = true
			var payload AgentJobResultPayload
			if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
				t.Fatal(err)
			}
			if payload.Result["status"] != "executed" {
				t.Fatalf("unexpected execution result: %#v", payload.Result)
			}
			w.WriteHeader(http.StatusOK)
		case "/server/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"klippy_state": "ready"}})
		case "/printer/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"state": "ready"}})
		case "/printer/objects/query":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"status": map[string]any{"print_stats": map[string]any{"state": "standby"}}}})
		case "/printer/gcode/script":
			sawExecute = true
			var body map[string]any
			if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
				t.Fatal(err)
			}
			if body["script"] != "M106 S64" {
				t.Fatalf("unexpected script: %#v", body)
			}
			_ = json.NewEncoder(w).Encode(map[string]any{"result": "ok"})
		default:
			http.NotFound(w, r)
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
	if !sawExecute || !sawResult {
		t.Fatalf("expected execute and result, execute=%v result=%v", sawExecute, sawResult)
	}
}

func TestAgentHandlesRemoteDoctorWithSanitizedLogTail(t *testing.T) {
	tmpDir := t.TempDir()
	logPath := filepath.Join(tmpDir, "agent.log")
	credentialPath := filepath.Join(tmpDir, "credential")
	configPath := filepath.Join(tmpDir, "config.json")
	if err := os.WriteFile(logPath, []byte("erro ptr_agent_secret\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(credentialPath, []byte("ptr_agent_test"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(configPath, []byte(`{}`), 0o600); err != nil {
		t.Fatal(err)
	}
	var sawResult bool
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/agent/jobs/next":
			_ = json.NewEncoder(w).Encode(AgentJobsResponse{
				ProtocolVersion: ProtocolVersion,
				Jobs: []AgentJob{{
					ID:            13,
					CorrelationID: "remote-doctor-001",
					JobType:       "remote_doctor",
					Payload:       map[string]any{},
					Status:        "pending",
				}},
			})
		case "/api/agent/jobs/13/ack":
			w.WriteHeader(http.StatusOK)
		case "/api/agent/jobs/13/result":
			sawResult = true
			var payload AgentJobResultPayload
			if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
				t.Fatal(err)
			}
			data := string(mustJSON(payload.Result))
			if !strings.Contains(data, "remote_doctor") {
				t.Fatalf("unexpected doctor payload: %s", data)
			}
			if strings.Contains(data, "ptr_agent_secret") {
				t.Fatalf("secret leaked in doctor payload: %s", data)
			}
			w.WriteHeader(http.StatusOK)
		case "/api/agent/heartbeat":
			w.WriteHeader(http.StatusOK)
		case "/server/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": "ok"})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()
	cfg := DefaultConfig()
	cfg.APIBaseURL = server.URL
	cfg.MoonrakerURL = server.URL
	cfg.CredentialFile = credentialPath
	cfg.LogFile = logPath
	cfg.QueueFile = filepath.Join(tmpDir, "queue.jsonl")
	cfg.configPath = configPath
	runner := &Runner{
		Config:    cfg,
		API:       NewAPIClient(server.URL, "ptr_agent_test", time.Second),
		Moonraker: NewMoonrakerClient(server.URL, time.Second),
		Logger:    discardLogger(),
	}
	if err := runner.PollJobsOnce(context.Background()); err != nil {
		t.Fatal(err)
	}
	if !sawResult {
		t.Fatal("expected doctor result")
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

func mustJSON(value any) []byte {
	data, err := json.Marshal(value)
	if err != nil {
		panic(err)
	}
	return data
}

func TestAgentUpdateAppliesValidatedBinary(t *testing.T) {
	targetVersion := "99.0.0"
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
				RecommendedVersion: targetVersion,
				ProtocolMin:        ProtocolVersion,
				ProtocolMax:        ProtocolVersion,
				AutoUpdate:         true,
				Releases: []UpdateRelease{{
					Platform:    Platform(),
					Version:     targetVersion,
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
	targetVersion := "99.0.0"
	tmpDir := t.TempDir()
	binaryPath := filepath.Join(tmpDir, "printora-agent")
	if err := os.WriteFile(binaryPath, []byte("old-binary"), 0o700); err != nil {
		t.Fatal(err)
	}
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/manifest" {
			_ = json.NewEncoder(w).Encode(UpdateManifest{
				ManifestVersion:    1,
				RecommendedVersion: targetVersion,
				ProtocolMin:        ProtocolVersion,
				ProtocolMax:        ProtocolVersion,
				AutoUpdate:         true,
				Releases: []UpdateRelease{{
					Platform:    Platform(),
					Version:     targetVersion,
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
	targetVersion := "99.0.0"
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
				RecommendedVersion: targetVersion,
				ProtocolMin:        ProtocolVersion,
				ProtocolMax:        ProtocolVersion,
				AutoUpdate:         true,
				Releases: []UpdateRelease{{
					Platform:    Platform(),
					Version:     targetVersion,
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
