package agent

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"sort"
	"strings"
	"time"
)

type MoonrakerClient struct {
	baseURL string
	http    *http.Client
}

func NewMoonrakerClient(baseURL string, timeout time.Duration) *MoonrakerClient {
	return &MoonrakerClient{
		baseURL: strings.TrimRight(baseURL, "/"),
		http: &http.Client{
			Timeout: timeout,
			Transport: &http.Transport{
				MaxIdleConns:        4,
				MaxIdleConnsPerHost: 2,
				IdleConnTimeout:     30 * time.Second,
			},
		},
	}
}

func (c *MoonrakerClient) Snapshot(ctx context.Context) map[string]any {
	result := map[string]any{
		"safe_mode": "read_only",
	}
	c.get(ctx, "/server/info", "server_info", result)
	c.get(ctx, "/printer/info", "printer_info", result)
	c.get(ctx, "/printer/objects/query?print_stats", "print_stats", result)
	c.get(ctx, "/printer/objects/query?extruder=temperature,target&heater_bed=temperature,target", "temperatures", result)
	c.get(ctx, "/machine/update/status", "update_status", result)
	return result
}

func (c *MoonrakerClient) RemotePayload(ctx context.Context, jobType string) map[string]any {
	switch jobType {
	case "remote_audit":
		return sanitizeMap(map[string]any{
			"safe_mode": "read_only",
			"kind":      "audit",
			"snapshot":  c.Snapshot(ctx),
		})
	case "remote_snapshot":
		return sanitizeMap(c.Snapshot(ctx))
	case "remote_health":
		snapshot := c.Snapshot(ctx)
		return sanitizeMap(map[string]any{
			"safe_mode":    "read_only",
			"kind":         "health",
			"server_info":  snapshot["server_info"],
			"printer_info": snapshot["printer_info"],
			"print_stats":  snapshot["print_stats"],
			"errors":       snapshotErrors(snapshot),
		})
	case "remote_temperatures":
		payload := map[string]any{"safe_mode": "read_only", "kind": "temperatures"}
		c.get(ctx, "/printer/objects/query?extruder=temperature,target&heater_bed=temperature,target", "temperatures", payload)
		return sanitizeMap(payload)
	case "remote_update_status":
		payload := map[string]any{"safe_mode": "read_only", "kind": "update_status"}
		c.get(ctx, "/machine/update/status", "update_status", payload)
		return sanitizeMap(payload)
	case "remote_can_status":
		return sanitizeMap(map[string]any{
			"safe_mode": "read_only",
			"kind":      "can_status",
			"status":    "not_supported",
			"detail":    "CAN remoto exige helper local dedicado em pacote futuro; nenhum comando foi executado.",
		})
	case "remote_final_validation":
		return sanitizeMap(map[string]any{
			"safe_mode": "read_only",
			"kind":      "final_validation",
			"snapshot":  c.Snapshot(ctx),
			"status":    "read_only_collected",
		})
	case "remote_report_sanitized":
		return sanitizeMap(map[string]any{
			"safe_mode": "read_only",
			"kind":      "sanitized_report",
			"snapshot":  c.Snapshot(ctx),
		})
	case "remote_backup_preview":
		return map[string]any{
			"safe_mode": "dry_run",
			"kind":      "backup_preview",
			"status":    "planned",
			"detail":    "Backup real não transferido; payload grande bloqueado até política de retenção.",
		}
	case "remote_operation_preview":
		return map[string]any{
			"safe_mode": "dry_run",
			"kind":      "operation_preview",
			"status":    "blocked",
			"detail":    "Operações mutáveis exigem autorização/preflight do PKG-47.",
		}
	case "remote_firmware_preview":
		return map[string]any{
			"safe_mode": "dry_run",
			"kind":      "firmware_preview",
			"status":    "blocked",
			"detail":    "Build/flash remoto exige gates de firmware e PKG-47.",
		}
	default:
		return map[string]any{"safe_mode": "read_only", "status": "not_supported", "job_type": jobType}
	}
}

func (c *MoonrakerClient) RemoteMutationPreflight(ctx context.Context, jobPayload map[string]any) map[string]any {
	payload := map[string]any{
		"safe_mode":   "remote_mutation_preflight",
		"kind":        "mutation_preflight",
		"action_id":   stringValue(jobPayload["action_id"]),
		"criticality": stringValue(jobPayload["criticality"]),
	}
	c.get(ctx, "/server/info", "server_info", payload)
	c.get(ctx, "/printer/info", "printer_info", payload)
	c.get(ctx, "/printer/objects/query?print_stats&toolhead&gcode_move&extruder", "object_status", payload)
	blockers := remotePreflightBlockers(payload)
	payload["connected"] = !hasMoonrakerError(payload)
	payload["printing"] = remotePrintState(payload) != "" && !remotePrintIdle(remotePrintState(payload))
	payload["print_state"] = remotePrintState(payload)
	payload["klipper_state"] = nestedString(payload["printer_info"], "result", "state")
	payload["klippy_state"] = nestedString(payload["server_info"], "result", "klippy_state")
	payload["blockers"] = blockers
	payload["can_execute"] = len(blockers) == 0
	payload["rollback_plan"] = jobPayload["rollback_plan"]
	return sanitizeMap(payload)
}

