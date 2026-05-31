package agent

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"time"
)

const Version = "0.1.0"

type Config struct {
	APIBaseURL      string `json:"api_base_url"`
	MoonrakerURL    string `json:"moonraker_url"`
	CredentialFile  string `json:"credential_file"`
	QueueFile       string `json:"queue_file"`
	LogFile         string `json:"log_file"`
	IntervalSeconds int    `json:"interval_seconds"`
	TimeoutSeconds  int    `json:"timeout_seconds"`
}

func DefaultConfig() Config {
	home, _ := os.UserHomeDir()
	base := filepath.Join(home, ".config", "printora-agent")
	return Config{
		APIBaseURL:      "https://printora.example.com",
		MoonrakerURL:    "http://127.0.0.1:7125",
		CredentialFile:  filepath.Join(base, "credential"),
		QueueFile:       filepath.Join(base, "queue.jsonl"),
		LogFile:         filepath.Join(base, "agent.log"),
		IntervalSeconds: 10,
		TimeoutSeconds:  5,
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
