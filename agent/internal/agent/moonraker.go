package agent

import (
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
