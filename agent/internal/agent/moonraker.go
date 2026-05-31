package agent

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
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

func (c *MoonrakerClient) Doctor(ctx context.Context) error {
	payload := map[string]any{}
	if err := c.get(ctx, "/server/info", "server_info", payload); err != nil {
		return err
	}
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