func (c *MoonrakerClient) RemoteMutationExecute(ctx context.Context, jobPayload map[string]any) map[string]any {
	preflight := c.RemoteMutationPreflight(ctx, jobPayload)
	if preflight["can_execute"] != true {
		return sanitizeMap(map[string]any{
			"safe_mode": "remote_mutation_blocked",
			"kind":      "mutation_execute",
			"status":    "blocked",
			"detail":    "preflight remoto bloqueou a execução",
			"preflight": preflight,
		})
	}
	commands := stringList(jobPayload["command_preview"])
	if len(commands) == 0 {
		return sanitizeMap(map[string]any{
			"safe_mode": "remote_mutation_blocked",
			"kind":      "mutation_execute",
			"status":    "blocked",
			"detail":    "job remoto sem comando permitido",
			"preflight": preflight,
		})
	}
	result := map[string]any{
		"safe_mode":     "remote_mutation_execute",
		"kind":          "mutation_execute",
		"status":        "executed",
		"preflight":     preflight,
		"command_count": len(commands),
		"rollback_plan": jobPayload["rollback_plan"],
	}
	if err := c.post(ctx, "/printer/gcode/script", map[string]any{"script": strings.Join(commands, "\n")}, "moonraker_response", result); err != nil {
		result["status"] = "failed"
		result["detail"] = err.Error()
	}
	return sanitizeMap(result)
}

func (c *MoonrakerClient) Doctor(ctx context.Context) error {
	payload := map[string]any{}
	if err := c.get(ctx, "/server/info", "server_info", payload); err != nil {
		return err
	}
	return nil
}

func snapshotErrors(snapshot map[string]any) []string {
	var errors []string
	for key, value := range snapshot {
		if strings.HasSuffix(key, "_error") {
			errors = append(errors, fmt.Sprintf("%s=%v", key, value))
		}
	}
	sort.Strings(errors)
	return errors
}

func remotePreflightBlockers(payload map[string]any) []string {
	var blockers []string
	if hasMoonrakerError(payload) {
		blockers = append(blockers, "Moonraker indisponível no preflight remoto.")
	}
	klipperState := nestedString(payload["printer_info"], "result", "state")
	if klipperState != "" && klipperState != "ready" {
		blockers = append(blockers, fmt.Sprintf("Klipper não está ready (%s).", klipperState))
	}
	klippyState := nestedString(payload["server_info"], "result", "klippy_state")
	if klippyState != "" && klippyState != "ready" {
		blockers = append(blockers, fmt.Sprintf("Klippy não está ready (%s).", klippyState))
	}
	printState := remotePrintState(payload)
	if printState != "" && !remotePrintIdle(printState) {
		blockers = append(blockers, fmt.Sprintf("Impressão em andamento (%s).", printState))
	}
	return blockers
}

func hasMoonrakerError(payload map[string]any) bool {
	for key := range payload {
		if strings.HasSuffix(key, "_error") {
			return true
		}
	}
	return false
}

func remotePrintState(payload map[string]any) string {
	return nestedString(payload["object_status"], "result", "status", "print_stats", "state")
}

func remotePrintIdle(state string) bool {
	switch state {
	case "", "standby", "complete", "cancelled", "error":
		return true
	default:
		return false
	}
}

func nestedString(value any, path ...string) string {
	current := value
	for _, key := range path {
		mapped, ok := current.(map[string]any)
		if !ok {
			return ""
		}
		current = mapped[key]
	}
	return stringValue(current)
}

func stringList(value any) []string {
	items, ok := value.([]any)
	if !ok {
		if strings, ok := value.([]string); ok {
			return strings
		}
		return nil
	}
	result := make([]string, 0, len(items))
	for _, item := range items {
		if text := strings.TrimSpace(stringValue(item)); text != "" {
			result = append(result, text)
		}
	}
	return result
}

func sanitizePayload(value any) any {
	switch typed := value.(type) {
	case map[string]any:
		cleaned := map[string]any{}
		for key, item := range typed {
			lowerKey := strings.ToLower(key)
			if strings.Contains(lowerKey, "password") || strings.Contains(lowerKey, "token") || strings.Contains(lowerKey, "secret") || strings.Contains(lowerKey, "credential") || strings.Contains(lowerKey, "private_key") {
				cleaned[key] = "[redacted]"
				continue
			}
			cleaned[key] = sanitizePayload(item)
		}
		return cleaned
	case []any:
		cleaned := make([]any, 0, len(typed))
		for _, item := range typed {
			cleaned = append(cleaned, sanitizePayload(item))
		}
		return cleaned
	default:
		return typed
	}
}

func sanitizeMap(value map[string]any) map[string]any {
	if mapped, ok := sanitizePayload(value).(map[string]any); ok {
		return mapped
	}
	return map[string]any{}
}

func (c *MoonrakerClient) post(ctx context.Context, path string, payload map[string]any, key string, out map[string]any) error {
	target, err := url.JoinPath(c.baseURL, strings.TrimPrefix(path, "/"))
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	body, err := json.Marshal(payload)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, target, bytes.NewReader(body))
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := c.http.Do(req)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		err := fmt.Errorf("moonraker %s: status %d", path, resp.StatusCode)
		out[key+"_error"] = err.Error()
		return err
	}
	var decoded any
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	out[key] = decoded
	return nil
}

func (c *MoonrakerClient) get(ctx context.Context, path string, key string, out map[string]any) error {
	target, err := url.JoinPath(c.baseURL, strings.TrimPrefix(strings.Split(path, "?")[0], "/"))
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	if strings.Contains(path, "?") {
		target += "?" + strings.SplitN(path, "?", 2)[1]
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	resp, err := c.http.Do(req)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		err := fmt.Errorf("moonraker %s: status %d", path, resp.StatusCode)
		out[key+"_error"] = err.Error()
		return err
	}
	var decoded any
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	out[key] = decoded
	return nil
}
