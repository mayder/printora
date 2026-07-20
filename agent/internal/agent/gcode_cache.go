package agent

import (
	"context"
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

const maxGcodeCacheBytes = 96 * 1024 * 1024

type readCloserWithLimit struct {
	io.Reader
	io.Closer
}

func (r *Runner) RemoteGcodeCache(ctx context.Context, payload map[string]any) map[string]any {
	filename := stringValue(payload["filename"])
	cacheKey := stringValue(payload["cache_key"])
	maxBytes := int64Number(payload["max_bytes"])
	if maxBytes <= 0 || maxBytes > maxGcodeCacheBytes {
		maxBytes = maxGcodeCacheBytes
	}
	if filename == "" || cacheKey == "" {
		return map[string]any{
			"safe_mode": "read_only",
			"kind":      "gcode_cache",
			"status":    "failed",
			"detail":    "filename e cache_key são obrigatórios",
		}
	}
	body, err := r.Moonraker.openGcodeFile(ctx, filename, maxBytes)
	if err != nil {
		return map[string]any{
			"safe_mode": "read_only",
			"kind":      "gcode_cache",
			"status":    "failed",
			"detail":    err.Error(),
			"filename":  filename,
			"cache_key": cacheKey,
		}
	}
	defer body.Close()

	result, err := r.API.UploadGcodeCache(ctx, cacheKey, filename, body)
	if err != nil {
		return map[string]any{
			"safe_mode": "read_only",
			"kind":      "gcode_cache",
			"status":    "failed",
			"detail":    err.Error(),
			"filename":  filename,
			"cache_key": cacheKey,
		}
	}
	result["safe_mode"] = "read_only"
	result["kind"] = "gcode_cache"
	if _, ok := result["status"]; !ok {
		result["status"] = "cached"
	}
	return sanitizeMap(result)
}

func (c *MoonrakerClient) openGcodeFile(ctx context.Context, filename string, maxBytes int64) (io.ReadCloser, error) {
	if strings.TrimSpace(filename) == "" {
		return nil, fmt.Errorf("nome de G-code inválido")
	}
	target := strings.TrimRight(c.baseURL, "/") + "/server/files/gcodes/" + escapePathSegments(filename)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		return nil, err
	}
	client := *c.http
	client.Timeout = 2 * time.Minute
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		defer resp.Body.Close()
		return nil, fmt.Errorf("moonraker file download status %d", resp.StatusCode)
	}
	if resp.ContentLength > maxBytes {
		defer resp.Body.Close()
		return nil, fmt.Errorf("G-code excede o limite de cache")
	}
	return &readCloserWithLimit{Reader: io.LimitReader(resp.Body, maxBytes+1), Closer: resp.Body}, nil
}

func int64Number(value any) int64 {
	switch typed := value.(type) {
	case float64:
		return int64(typed)
	case int:
		return int64(typed)
	case int64:
		return typed
	default:
		return 0
	}
}
