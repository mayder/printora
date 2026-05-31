package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"

	"github.com/mayder/printora/agent/internal/agent"
)

func main() {
	configPath := flag.String("config", defaultConfigPath(), "caminho do config JSON")
	flag.Parse()
	command := "run"
	if flag.NArg() > 0 {
		command = flag.Arg(0)
	}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	switch command {
	case "config-sample":
		must(agent.WriteSampleConfig(*configPath))
		fmt.Println(*configPath)
	case "store-credential":
		must(storeCredential(*configPath, os.Stdin))
	case "doctor":
		for _, result := range agent.Doctor(ctx, *configPath) {
			fmt.Printf("%-18s %-5s %s\n", result.Name, result.Status, result.Detail)
		}
	case "once":
		must(runOnce(ctx, *configPath))
	case "run":
		must(run(ctx, *configPath))
	case "systemd":
		fmt.Print(systemdUnit())
	default:
		fmt.Fprintf(os.Stderr, "uso: printora-agent [-config path] [run|once|doctor|config-sample|store-credential|systemd]\n")
		os.Exit(2)
	}
}

func storeCredential(configPath string, input io.Reader) error {
	cfg, err := agent.LoadConfig(configPath)
	if err != nil {
		return err
	}
	data, err := io.ReadAll(input)
	if err != nil {
		return err
	}
	credential := agent.TrimSpaceForCLI(string(data))
	if credential == "" {
		return fmt.Errorf("credencial vazia")
	}
	if err := os.MkdirAll(filepath.Dir(cfg.CredentialFile), 0o700); err != nil {
		return err
	}
	return os.WriteFile(cfg.CredentialFile, []byte(credential+"\n"), 0o600)
}

func runOnce(ctx context.Context, configPath string) error {
	runner, closer, err := buildRunner(configPath)
	if err != nil {
		return err
	}
	defer closer()
	return runner.RunOnce(ctx)
}

func run(ctx context.Context, configPath string) error {
	runner, closer, err := buildRunner(configPath)
	if err != nil {
		return err
	}
	defer closer()
	return runner.Run(ctx)
}

func buildRunner(configPath string) (*agent.Runner, func(), error) {
	cfg, err := agent.LoadConfig(configPath)
	if err != nil {
		return nil, nil, err
	}
	credential, err := agent.ReadCredential(cfg.CredentialFile)
	if err != nil {
		return nil, nil, err
	}
	logger, closer, err := agent.NewLogger(cfg.LogFile)
	if err != nil {
		return nil, nil, err
	}
	return agent.NewRunner(cfg, credential, logger), func() { _ = closer.Close() }, nil
}

func must(err error) {
	if err == nil {
		return
	}
	fmt.Fprintln(os.Stderr, err)
	os.Exit(1)
}

func defaultConfigPath() string {
	if os.Geteuid() == 0 {
		return "/etc/printora-agent/config.json"
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return "printora-agent.json"
	}
	return filepath.Join(home, ".config", "printora-agent", "config.json")
}

func systemdUnit() string {
	return `[Unit]
Description=Printora Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/printora-agent -config /etc/printora-agent/config.json run
Restart=always
RestartSec=5
User=printora-agent
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
`
}
