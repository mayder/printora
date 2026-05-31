package agent

import (
	"context"
	"fmt"
	"os"
	"runtime"
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
