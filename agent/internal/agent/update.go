package agent

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"
)

type UpdateManifest struct {
	ManifestVersion    int             `json:"manifest_version"`
	MinimumVersion     string          `json:"minimum_version"`
	RecommendedVersion string          `json:"recommended_version"`
	BlockedVersions    []string        `json:"blocked_versions"`
	ProtocolVersion    int             `json:"protocol_version"`
	ProtocolMin        int             `json:"protocol_min"`
	ProtocolMax        int             `json:"protocol_max"`
	AutoUpdate         bool            `json:"auto_update"`
	Releases           []UpdateRelease `json:"releases"`
}

type UpdateRelease struct {
	Platform    string `json:"platform"`
	Version     string `json:"version"`
	URL         string `json:"url"`
	SHA256      string `json:"sha256"`
	Signature   string `json:"signature"`
	ProtocolMin int    `json:"protocol_min"`
	ProtocolMax int    `json:"protocol_max"`
}

type UpdateState struct {
	LastCheckAt    string `json:"last_check_at"`
	LastStatus     string `json:"last_status"`
	CurrentVersion string `json:"current_version"`
	TargetVersion  string `json:"target_version,omitempty"`
	Detail         string `json:"detail,omitempty"`
}

type UpdateResult struct {
	Status        string
	TargetVersion string
	Detail        string
}

func (r *Runner) MaybeCheckAgentUpdate(ctx context.Context) {
	if !r.Config.UpdateEnabled {
		return
	}
	state, _ := loadUpdateState(r.Config.UpdateStateFile)
	if !shouldCheckUpdate(state, r.Config.UpdateCheckIntervalSeconds) {
		return
	}
	result := r.CheckAgentUpdate(ctx)
	r.RecordUpdateResult(ctx, result)
}

func (r *Runner) RecordUpdateResult(ctx context.Context, result UpdateResult) {
	_ = r.API.UpdateReport(ctx, AgentUpdateReportPayload{
		Status:         result.Status,
		CurrentVersion: Version,
		TargetVersion:  result.TargetVersion,
		Platform:       Platform(),
		Detail:         result.Detail,
	})
	_ = saveUpdateState(r.Config.UpdateStateFile, UpdateState{
		LastCheckAt:    time.Now().UTC().Format(time.RFC3339),
		LastStatus:     result.Status,
		CurrentVersion: Version,
		TargetVersion:  result.TargetVersion,
		Detail:         result.Detail,
	})
}

func (r *Runner) CheckAgentUpdate(ctx context.Context) UpdateResult {
	manifest, err := fetchUpdateManifest(ctx, r.Config)
	if err != nil {
		return UpdateResult{Status: "failed", Detail: err.Error()}
	}
	release, result := selectUpdateRelease(manifest, Platform(), Version)
	if result.Status != "available" {
		return result
	}
	if !manifest.AutoUpdate {
		result.Status = "skipped"
		result.Detail = "auto_update desabilitado no manifesto"
		return result
	}
	if release.URL == "" {
		return UpdateResult{Status: "skipped", TargetVersion: release.Version, Detail: "release sem URL de download"}
	}
	stagedPath, err := downloadRelease(ctx, r.Config, release)
	if err != nil {
		return UpdateResult{Status: "failed", TargetVersion: release.Version, Detail: err.Error()}
	}
	if err := applyRelease(r.Config, stagedPath, release.Version); err != nil {
		return UpdateResult{Status: "rolled_back", TargetVersion: release.Version, Detail: err.Error()}
	}
	return UpdateResult{Status: "applied", TargetVersion: release.Version, Detail: "binário do agente atualizado"}
}

func fetchUpdateManifest(ctx context.Context, cfg Config) (UpdateManifest, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, cfg.UpdateManifestURL, nil)
	if err != nil {
		return UpdateManifest{}, err
	}
	client := &http.Client{Timeout: Timeout(cfg)}
	resp, err := client.Do(req)
	if err != nil {
		return UpdateManifest{}, err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return UpdateManifest{}, fmt.Errorf("manifest status %d", resp.StatusCode)
	}
	var manifest UpdateManifest
	if err := json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&manifest); err != nil {
		return UpdateManifest{}, err
	}
	return manifest, nil
}

