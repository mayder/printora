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
	"runtime"
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

func TestGcodeStoreDeltaKeepsOnlyNewConsoleMessages(t *testing.T) {
	before := []string{
		"B:21.2 /0.0 T0:216.3 /220.0",
		"// PID parameters: pid_Kp=42.725 pid_Ki=11.393 pid_Kd=40.055",
		"G28",
		"// Found active tool probe: tool_probe T0",
	}
	after := []string{
		"B:21.1 /0.0 T0:214.5 /220.0",
		"B:21.2 /0.0 T0:216.3 /220.0",
		"// PID parameters: pid_Kp=42.725 pid_Ki=11.393 pid_Kd=40.055",
		"G28",
		"// Found active tool probe: tool_probe T0",
		"G28",
		"// toolchanger initialized, active tool T0",
	}

	delta := gcodeStoreDelta(before, after)

	if strings.Join(delta, "\n") != "G28\n// toolchanger initialized, active tool T0" {
		t.Fatalf("unexpected delta: %#v", delta)
	}
}

func TestHostMetricsClassifiesKnownKlipperServices(t *testing.T) {
	cases := map[string]string{
		"/usr/local/bin/printora-agent -config /etc/printora-agent/config.json": "printora-agent",
		"/home/pi/moonraker-env/bin/python /home/pi/moonraker/moonraker.py":     "moonraker",
		"/home/pi/klippy-env/bin/python /home/pi/klipper/klippy/klippy.py":      "klipper",
		"/usr/bin/nginx -g daemon off;":                                         "mainsail/nginx",
		"/opt/spoolman/venv/bin/python -m spoolman":                             "spoolman",
	}
	for command, expected := range cases {
		if got := classifyService(command); got != expected {
			t.Fatalf("classifyService(%q)=%q, expected %q", command, got, expected)
		}
	}
}

func TestHostMetricsCPUUsesPreviousCachedSample(t *testing.T) {
	previous := map[int]processSample{
		100: {
			pid:       100,
			service:   "printora-agent",
			command:   "/usr/local/bin/printora-agent -config /etc/printora-agent/config.json",
			cpuTicks:  10,
			totalTick: 1000,
		},
	}
	current := map[int]processSample{
		100: {
			pid:       100,
			service:   "printora-agent",
			command:   "/usr/local/bin/printora-agent -config /etc/printora-agent/config.json",
			cpuTicks:  20,
			rssBytes:  12 * 1024 * 1024,
			vszBytes:  1200 * 1024 * 1024,
			totalTick: 1100,
		},
	}

	services := serviceMetricsPayload(previous, current)
	if len(services) != 1 {
		t.Fatalf("expected one service metric, got %#v", services)
	}
	metric, ok := services[0].(map[string]any)
	if !ok {
		t.Fatalf("unexpected metric type: %#v", services[0])
	}
	expectedCPU := roundMetric((float64(20-10) / float64(1100-1000)) * float64(runtime.NumCPU()) * 100)
	if metric["cpu_percent"] != expectedCPU {
		t.Fatalf("unexpected cpu percent: %#v, expected %#v", metric["cpu_percent"], expectedCPU)
	}
	if metric["rss_bytes"] != uint64(12*1024*1024) {
		t.Fatalf("unexpected rss: %#v", metric["rss_bytes"])
	}

	warmupServices := serviceMetricsPayload(nil, current)
	warmupMetric := warmupServices[0].(map[string]any)
	if warmupMetric["cpu_percent"] != nil {
		t.Fatalf("warmup sample should not synthesize cpu usage: %#v", warmupMetric["cpu_percent"])
	}
}

