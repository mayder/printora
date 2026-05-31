package agent

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
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

type AgentJob struct {
	ID            int            `json:"id"`
	CorrelationID string         `json:"correlation_id"`
	JobType       string         `json:"job_type"`
	Payload       map[string]any `json:"payload"`
	Status        string         `json:"status"`
	Attempts      int            `json:"attempts"`
}

type AgentJobsResponse struct {
	ProtocolVersion int        `json:"protocol_version"`
	Jobs            []AgentJob `json:"jobs"`
}

type AgentJobResultPayload struct {
	CorrelationID string         `json:"correlation_id"`
	Result        map[string]any `json:"result"`
}

type AgentJobErrorPayload struct {
	CorrelationID string         `json:"correlation_id"`
	ErrorMessage  string         `json:"error_message"`
	Result        map[string]any `json:"result"`
}

type AgentUpdateReportPayload struct {
	Status         string `json:"status"`
	CurrentVersion string `json:"current_version"`
	TargetVersion  string `json:"target_version,omitempty"`
	Platform       string `json:"platform,omitempty"`
	Detail         string `json:"detail,omitempty"`
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

func (c *APIClient) NextJobs(ctx context.Context, limit int) ([]AgentJob, error) {
	var response AgentJobsResponse
	if err := c.get(ctx, fmt.Sprintf("/api/agent/jobs/next?limit=%d", limit), &response); err != nil {
		return nil, err
	}
	return response.Jobs, nil
}

func (c *APIClient) AckJob(ctx context.Context, jobID int) error {
	return c.post(ctx, fmt.Sprintf("/api/agent/jobs/%d/ack", jobID), map[string]any{})
}

func (c *APIClient) NackJob(ctx context.Context, jobID int, correlationID string, reason string) error {
	return c.post(ctx, fmt.Sprintf("/api/agent/jobs/%d/nack", jobID), AgentJobErrorPayload{CorrelationID: correlationID, ErrorMessage: reason})
}

func (c *APIClient) ResultJob(ctx context.Context, jobID int, payload AgentJobResultPayload) error {
	return c.post(ctx, fmt.Sprintf("/api/agent/jobs/%d/result", jobID), payload)
}

func (c *APIClient) ErrorJob(ctx context.Context, jobID int, payload AgentJobErrorPayload) error {
	return c.post(ctx, fmt.Sprintf("/api/agent/jobs/%d/error", jobID), payload)
}

func (c *APIClient) UpdateReport(ctx context.Context, payload AgentUpdateReportPayload) error {
	return c.post(ctx, "/api/agent/update/reports", payload)
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

func (c *APIClient) get(ctx context.Context, path string, target any) error {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+path, nil)
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+c.credential)
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("api %s: status %d", path, resp.StatusCode)
	}
	data, err := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if err != nil {
		return err
	}
	return json.Unmarshal(data, target)
}
