package agent

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"
)

type APIClient struct {
	baseURL    string
	credential string
	http       *http.Client
}

type HeartbeatPayload struct {
	AgentVersion string         `json:"agent_version"`
	Platform     string         `json:"platform"`
	Capabilities map[string]any `json:"capabilities"`
}

type SnapshotPayload struct {
	Payload map[string]any `json:"payload"`
}

func NewAPIClient(baseURL string, credential string, timeout time.Duration) *APIClient {
	return &APIClient{
		baseURL:    strings.TrimRight(baseURL, "/"),
		credential: credential,
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

func (c *APIClient) Heartbeat(ctx context.Context, payload HeartbeatPayload) error {
	return c.post(ctx, "/api/agent/heartbeat", payload)
}

func (c *APIClient) Snapshot(ctx context.Context, payload SnapshotPayload) error {
	return c.post(ctx, "/api/agent/snapshots", payload)
}

func (c *APIClient) Doctor(ctx context.Context) error {
	return c.Heartbeat(ctx, HeartbeatPayload{
		AgentVersion: Version,
		Platform:     Platform(),
		Capabilities: map[string]any{"doctor": true},
	})
}

func (c *APIClient) post(ctx context.Context, path string, payload any) error {
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+path, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+c.credential)
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("api %s: status %d", path, resp.StatusCode)
	}
	return nil
}
