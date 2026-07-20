package agent

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

const Version = "0.1.33"
const ProtocolVersion = 1

type Config struct {
	APIBaseURL                 string   `json:"api_base_url"`
	MoonrakerURL               string   `json:"moonraker_url"`
	CredentialFile             string   `json:"credential_file"`
	QueueFile                  string   `json:"queue_file"`
	LogFile                    string   `json:"log_file"`
	IntervalSeconds            int      `json:"interval_seconds"`
	TimeoutSeconds             int      `json:"timeout_seconds"`
	WebSocketEnabled           bool     `json:"websocket_enabled"`
	PollingEnabled             bool     `json:"polling_enabled"`
	MaxPayloadBytes            int      `json:"max_payload_bytes"`
	UpdateEnabled              bool     `json:"update_enabled"`
	UpdateCheckIntervalSeconds int      `json:"update_check_interval_seconds"`
	UpdateManifestURL          string   `json:"update_manifest_url"`
	UpdateStateFile            string   `json:"update_state_file"`
	UpdateStagingDir           string   `json:"update_staging_dir"`
	AgentBinaryPath            string   `json:"agent_binary_path"`
	AgentServiceName           string   `json:"agent_service_name"`
	AllowServiceRestart        bool     `json:"allow_service_restart"`
	UpdateHealthCommand        []string `json:"update_health_command"`
	configPath                 string
}

func DefaultConfig() Config {
	home, _ := os.UserHomeDir()
	base := filepath.Join(home, ".config", "printora-agent")
	return Config{
		APIBaseURL:                 "https://printora.example.com",
		MoonrakerURL:               "http://127.0.0.1:7125",
		CredentialFile:             filepath.Join(base, "credential"),
		QueueFile:                  filepath.Join(base, "queue.jsonl"),
		LogFile:                    filepath.Join(base, "agent.log"),
		IntervalSeconds:            10,
		TimeoutSeconds:             5,
		WebSocketEnabled:           true,
		PollingEnabled:             true,
		MaxPayloadBytes:            64 * 1024,
		UpdateEnabled:              true,
		UpdateCheckIntervalSeconds: 3600,
		UpdateManifestURL:          "",
		UpdateStateFile:            filepath.Join(base, "update-state.json"),
		UpdateStagingDir:           filepath.Join(base, "updates"),
		AgentBinaryPath:            "",
		AgentServiceName:           "printora-agent",
		AllowServiceRestart:        false,
	}
}

func LoadConfig(path string) (Config, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("config: %w", err)
	}
	cfg := DefaultConfig()
	if err := json.Unmarshal(data, &cfg); err != nil {
		return Config{}, fmt.Errorf("config json: %w", err)
	}
	cfg.configPath = path
	if cfg.APIBaseURL == "" {
		return Config{}, errors.New("config: api_base_url obrigatório")
	}
	if cfg.MoonrakerURL == "" {
		return Config{}, errors.New("config: moonraker_url obrigatório")
	}
	if cfg.CredentialFile == "" {
		return Config{}, errors.New("config: credential_file obrigatório")
	}
	if cfg.IntervalSeconds <= 0 {
		cfg.IntervalSeconds = 10
	}
	if cfg.TimeoutSeconds <= 0 {
		cfg.TimeoutSeconds = 5
	}
	if cfg.MaxPayloadBytes <= 0 {
		cfg.MaxPayloadBytes = 64 * 1024
	}
	if cfg.UpdateCheckIntervalSeconds <= 0 {
		cfg.UpdateCheckIntervalSeconds = 3600
	}
	if cfg.UpdateManifestURL == "" {
		cfg.UpdateManifestURL = strings.TrimRight(cfg.APIBaseURL, "/") + "/api/agent/update/manifest"
	}
	if cfg.UpdateStateFile == "" {
		cfg.UpdateStateFile = filepath.Join(filepath.Dir(cfg.QueueFile), "update-state.json")
	}
	if cfg.UpdateStagingDir == "" {
		cfg.UpdateStagingDir = filepath.Join(filepath.Dir(cfg.QueueFile), "updates")
	}
	if cfg.AgentServiceName == "" {
		cfg.AgentServiceName = "printora-agent"
	}
	return cfg, nil
}

func WriteSampleConfig(path string) error {
	cfg := DefaultConfig()
	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o600)
}

func ReadCredential(path string) (string, error) {
	info, err := os.Stat(path)
	if err != nil {
		return "", fmt.Errorf("credential: %w", err)
	}
	if runtime.GOOS != "windows" && info.Mode().Perm()&0o077 != 0 {
		return "", fmt.Errorf("credential: permissões inseguras %s, esperado 0600", info.Mode().Perm())
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("credential: %w", err)
	}
	credential := trimSpace(string(data))
	if credential == "" {
		return "", errors.New("credential: vazio")
	}
	return credential, nil
}

func Platform() string {
	return runtime.GOOS + "/" + runtime.GOARCH
}

func Timeout(cfg Config) time.Duration {
	return time.Duration(cfg.TimeoutSeconds) * time.Second
}

func trimSpace(value string) string {
	for len(value) > 0 {
		switch value[0] {
		case ' ', '\n', '\r', '\t':
			value = value[1:]
		default:
			goto right
		}
	}
right:
	for len(value) > 0 {
		switch value[len(value)-1] {
		case ' ', '\n', '\r', '\t':
			value = value[:len(value)-1]
		default:
			return value
		}
	}
	return value
}

func TrimSpaceForCLI(value string) string {
	return trimSpace(value)
}