func TestRunnerCapabilitiesIncludeCachedHostMetrics(t *testing.T) {
	runner := &Runner{Config: DefaultConfig(), startedAt: time.Now()}
	capabilities := runner.capabilities(context.Background(), false)
	if capabilities["protocol_v"] != ProtocolVersion {
		t.Fatalf("missing protocol_v: %#v", capabilities)
	}
	metrics, ok := capabilities["host_metrics"].(map[string]any)
	if !ok {
		t.Fatalf("missing host metrics: %#v", capabilities)
	}
	if metrics["safe_mode"] != "host_metrics_current" {
		t.Fatalf("unexpected host metrics payload: %#v", metrics)
	}
	if _, ok := metrics["services"]; runtime.GOOS == "linux" && !ok {
		t.Fatalf("expected linux service metrics: %#v", metrics)
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
	var snapshots int32
	var moonrakerReads int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/api/agent/heartbeat":
			atomic.AddInt32(&heartbeats, 1)
			w.WriteHeader(http.StatusOK)
		case "/api/agent/snapshots":
			atomic.AddInt32(&snapshots, 1)
			w.WriteHeader(http.StatusOK)
		case "/api/agent/jobs/next":
			atomic.AddInt32(&polls, 1)
			_ = json.NewEncoder(w).Encode(AgentJobsResponse{ProtocolVersion: ProtocolVersion, Jobs: []AgentJob{}})
		case "/server/info", "/printer/info", "/printer/objects/query", "/machine/update/status":
			atomic.AddInt32(&moonrakerReads, 1)
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
	if atomic.LoadInt32(&snapshots) != 0 || atomic.LoadInt32(&moonrakerReads) != 0 {
		t.Fatalf("fallback should not read moonraker automatically, snapshots=%d moonraker=%d", snapshots, moonrakerReads)
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

func TestAgentHandlesRemoteSelfUpdateJob(t *testing.T) {
	var sawReport bool
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
					ID:            14,
					CorrelationID: "remote-agent-update-001",
					JobType:       "remote_agent_update_check",
					Payload:       map[string]any{"safe_mode": "agent_self_update"},
					Status:        "pending",
				}},
			})
		case "/api/agent/jobs/14/ack":
			w.WriteHeader(http.StatusOK)
		case "/api/agent/update/manifest":
			_ = json.NewEncoder(w).Encode(UpdateManifest{
				ManifestVersion:    1,
				RecommendedVersion: Version,
				ProtocolMin:        ProtocolVersion,
				ProtocolMax:        ProtocolVersion,
				AutoUpdate:         true,
				Releases: []UpdateRelease{{
					Platform:    Platform(),
					Version:     Version,
					ProtocolMin: ProtocolVersion,
					ProtocolMax: ProtocolVersion,
				}},
			})
		case "/api/agent/update/reports":
			sawReport = true
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte(`{"id":1,"printer_id":1,"agent_id":1,"event_type":"agent_update","status":"skipped","detail":"{}","created_at":"now"}`))
		case "/api/agent/jobs/14/result":
			sawResult = true
			var payload AgentJobResultPayload
			if err := json.NewDecoder(r.Body).Decode(&payload); err != nil {
				t.Fatal(err)
			}
			if payload.CorrelationID != "remote-agent-update-001" || payload.Result["status"] != "skipped" {
				t.Fatalf("unexpected update result: %#v", payload)
			}
			w.WriteHeader(http.StatusOK)
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()
	cfg := DefaultConfig()
	cfg.APIBaseURL = server.URL
	cfg.UpdateManifestURL = server.URL + "/api/agent/update/manifest"
	cfg.QueueFile = filepath.Join(t.TempDir(), "queue.jsonl")
	runner := &Runner{
		Config:    cfg,
		API:       NewAPIClient(server.URL, "ptr_agent_test", time.Second),
		Moonraker: NewMoonrakerClient(server.URL, time.Second),
		Logger:    discardLogger(),
	}
	if err := runner.PollJobsOnce(context.Background()); err != nil {
		t.Fatal(err)
	}
	if !sawReport || !sawResult {
		t.Fatalf("expected update report and result, report=%v result=%v", sawReport, sawResult)
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

func TestRemoteGcodeExecuteTreatsAwaitingHeadersTimeoutAsDispatched(t *testing.T) {
	var sawExecute bool
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/server/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"klippy_state": "ready"}})
		case "/printer/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"state": "ready"}})
		case "/printer/objects/list":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"objects": []any{"toolhead", "print_stats"}}})
		case "/printer/objects/query":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"status": map[string]any{"print_stats": map[string]any{"state": "standby"}}}})
		case "/printer/gcode/script":
			sawExecute = true
			time.Sleep(30 * time.Millisecond)
			_ = json.NewEncoder(w).Encode(map[string]any{"result": "ok"})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	client := NewMoonrakerClient(server.URL, time.Millisecond)
	result := client.RemoteGcodeExecute(context.Background(), map[string]any{"commands": []any{"G28"}})
	if !sawExecute {
		t.Fatal("expected gcode request to reach Moonraker")
	}
	if result["status"] != "dispatched_unconfirmed" {
		t.Fatalf("unexpected status: %#v", result)
	}
	sent, ok := result["sent_commands"].([]any)
	if !ok || len(sent) != 1 || sent[0] != "G28" {
		t.Fatalf("unexpected sent commands: %#v", result["sent_commands"])
	}
}

func TestRemoteGcodeUploadSendsMultipartFileAndCanStartPrint(t *testing.T) {
	var sawUpload bool
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/server/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"klippy_state": "ready"}})
		case "/printer/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"state": "ready"}})
		case "/printer/objects/list":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"objects": []any{"toolhead", "print_stats"}}})
		case "/printer/objects/query":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"status": map[string]any{"print_stats": map[string]any{"state": "standby"}}}})
		case "/server/files/upload":
			sawUpload = true
			if err := r.ParseMultipartForm(1024 * 1024); err != nil {
				t.Fatal(err)
			}
			if r.FormValue("root") != "gcodes" || r.FormValue("path") != "printora" || r.FormValue("print") != "true" {
				t.Fatalf("unexpected upload form: %#v", r.Form)
			}
			file, header, err := r.FormFile("file")
			if err != nil {
				t.Fatal(err)
			}
			defer file.Close()
			if header.Filename != "cube_job_1.gcode" {
				t.Fatalf("unexpected filename: %s", header.Filename)
			}
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"item": map[string]any{"path": "printora/cube_job_1.gcode"}}})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	client := NewMoonrakerClient(server.URL, time.Second)
	result := client.RemoteGcodeUpload(context.Background(), map[string]any{
		"remote_filename": "printora/cube_job_1.gcode",
		"gcode_content":   "G28\n",
		"start_print":     true,
	})
	if !sawUpload {
		t.Fatal("expected upload request")
	}
	if result["status"] != "started" || result["started"] != true {
		t.Fatalf("unexpected upload result: %#v", result)
	}
	if _, leaked := result["gcode_content"]; leaked {
		t.Fatalf("gcode content leaked in result: %#v", result)
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
