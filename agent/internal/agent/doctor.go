package agent

import (
	"context"
	"fmt"
	"os"
	"runtime"
	"strings"
)

type DoctorResult struct {
	Name   string
	Status string
	Detail string
}

func Doctor(ctx context.Context, configPath string) []DoctorResult {
	var results []DoctorResult
	cfg, err := LoadConfig(configPath)
	if err != nil {
		return append(results, DoctorResult{"config", "fail", err.Error()})
	}
	results = append(results, DoctorResult{"config", "ok", configPath})
	if runtime.GOOS != "windows" {
		if info, err := os.Stat(configPath); err != nil {
			results = append(results, DoctorResult{"config_permission", "fail", err.Error()})
		} else if info.Mode().Perm()&0o077 != 0 {
			results = append(results, DoctorResult{"config_permission", "warn", fmt.Sprintf("permissão %s, recomendado 0600", info.Mode().Perm())})
		} else {
			results = append(results, DoctorResult{"config_permission", "ok", info.Mode().Perm().String()})
		}
	}
	credential, err := ReadCredential(cfg.CredentialFile)
	if err != nil {
		results = append(results, DoctorResult{"credential", "fail", err.Error()})
		return results
	}
	results = append(results, DoctorResult{"credential", "ok", "arquivo válido e restrito"})
	if err := NewMoonrakerClient(cfg.MoonrakerURL, Timeout(cfg)).Doctor(ctx); err != nil {
		results = append(results, DoctorResult{"moonraker", "fail", err.Error()})
	} else {
		results = append(results, DoctorResult{"moonraker", "ok", cfg.MoonrakerURL})
	}
	if err := NewAPIClient(cfg.APIBaseURL, credential, Timeout(cfg)).Doctor(ctx); err != nil {
		results = append(results, DoctorResult{"api", "fail", err.Error()})
	} else {
		results = append(results, DoctorResult{"api", "ok", cfg.APIBaseURL})
	}
	return results
}

func RemoteDoctor(ctx context.Context, cfg Config, api *APIClient, moonraker *MoonrakerClient) map[string]any {
	results := []map[string]any{
		{"name": "agent_version", "status": "ok", "detail": Version},
		{"name": "platform", "status": "ok", "detail": Platform()},
		{"name": "protocol", "status": "ok", "detail": ProtocolVersion},
	}
	if cfg.configPath != "" {
		if info, err := os.Stat(cfg.configPath); err != nil {
			results = append(results, map[string]any{"name": "config", "status": "fail", "detail": err.Error()})
		} else if runtime.GOOS != "windows" && info.Mode().Perm()&0o077 != 0 {
			results = append(results, map[string]any{"name": "config_permission", "status": "warn", "detail": fmt.Sprintf("permissão %s, recomendado 0600", info.Mode().Perm())})
		} else {
			results = append(results, map[string]any{"name": "config", "status": "ok", "detail": "configuração acessível"})
		}
	}
	if _, err := ReadCredential(cfg.CredentialFile); err != nil {
		results = append(results, map[string]any{"name": "credential", "status": "fail", "detail": err.Error()})
	} else {
		results = append(results, map[string]any{"name": "credential", "status": "ok", "detail": "arquivo válido e restrito"})
	}
	if err := moonraker.Doctor(ctx); err != nil {
		results = append(results, map[string]any{"name": "moonraker", "status": "fail", "detail": err.Error()})
	} else {
		results = append(results, map[string]any{"name": "moonraker", "status": "ok", "detail": cfg.MoonrakerURL})
	}
	if err := api.Doctor(ctx); err != nil {
		results = append(results, map[string]any{"name": "api", "status": "fail", "detail": err.Error()})
	} else {
		results = append(results, map[string]any{"name": "api", "status": "ok", "detail": cfg.APIBaseURL})
	}
	results = append(results, map[string]any{"name": "queue", "status": "ok", "detail": fileSummary(cfg.QueueFile)})
	results = append(results, map[string]any{"name": "log", "status": "ok", "detail": fileSummary(cfg.LogFile)})
	return sanitizeMap(map[string]any{
		"safe_mode":     "support_diagnostics",
		"kind":          "remote_doctor",
		"agent_version": Version,
		"platform":      Platform(),
		"protocol_v":    ProtocolVersion,
		"checks":        results,
		"log_tail":      sanitizedTail(cfg.LogFile, 8),
	})
}

func fileSummary(path string) string {
	if path == "" {
		return "não configurado"
	}
	info, err := os.Stat(path)
	if err != nil {
		return err.Error()
	}
	return fmt.Sprintf("%d bytes", info.Size())
}

func sanitizedTail(path string, maxLines int) []string {
	if path == "" || maxLines <= 0 {
		return nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil
	}
	lines := strings.Split(string(data), "\n")
	start := len(lines) - maxLines
	if start < 0 {
		start = 0
	}
	result := make([]string, 0, maxLines)
	for _, line := range lines[start:] {
		line = strings.TrimSpace(line)
		if line != "" {
			result = append(result, redactSecretText(line))
		}
	}
	return result
}
