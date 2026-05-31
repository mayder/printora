package agent

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"time"

	"nhooyr.io/websocket"
)

type ProtocolMessage struct {
	ProtocolVersion int            `json:"protocol_version"`
	MessageType     string         `json:"message_type"`
	CorrelationID   string         `json:"correlation_id"`
	Payload         map[string]any `json:"payload"`
}

func (r *Runner) RunChannel(ctx context.Context) error {
	backoff := time.Second
	for {
		if err := r.runWebSocket(ctx); err != nil {
			r.Logger.Printf("websocket unavailable, fallback polling: %v", err)
			if r.Config.PollingEnabled {
				if pollErr := r.PollJobsOnce(ctx); pollErr != nil {
					r.Logger.Printf("polling fallback failed: %v", pollErr)
				}
			}
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(backoff):
		}
		if backoff < 30*time.Second {
			backoff *= 2
		}
	}
}

func (r *Runner) PollJobsOnce(ctx context.Context) error {
	jobs, err := r.API.NextJobs(ctx, 10)
	if err != nil {
		return err
	}
	for _, job := range jobs {
		r.handleJob(ctx, job)
	}
	return nil
}

func (r *Runner) runWebSocket(ctx context.Context) error {
	wsURL, err := websocketURL(r.Config.APIBaseURL)
	if err != nil {
		return err
	}
	headers := http.Header{"Authorization": []string{"Bearer " + r.API.credential}}
	conn, _, err := websocket.Dial(ctx, wsURL, &websocket.DialOptions{HTTPHeader: headers})
	if err != nil {
		return err
	}
	defer conn.Close(websocket.StatusNormalClosure, "closed")
	if err := writeMessage(ctx, conn, "hello", "hello", helloPayload(r)); err != nil {
		return err
	}
	heartbeatTicker := time.NewTicker(time.Duration(r.Config.IntervalSeconds) * time.Second)
	defer heartbeatTicker.Stop()
	for {
		readTimeout := time.Duration(r.Config.IntervalSeconds+r.Config.TimeoutSeconds) * time.Second
		readCtx, cancel := context.WithTimeout(ctx, readTimeout)
		_, data, err := conn.Read(readCtx)
		cancel()
		if err != nil {
			select {
			case <-heartbeatTicker.C:
				if writeErr := writeMessage(ctx, conn, "heartbeat", "heartbeat", helloPayload(r)); writeErr != nil {
					return writeErr
				}
				continue
			default:
				return err
			}
		}
		var message ProtocolMessage
		if err := json.Unmarshal(data, &message); err != nil {
			return err
		}
		if message.ProtocolVersion != ProtocolVersion {
			return fmt.Errorf("protocol version incompatible: %d", message.ProtocolVersion)
		}
		if message.MessageType == "job" {
			job := AgentJob{
				ID:            intNumber(message.Payload["job_id"]),
				CorrelationID: stringValue(message.Payload["correlation_id"]),
				JobType:       stringValue(message.Payload["job_type"]),
				Payload:       mapValue(message.Payload["payload"]),
				Attempts:      intNumber(message.Payload["attempts"]),
			}
			r.handleJob(ctx, job)
		}
	}
}

func (r *Runner) handleJob(ctx context.Context, job AgentJob) {
	if err := r.API.AckJob(ctx, job.ID); err != nil {
		r.Logger.Printf("job ack failed id=%d: %v", job.ID, err)
		return
	}
	switch job.JobType {
	case "ping":
		_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: map[string]any{"pong": true, "agent_version": Version}})
	case "snapshot":
		snapshot := r.Moonraker.Snapshot(ctx)
		_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: compactSnapshot(snapshot)})
	case "remote_audit", "remote_snapshot", "remote_health", "remote_temperatures", "remote_update_status", "remote_can_status", "remote_final_validation", "remote_report_sanitized", "remote_backup_preview", "remote_operation_preview", "remote_firmware_preview":
		payload := r.Moonraker.RemotePayload(ctx, job.JobType)
		_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
	case "remote_mutation_preflight":
		payload := r.Moonraker.RemoteMutationPreflight(ctx, job.Payload)
		_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
	case "remote_mutation_execute":
		payload := r.Moonraker.RemoteMutationExecute(ctx, job.Payload)
		if payload["status"] == "executed" {
			_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
		} else {
			_ = r.API.ErrorJob(ctx, job.ID, AgentJobErrorPayload{CorrelationID: job.CorrelationID, ErrorMessage: stringValue(payload["detail"]), Result: mapValueOrEmpty(payload)})
		}
	case "remote_doctor":
		payload := RemoteDoctor(ctx, r.Config, r.API, r.Moonraker)
		_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
	default:
		_ = r.API.ErrorJob(ctx, job.ID, AgentJobErrorPayload{CorrelationID: job.CorrelationID, ErrorMessage: "unsupported job type", Result: map[string]any{"job_type": job.JobType}})
	}
}

func websocketURL(base string) (string, error) {
	parsed, err := url.Parse(base)
	if err != nil {
		return "", err
	}
	switch parsed.Scheme {
	case "https":
		parsed.Scheme = "wss"
	case "http":
		parsed.Scheme = "ws"
	default:
		return "", fmt.Errorf("unsupported api scheme %q", parsed.Scheme)
	}
	parsed.Path = "/api/agent/ws"
	parsed.RawQuery = ""
	return parsed.String(), nil
}

func writeMessage(ctx context.Context, conn *websocket.Conn, messageType string, correlationID string, payload map[string]any) error {
	data, err := json.Marshal(ProtocolMessage{ProtocolVersion: ProtocolVersion, MessageType: messageType, CorrelationID: correlationID, Payload: payload})
	if err != nil {
		return err
	}
	return conn.Write(ctx, websocket.MessageText, data)
}

func helloPayload(r *Runner) map[string]any {
	return map[string]any{
		"agent_version": Version,
		"platform":      Platform(),
		"capabilities": map[string]any{
			"heartbeat":  true,
			"snapshot":   true,
			"mutation":   true,
			"doctor":     true,
			"parity":     true,
			"jobs":       true,
			"websocket":  true,
			"polling":    r.Config.PollingEnabled,
			"read_only":  true,
			"protocol_v": ProtocolVersion,
		},
	}
}

func stringValue(value any) string {
	if text, ok := value.(string); ok {
		return text
	}
	return ""
}

func intNumber(value any) int {
	switch typed := value.(type) {
	case float64:
		return int(typed)
	case int:
		return typed
	default:
		return 0
	}
}

func mapValue(value any) map[string]any {
	if mapped, ok := value.(map[string]any); ok {
		return mapped
	}
	return map[string]any{}
}

func mapValueOrEmpty(value any) map[string]any {
	if mapped, ok := value.(map[string]any); ok {
		return mapped
	}
	return map[string]any{"value": value}
}

func discardLogger() *log.Logger {
	return log.New(ioDiscard{}, "", 0)
}

type ioDiscard struct{}

func (ioDiscard) Write(p []byte) (int, error) {
	return len(p), nil
}
