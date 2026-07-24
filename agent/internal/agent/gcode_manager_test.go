package agent

import (
	"context"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"
	"time"
)

func TestRemoteGcodeManagerCoversQueueDirectoryPreheatAndBatchActions(t *testing.T) {
	var queueMutations atomic.Int32
	var fileMutations atomic.Int32
	var scripts atomic.Int32
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/server/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"klippy_state": "ready"}})
		case "/printer/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"state": "ready"}})
		case "/printer/objects/list":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"objects": []any{"print_stats"}}})
		case "/printer/objects/query":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"status": map[string]any{"print_stats": map[string]any{"state": "standby"}}}})
		case "/server/job_queue/status":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"queue_state": "ready", "queued_jobs": []any{}}})
		case "/server/job_queue/job", "/server/job_queue/pause", "/server/job_queue/start":
			queueMutations.Add(1)
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"ok": true}})
		case "/server/files/directory", "/server/files/move", "/server/files/copy":
			fileMutations.Add(1)
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"ok": true}})
		case "/server/files/gcodes/jobs/old.gcode":
			fileMutations.Add(1)
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"ok": true}})
		case "/printer/gcode/script":
			scripts.Add(1)
			_ = json.NewEncoder(w).Encode(map[string]any{"result": "ok"})
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	client := NewMoonrakerClient(server.URL, time.Second)
	cases := []map[string]any{
		{"action": "queue_status"},
		{"action": "queue_add", "filenames": []string{"jobs/a.gcode", "jobs/b.gcode"}},
		{"action": "queue_remove", "job_ids": []any{"1", "2"}},
		{"action": "queue_pause"},
		{"action": "queue_resume"},
		{"action": "queue_start"},
		{"action": "directory_move", "directory": "jobs/old", "target_directory": "jobs/new"},
		{"action": "directory_delete", "directory": "jobs/new"},
		{"action": "preheat", "hotend_temperature": 205.0, "bed_temperature": 60.0},
		{"action": "batch_duplicate", "filenames": []any{"jobs/a.gcode"}},
		{"action": "batch_move", "filenames": []any{"jobs/b.gcode"}, "target_directory": "archive"},
		{"action": "batch_delete", "filenames": []any{"jobs/old.gcode"}},
	}
	for _, payload := range cases {
		result := client.RemoteGcodeManager(context.Background(), payload)
		if result["status"] != "executed" {
			t.Fatalf("action %q failed: %#v", payload["action"], result)
		}
	}
	if queueMutations.Load() != 5 {
		t.Fatalf("unexpected queue mutation count: %d", queueMutations.Load())
	}
	if fileMutations.Load() != 5 {
		t.Fatalf("unexpected file mutation count: %d", fileMutations.Load())
	}
	if scripts.Load() != 2 {
		t.Fatalf("expected one command per heater, got %d", scripts.Load())
	}
}

func TestRemoteGcodeManagerRejectsInvalidInputs(t *testing.T) {
	client := NewMoonrakerClient("http://127.0.0.1:1", 10*time.Millisecond)
	cases := []map[string]any{
		{"action": "unknown"},
		{"action": "metadata_scan", "filename": "../secret.gcode"},
		{"action": "preheat", "hotend_temperature": 301},
		{"action": "directory_create", "directory": "../jobs"},
		{"action": "queue_add", "filenames": []any{"invalid.txt"}},
		{"action": "queue_remove", "job_ids": []any{}},
		{"action": "batch_move", "filenames": []any{"a.gcode"}},
		{"action": "batch_delete", "filenames": []any{}},
	}
	for _, payload := range cases {
		result := client.RemoteGcodeManager(context.Background(), payload)
		if result["status"] != "failed" && result["status"] != "blocked" {
			t.Fatalf("action %q should fail safely: %#v", payload["action"], result)
		}
	}
	if cleanRelativeGcodeDirectory("jobs\\today") != "jobs/today" ||
		cleanRelativeGcodeDirectory("jobs/./today") != "" ||
		cleanRelativeGcodeDirectory("/") != "" {
		t.Fatal("unexpected directory normalization")
	}
	if got := cleanGcodeFilenameList([]string{"a.gcode", "bad.txt"}); len(got) != 1 || got[0] != "a.gcode" {
		t.Fatalf("unexpected filename list: %#v", got)
	}
	if got := cleanStringList([]string{"ignored"}, 10); got != nil {
		t.Fatalf("non-any string list should be rejected: %#v", got)
	}
}

func TestRunnerRemoteGcodeUploadDownloadsStagedBody(t *testing.T) {
	var downloaded atomic.Bool
	cloud := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path != "/api/agent/gcode-uploads/upload-key" {
			http.NotFound(w, r)
			return
		}
		if r.Header.Get("Authorization") != "Bearer credential" {
			t.Fatal("missing agent authorization")
		}
		downloaded.Store(true)
		_, _ = w.Write([]byte("; staged\nM117 PRINTORA TEST\n"))
	}))
	defer cloud.Close()

	var uploaded atomic.Bool
	moonraker := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch r.URL.Path {
		case "/server/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"klippy_state": "ready"}})
		case "/printer/info":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"state": "ready"}})
		case "/printer/objects/list":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"objects": []any{"print_stats"}}})
		case "/printer/objects/query":
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"status": map[string]any{"print_stats": map[string]any{"state": "standby"}}}})
		case "/server/files/metadata":
			http.NotFound(w, r)
		case "/server/files/upload":
			file, _, err := r.FormFile("file")
			if err != nil {
				t.Fatal(err)
			}
			defer file.Close()
			body, _ := io.ReadAll(file)
			if !strings.Contains(string(body), "PRINTORA TEST") {
				t.Fatalf("unexpected staged body: %q", body)
			}
			uploaded.Store(true)
			_ = json.NewEncoder(w).Encode(map[string]any{"result": map[string]any{"item": map[string]any{"path": "smoke.gcode"}}})
		default:
			http.NotFound(w, r)
		}
	}))
	defer moonraker.Close()

	runner := &Runner{
		API:       NewAPIClient(cloud.URL, "credential", time.Second),
		Moonraker: NewMoonrakerClient(moonraker.URL, time.Second),
	}
	result := runner.RemoteGcodeUpload(context.Background(), map[string]any{
		"upload_key":      "upload-key",
		"remote_filename": "smoke.gcode",
	})
	if result["status"] != "uploaded" || !downloaded.Load() || !uploaded.Load() {
		t.Fatalf("unexpected staged upload result: %#v", result)
	}

	failedRunner := &Runner{
		API:       NewAPIClient(cloud.URL, "credential", time.Second),
		Moonraker: runner.Moonraker,
	}
	failed := failedRunner.RemoteGcodeUpload(context.Background(), map[string]any{
		"upload_key":      "missing",
		"remote_filename": "missing.gcode",
	})
	if failed["status"] != "failed" || failed["safe_mode"] != "remote_gcode_upload_failed" {
		t.Fatalf("unexpected failed staged upload: %#v", failed)
	}
}
