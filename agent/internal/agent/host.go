package agent

import (
	"bytes"
	"context"
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"time"
)

const maxHostScriptOutputBytes = 48 * 1024

func RemoteHostScript(ctx context.Context, payload map[string]any) map[string]any {
	script := stringValue(payload["script"])
	if strings.TrimSpace(script) == "" {
		return map[string]any{
			"safe_mode": "agent_host_script",
			"status":    "blocked",
			"error":     "script vazio",
			"exit_code": nil,
		}
	}
	timeoutSeconds := intNumber(payload["timeout_seconds"])
	if timeoutSeconds <= 0 {
		timeoutSeconds = 30
	}
	if timeoutSeconds > 1200 {
		timeoutSeconds = 1200
	}
	runCtx, cancel := context.WithTimeout(ctx, time.Duration(timeoutSeconds)*time.Second)
	defer cancel()

	command := exec.CommandContext(runCtx, "bash", "-s")
	command.Stdin = strings.NewReader(script)
	command.Env = append(os.Environ(), hostScriptEnv(payload)...)
	var stdout bytes.Buffer
	var stderr bytes.Buffer
	command.Stdout = limitWriter{Buffer: &stdout, Max: maxHostScriptOutputBytes}
	command.Stderr = limitWriter{Buffer: &stderr, Max: maxHostScriptOutputBytes}

	err := command.Run()
	exitCode := 0
	errorMessage := ""
	if err != nil {
		exitCode = 1
		errorMessage = err.Error()
		if exitErr, ok := err.(*exec.ExitError); ok {
			exitCode = exitErr.ExitCode()
		}
	}
	if runCtx.Err() == context.DeadlineExceeded {
		errorMessage = fmt.Sprintf("timeout do agente após %ds", timeoutSeconds)
	}
	status := "ok"
	if errorMessage != "" || exitCode != 0 {
		status = "error"
	}
	return sanitizeMap(map[string]any{
		"safe_mode":       "agent_host_script",
		"kind":            stringValue(payload["kind"]),
		"status":          status,
		"stdout":          stdout.String(),
		"stderr":          stderr.String(),
		"exit_code":       exitCode,
		"error":           errorMessage,
		"timeout_seconds": timeoutSeconds,
	})
}

func hostScriptEnv(payload map[string]any) []string {
	values := []string{"PRINTORA_AGENT_EXECUTION=1"}
	env, ok := payload["env"].(map[string]any)
	if !ok {
		return values
	}
	for key, value := range env {
		cleanKey := strings.TrimSpace(key)
		if cleanKey == "" || strings.ContainsAny(cleanKey, "=\x00") {
			continue
		}
		values = append(values, cleanKey+"="+envString(value))
	}
	return values
}

func envString(value any) string {
	switch typed := value.(type) {
	case string:
		return typed
	case float64:
		return strconv.FormatFloat(typed, 'f', -1, 64)
	case bool:
		if typed {
			return "1"
		}
		return "0"
	default:
		return fmt.Sprintf("%v", typed)
	}
}

type limitWriter struct {
	*bytes.Buffer
	Max int
}

func (w limitWriter) Write(p []byte) (int, error) {
	originalLength := len(p)
	if w.Buffer.Len() >= w.Max {
		return originalLength, nil
	}
	remaining := w.Max - w.Buffer.Len()
	if len(p) > remaining {
		p = p[:remaining]
	}
	_, _ = w.Buffer.Write(p)
	return originalLength, nil
}
