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

const (
	minReconnectBackoff = time.Second
	maxReconnectBackoff = time.Minute
)

type ProtocolMessage struct {
	ProtocolVersion int            `json:"protocol_version"`
	MessageType     string         `json:"message_type"`
	CorrelationID   string         `json:"correlation_id"`
	Payload         map[string]any `json:"payload"`
}

func (r *Runner) RunChannel(ctx context.Context) error {
	backoff := minReconnectBackoff
	for {
		connected, err := r.runWebSocket(ctx)
		if err != nil {
			if ctx.Err() != nil {
				return ctx.Err()
			}
			r.Logger.Printf("websocket unavailable, fallback polling: %v", err)
			r.runReconnectFallback(ctx, backoff)
			if connected {
				backoff = minReconnectBackoff
				continue
			}
		}
		backoff = nextReconnectBackoff(backoff)
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

func (r *Runner) runReconnectFallback(ctx context.Context, duration time.Duration) {
	if duration <= 0 {
		duration = minReconnectBackoff
	}
	deadline := time.NewTimer(duration)
	defer deadline.Stop()
	ticker := time.NewTicker(r.loopInterval())
	defer ticker.Stop()
	for {
		r.runFallbackCycle(ctx)
		select {
		case <-ctx.Done():
			return
		case <-deadline.C:
			return
		case <-ticker.C:
		}
	}
}

func (r *Runner) runFallbackCycle(ctx context.Context) {
	if err := r.RunOnce(ctx); err != nil {
		r.Logger.Printf("heartbeat fallback failed: %v", err)
	}
	if r.Config.PollingEnabled {
		if pollErr := r.PollJobsOnce(ctx); pollErr != nil {
			r.Logger.Printf("polling fallback failed: %v", pollErr)
		}
	}
}

func (r *Runner) loopInterval() time.Duration {
	seconds := r.Config.IntervalSeconds
	if seconds <= 0 {
		seconds = DefaultConfig().IntervalSeconds
	}
	return time.Duration(seconds) * time.Second
}

func (r *Runner) operationTimeout() time.Duration {
	timeout := Timeout(r.Config)
	if timeout <= 0 {
		timeout = Timeout(DefaultConfig())
	}
	return timeout
}

func nextReconnectBackoff(current time.Duration) time.Duration {
	if current <= 0 {
		return minReconnectBackoff
	}
	next := current * 2
	if next > maxReconnectBackoff {
		return maxReconnectBackoff
	}
	return next
}

func (r *Runner) runWebSocket(ctx context.Context) (bool, error) {
	wsURL, err := websocketURL(r.Config.APIBaseURL)
	if err != nil {
		return false, err
	}
	headers := http.Header{"Authorization": []string{"Bearer " + r.API.credential}}
	dialCtx, cancelDial := context.WithTimeout(ctx, r.operationTimeout())
	conn, _, err := websocket.Dial(dialCtx, wsURL, &websocket.DialOptions{HTTPHeader: headers})
	cancelDial()
	if err != nil {
		return false, err
	}
	defer conn.Close(websocket.StatusNormalClosure, "closed")
	helloCtx, cancelHello := context.WithTimeout(ctx, r.operationTimeout())
	err = writeMessage(helloCtx, conn, "hello", "hello", helloPayload(r))
	cancelHello()
	if err != nil {
		return false, err
	}
	connected := true
	heartbeatInterval := r.loopInterval()
	heartbeatCtx, stopHeartbeat := context.WithCancel(ctx)
	defer stopHeartbeat()
	heartbeatErrors := make(chan error, 1)
	go func() {
		ticker := time.NewTicker(heartbeatInterval)
		defer ticker.Stop()
		for {
			select {
			case <-heartbeatCtx.Done():
				return
			case <-ticker.C:
				writeCtx, cancelWrite := context.WithTimeout(heartbeatCtx, r.operationTimeout())
				err := writeMessage(writeCtx, conn, "heartbeat", "heartbeat", helloPayload(r))
				cancelWrite()
				if err != nil {
					select {
					case heartbeatErrors <- err:
					default:
					}
					_ = conn.Close(websocket.StatusInternalError, "heartbeat failed")
					return
				}
			}
		}
	}()
	for {
		select {
		case err := <-heartbeatErrors:
			return connected, err
		default:
		}
		_, data, err := conn.Read(ctx)
		if err != nil {
			select {
			case heartbeatErr := <-heartbeatErrors:
				return connected, heartbeatErr
			default:
				return connected, err
			}
		}
		var message ProtocolMessage
		if err := json.Unmarshal(data, &message); err != nil {
			return connected, err
		}
		if message.ProtocolVersion != ProtocolVersion {
			return connected, fmt.Errorf("protocol version incompatible: %d", message.ProtocolVersion)
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
	case "remote_audit", "remote_snapshot", "remote_health", "remote_temperatures", "remote_update_status", "remote_can_status", "remote_final_validation", "remote_report_sanitized", "remote_backup_preview", "remote_operation_preview", "remote_firmware_preview", "remote_moonraker_status", "remote_operation_status", "remote_calibration_capabilities", "remote_firmware_inventory":
		payload := r.Moonraker.RemotePayload(ctx, job.JobType)
		_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
	case "remote_update_action":
		payload := r.Moonraker.RemoteUpdateAction(ctx, job.Payload)
		if payload["status"] == "accepted" {
			_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
		} else {
			_ = r.API.ErrorJob(ctx, job.ID, AgentJobErrorPayload{CorrelationID: job.CorrelationID, ErrorMessage: stringValue(payload["moonraker_response_error"]), Result: mapValueOrEmpty(payload)})
		}
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
	case "remote_gcode_preflight":
		payload := r.Moonraker.RemoteGcodePreflight(ctx, job.Payload)
		_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
	case "remote_gcode_execute":
		payload := r.Moonraker.RemoteGcodeExecute(ctx, job.Payload)
		if payload["status"] == "executed" {
			_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
		} else {
			_ = r.API.ErrorJob(ctx, job.ID, AgentJobErrorPayload{CorrelationID: job.CorrelationID, ErrorMessage: stringValue(payload["detail"]), Result: mapValueOrEmpty(payload)})
		}
	case "remote_host_script":
		payload := RemoteHostScript(ctx, job.Payload)
		if payload["status"] == "ok" {
			_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
		} else {
			_ = r.API.ErrorJob(ctx, job.ID, AgentJobErrorPayload{CorrelationID: job.CorrelationID, ErrorMessage: stringValue(payload["error"]), Result: mapValueOrEmpty(payload)})
		}
	case "remote_doctor":
		payload := RemoteDoctor(ctx, r.Config, r.API, r.Moonraker)
		_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: mapValueOrEmpty(payload)})
	case "remote_agent_update_check":
		result := r.CheckAgentUpdate(ctx)
		r.RecordUpdateResult(ctx, result)
		payload := map[string]any{
			"safe_mode":       "agent_self_update",
			"status":          result.Status,
			"current_version": Version,
			"target_version":  result.TargetVersion,
			"detail":          result.Detail,
		}
		_ = r.API.ResultJob(ctx, job.ID, AgentJobResultPayload{CorrelationID: job.CorrelationID, Result: payload})
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
			"heartbeat":   true,
			"snapshot":    true,
			"mutation":    true,
			"doctor":      true,
			"parity":      true,
			"updates":     true,
			"gcode_jobs":  true,
			"host_script": true,
			"jobs":        true,
			"websocket":   true,
			"polling":     r.Config.PollingEnabled,
			"read_only":   true,
			"protocol_v":  ProtocolVersion,
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