func selectUpdateRelease(manifest UpdateManifest, platform string, currentVersion string) (UpdateRelease, UpdateResult) {
	for _, blocked := range manifest.BlockedVersions {
		if normalizeVersion(blocked) == normalizeVersion(currentVersion) {
			return UpdateRelease{}, UpdateResult{Status: "blocked", Detail: "versão atual bloqueada pelo servidor"}
		}
	}
	if ProtocolVersion < manifest.ProtocolMin || ProtocolVersion > manifest.ProtocolMax {
		return UpdateRelease{}, UpdateResult{Status: "blocked", Detail: "protocolo incompatível com manifesto"}
	}
	for _, release := range manifest.Releases {
		if release.Platform != platform {
			continue
		}
		if ProtocolVersion < release.ProtocolMin || ProtocolVersion > release.ProtocolMax {
			return release, UpdateResult{Status: "blocked", TargetVersion: release.Version, Detail: "protocolo incompatível com release"}
		}
		if compareVersion(release.Version, currentVersion) <= 0 {
			return release, UpdateResult{Status: "skipped", TargetVersion: release.Version, Detail: "agente já está atualizado"}
		}
		return release, UpdateResult{Status: "available", TargetVersion: release.Version, Detail: "update disponível"}
	}
	return UpdateRelease{}, UpdateResult{Status: "skipped", Detail: "sem release para " + platform}
}

func downloadRelease(ctx context.Context, cfg Config, release UpdateRelease) (string, error) {
	if release.SHA256 == "" {
		return "", errors.New("release sem sha256")
	}
	if err := os.MkdirAll(cfg.UpdateStagingDir, 0o700); err != nil {
		return "", err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, release.URL, nil)
	if err != nil {
		return "", err
	}
	client := &http.Client{Timeout: updateDownloadTimeout(cfg)}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", fmt.Errorf("download status %d", resp.StatusCode)
	}
	stagedPath := filepath.Join(cfg.UpdateStagingDir, "printora-agent-"+safeFilePart(release.Version))
	file, err := os.OpenFile(stagedPath, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o700)
	if err != nil {
		return "", err
	}
	hasher := sha256.New()
	if _, err := io.Copy(io.MultiWriter(file, hasher), io.LimitReader(resp.Body, 128<<20)); err != nil {
		_ = file.Close()
		return "", err
	}
	if err := file.Close(); err != nil {
		return "", err
	}
	actual := hex.EncodeToString(hasher.Sum(nil))
	if !strings.EqualFold(actual, release.SHA256) {
		return "", fmt.Errorf("sha256 inválido: esperado %s, recebido %s", release.SHA256, actual)
	}
	return stagedPath, nil
}

func updateDownloadTimeout(cfg Config) time.Duration {
	timeout := Timeout(cfg)
	if timeout < 60*time.Second {
		return 60 * time.Second
	}
	return timeout
}

func applyRelease(cfg Config, stagedPath string, targetVersion string) error {
	binaryPath, err := currentBinaryPath(cfg)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(cfg.UpdateStagingDir, 0o700); err != nil {
		return err
	}
	backupPath := filepath.Join(cfg.UpdateStagingDir, "printora-agent.backup-"+safeFilePart(Version))
	if err := copyFile(binaryPath, backupPath, 0o700); err != nil {
		return fmt.Errorf("backup binário: %w", err)
	}
	if cfg.configPath != "" {
		_ = copyFile(cfg.configPath, filepath.Join(cfg.UpdateStagingDir, "config.backup-"+safeFilePart(time.Now().UTC().Format("20060102T150405Z"))+".json"), 0o600)
	}
	if err := replaceExecutable(stagedPath, binaryPath); err != nil {
		return fmt.Errorf("troca binário: %w", err)
	}
	if err := runUpdateHealthCommand(cfg); err != nil {
		_ = copyFile(backupPath, binaryPath, 0o755)
		return fmt.Errorf("health pós-update falhou, rollback aplicado: %w", err)
	}
	if cfg.AllowServiceRestart {
		if err := restartAgentService(cfg.AgentServiceName); err != nil {
			_ = copyFile(backupPath, binaryPath, 0o755)
			return fmt.Errorf("restart do agente falhou, rollback aplicado: %w", err)
		}
	}
	_ = targetVersion
	return nil
}

func runUpdateHealthCommand(cfg Config) error {
	if len(cfg.UpdateHealthCommand) == 0 {
		return nil
	}
	command := exec.Command(cfg.UpdateHealthCommand[0], cfg.UpdateHealthCommand[1:]...)
	return command.Run()
}

func restartAgentService(serviceName string) error {
	if runtime.GOOS == "windows" {
		return errors.New("restart automático do serviço não suportado no Windows")
	}
	if serviceName == "" {
		serviceName = "printora-agent"
	}
	return exec.Command("systemctl", "restart", serviceName).Run()
}

func currentBinaryPath(cfg Config) (string, error) {
	if cfg.AgentBinaryPath != "" {
		return cfg.AgentBinaryPath, nil
	}
	return os.Executable()
}

func copyFile(source string, target string, mode os.FileMode) error {
	input, err := os.Open(source)
	if err != nil {
		return err
	}
	defer input.Close()
	if err := os.MkdirAll(filepath.Dir(target), 0o700); err != nil {
		return err
	}
	output, err := os.OpenFile(target, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, mode)
	if err != nil {
		return err
	}
	if _, err := io.Copy(output, input); err != nil {
		_ = output.Close()
		return err
	}
	if err := output.Close(); err != nil {
		return err
	}
	return os.Chmod(target, mode)
}

func replaceExecutable(source string, target string) error {
	tempTarget := target + ".new"
	if err := copyFile(source, tempTarget, 0o755); err != nil {
		return err
	}
	if err := os.Rename(tempTarget, target); err != nil {
		_ = os.Remove(tempTarget)
		return err
	}
	return nil
}

func loadUpdateState(path string) (UpdateState, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return UpdateState{}, err
	}
	var state UpdateState
	return state, json.Unmarshal(data, &state)
}

func saveUpdateState(path string, state UpdateState) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	data, err := json.MarshalIndent(state, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, append(data, '\n'), 0o600)
}

func shouldCheckUpdate(state UpdateState, intervalSeconds int) bool {
	if state.LastCheckAt == "" {
		return true
	}
	lastCheckAt, err := time.Parse(time.RFC3339, state.LastCheckAt)
	if err != nil {
		return true
	}
	return time.Since(lastCheckAt) >= time.Duration(intervalSeconds)*time.Second
}

func safeFilePart(value string) string {
	replacer := strings.NewReplacer("/", "_", "\\", "_", ":", "_", " ", "_")
	return replacer.Replace(value)
}

func compareVersion(left string, right string) int {
	leftParts := versionParts(left)
	rightParts := versionParts(right)
	maxLen := len(leftParts)
	if len(rightParts) > maxLen {
		maxLen = len(rightParts)
	}
	for i := 0; i < maxLen; i++ {
		leftValue, rightValue := 0, 0
		if i < len(leftParts) {
			leftValue = leftParts[i]
		}
		if i < len(rightParts) {
			rightValue = rightParts[i]
		}
		if leftValue > rightValue {
			return 1
		}
		if leftValue < rightValue {
			return -1
		}
	}
	return 0
}

func versionParts(value string) []int {
	cleaned := normalizeVersion(value)
	var result []int
	for _, part := range strings.Split(cleaned, ".") {
		number, _ := strconv.Atoi(part)
		result = append(result, number)
	}
	return result
}

func normalizeVersion(value string) string {
	return strings.TrimPrefix(strings.TrimSpace(value), "v")
}
