package agent

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/url"
	"sort"
	"strings"
	"time"
)

type MoonrakerClient struct {
	baseURL    string
	http       *http.Client
	visuals    operationVisualCache
	gcodeFiles gcodeFilesListCache
}

const updateManagerActionTimeout = 55 * time.Second
const operationGcodeFileLimit = 20

func NewMoonrakerClient(baseURL string, timeout time.Duration) *MoonrakerClient {
	return &MoonrakerClient{
		baseURL: strings.TrimRight(baseURL, "/"),
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

func (c *MoonrakerClient) Snapshot(ctx context.Context) map[string]any {
	result := map[string]any{
		"safe_mode": "read_only",
	}
	c.get(ctx, "/server/info", "server_info", result)
	c.get(ctx, "/printer/info", "printer_info", result)
	c.get(ctx, "/printer/objects/query?print_stats", "print_stats", result)
	c.get(ctx, "/printer/objects/query?extruder=temperature,target&heater_bed=temperature,target", "temperatures", result)
	c.get(ctx, "/machine/update/status", "update_status", result)
	return result
}

func (c *MoonrakerClient) PrintState(ctx context.Context) (string, error) {
	payload := map[string]any{}
	if err := c.get(ctx, "/printer/objects/query?print_stats", "print_stats", payload); err != nil {
		return "", err
	}
	state := nestedString(payload["print_stats"], "result", "status", "print_stats", "state")
	if state == "" {
		return "", fmt.Errorf("moonraker não informou print_stats.state")
	}
	return state, nil
}

func (c *MoonrakerClient) RemotePayload(ctx context.Context, jobType string) map[string]any {
	switch jobType {
	case "remote_moonraker_status":
		return sanitizeMap(c.Status(ctx))
	case "remote_operation_status":
		return sanitizeMap(c.OperationStatus(ctx))
	case "remote_gcode_files_list":
		return sanitizeMap(c.GcodeFiles(ctx, nil))
	case "remote_calibration_capabilities":
		return sanitizeMap(c.CalibrationCapabilities(ctx))
	case "remote_firmware_inventory":
		return sanitizeMap(c.FirmwareInventory(ctx))
	case "remote_audit":
		return sanitizeMap(map[string]any{
			"safe_mode": "read_only",
			"kind":      "audit",
			"snapshot":  c.Snapshot(ctx),
		})
	case "remote_snapshot":
		return sanitizeMap(c.Snapshot(ctx))
	case "remote_health":
		snapshot := c.Snapshot(ctx)
		return sanitizeMap(map[string]any{
			"safe_mode":    "read_only",
			"kind":         "health",
			"server_info":  snapshot["server_info"],
			"printer_info": snapshot["printer_info"],
			"print_stats":  snapshot["print_stats"],
			"errors":       snapshotErrors(snapshot),
		})
	case "remote_temperatures":
		payload := map[string]any{"safe_mode": "read_only", "kind": "temperatures"}
		c.get(ctx, "/printer/objects/query?extruder=temperature,target&heater_bed=temperature,target", "temperatures", payload)
		return sanitizeMap(payload)
	case "remote_update_status":
		payload := map[string]any{"safe_mode": "read_only", "kind": "update_status"}
		c.get(ctx, "/machine/update/status", "update_status", payload)
		return sanitizeMap(payload)
	case "remote_can_status":
		return sanitizeMap(map[string]any{
			"safe_mode": "read_only",
			"kind":      "can_status",
			"status":    "not_supported",
			"detail":    "CAN remoto exige helper local dedicado em pacote futuro; nenhum comando foi executado.",
		})
	case "remote_final_validation":
		return sanitizeMap(map[string]any{
			"safe_mode": "read_only",
			"kind":      "final_validation",
			"snapshot":  c.Snapshot(ctx),
			"status":    "read_only_collected",
		})
	case "remote_report_sanitized":
		return sanitizeMap(map[string]any{
			"safe_mode": "read_only",
			"kind":      "sanitized_report",
			"snapshot":  c.Snapshot(ctx),
		})
	case "remote_backup_preview":
		return map[string]any{
			"safe_mode": "dry_run",
			"kind":      "backup_preview",
			"status":    "planned",
			"detail":    "Backup real não transferido; payload grande bloqueado até política de retenção.",
		}
	case "remote_operation_preview":
		return map[string]any{
			"safe_mode": "dry_run",
			"kind":      "operation_preview",
			"status":    "blocked",
			"detail":    "Operações mutáveis exigem autorização/preflight do PKG-47.",
		}
	case "remote_firmware_preview":
		return map[string]any{
			"safe_mode": "dry_run",
			"kind":      "firmware_preview",
			"status":    "blocked",
			"detail":    "Build/flash remoto exige gates de firmware e PKG-47.",
		}
	default:
		return map[string]any{"safe_mode": "read_only", "status": "not_supported", "job_type": jobType}
	}
}

func (c *MoonrakerClient) Status(ctx context.Context) map[string]any {
	payload := map[string]any{
		"safe_mode": "read_only",
		"kind":      "moonraker_status",
	}
	c.get(ctx, "/server/info", "server_info", payload)
	c.get(ctx, "/printer/info", "printer_info", payload)
	c.get(ctx, "/machine/system_info", "system_info", payload)
	c.get(ctx, "/machine/proc_stats", "proc_stats", payload)
	c.get(ctx, "/machine/update/status", "update_status", payload)
	return payload
}

func (c *MoonrakerClient) OperationStatus(ctx context.Context) map[string]any {
	payload := c.Status(ctx)
	payload["kind"] = "operation_status"
	objects := c.objectList(ctx)
	payload["objects_list"] = objects
	query := operationQuery(objects)
	if query != "" {
		c.get(ctx, "/printer/objects/query?"+query, "operation_objects", payload)
	}
	filename := operationFilename(payload)
	if operationPrintIdle(payload) {
		c.enrichOperationGcodeFiles(ctx, payload)
	} else if filename != "" {
		c.get(ctx, "/server/files/metadata?filename="+url.QueryEscape(filename), "file_metadata", payload)
		c.enrichOperationVisuals(ctx, filename, payload)
	}
	c.get(ctx, "/server/history/totals", "history_totals", payload)
	return payload
}

func (c *MoonrakerClient) CalibrationCapabilities(ctx context.Context) map[string]any {
	payload := map[string]any{
		"safe_mode": "read_only",
		"kind":      "calibration_capabilities",
	}
	objects := c.objectList(ctx)
	payload["objects_list"] = objects
	if hasObject(objects, "toolhead") {
		c.get(ctx, "/printer/objects/query?toolhead=axis_minimum,axis_maximum", "toolhead", payload)
	}
	return payload
}

func (c *MoonrakerClient) FirmwareInventory(ctx context.Context) map[string]any {
	payload := map[string]any{
		"safe_mode": "read_only",
		"kind":      "firmware_inventory",
	}
	objects := c.objectList(ctx)
	payload["objects_list"] = objects
	query := firmwareQuery(objects)
	if query != "" {
		c.get(ctx, "/printer/objects/query?"+query, "object_payload", payload)
		compactFirmwareObjectPayload(payload)
	}
	return payload
}

func (c *MoonrakerClient) RemoteUpdateAction(ctx context.Context, jobPayload map[string]any) map[string]any {
	action := stringValue(jobPayload["action"])
	target := stringValue(jobPayload["target"])
	payload := map[string]any{
		"safe_mode": "remote_update_manager",
		"kind":      "update_action",
		"action":    action,
		"target":    target,
	}
	switch action {
	case "refresh":
		path := "/machine/update/refresh"
		if target != "" && target != "all" {
			path += "?name=" + url.QueryEscape(target)
		}
		c.postWithTimeout(ctx, path, nil, "moonraker_response", payload, updateManagerActionTimeout)
	case "update":
		path, ok := updatePath(target)
		if !ok {
			payload["moonraker_response_error"] = "target de update não suportado pelo agente"
			break
		}
		c.postWithTimeout(ctx, path, nil, "moonraker_response", payload, updateManagerActionTimeout)
	case "rollback":
		if target == "" || target == "all" {
			payload["moonraker_response_error"] = "rollback exige componente específico"
			break
		}
		c.postWithTimeout(ctx, "/machine/update/rollback", map[string]any{"name": target}, "moonraker_response", payload, updateManagerActionTimeout)
	default:
		payload["moonraker_response_error"] = "ação de update não suportada"
	}
	if payload["moonraker_response_error"] != nil {
		payload["status"] = "failed"
	} else {
		payload["status"] = "accepted"
	}
	return sanitizeMap(payload)
}

func (c *MoonrakerClient) RemoteMutationPreflight(ctx context.Context, jobPayload map[string]any) map[string]any {
	payload := map[string]any{
		"safe_mode":   "remote_mutation_preflight",
		"kind":        "mutation_preflight",
		"action_id":   stringValue(jobPayload["action_id"]),
		"criticality": stringValue(jobPayload["criticality"]),
	}
	c.get(ctx, "/server/info", "server_info", payload)
	c.get(ctx, "/printer/info", "printer_info", payload)
	payload["objects_list"] = c.objectList(ctx)
	c.get(ctx, "/printer/objects/query?print_stats&toolhead&gcode_move&extruder", "object_status", payload)
	blockers := remotePreflightBlockers(payload, stringValue(jobPayload["action_id"]))
	if blockers == nil {
		blockers = []string{}
	}
	payload["connected"] = !hasMoonrakerError(payload)
	payload["printing"] = remotePrintState(payload) != "" && !remotePrintIdle(remotePrintState(payload))
	payload["print_state"] = remotePrintState(payload)
	payload["klipper_state"] = nestedString(payload["printer_info"], "result", "state")
	payload["klippy_state"] = nestedString(payload["server_info"], "result", "klippy_state")
	payload["blockers"] = blockers
	payload["can_execute"] = len(blockers) == 0
	payload["rollback_plan"] = jobPayload["rollback_plan"]
	return sanitizeMap(payload)
}

func (c *MoonrakerClient) RemoteMutationExecute(ctx context.Context, jobPayload map[string]any) map[string]any {
	preflight := c.RemoteMutationPreflight(ctx, jobPayload)
	if preflight["can_execute"] != true {
		return sanitizeMap(map[string]any{
			"safe_mode": "remote_mutation_blocked",
			"kind":      "mutation_execute",
			"status":    "blocked",
			"detail":    "preflight remoto bloqueou a execução",
			"preflight": preflight,
		})
	}
	commands := stringList(jobPayload["command_preview"])
	if len(commands) == 0 {
		return sanitizeMap(map[string]any{
			"safe_mode": "remote_mutation_blocked",
			"kind":      "mutation_execute",
			"status":    "blocked",
			"detail":    "job remoto sem comando permitido",
			"preflight": preflight,
		})
	}
	result := map[string]any{
		"safe_mode":     "remote_mutation_execute",
		"kind":          "mutation_execute",
		"status":        "executed",
		"preflight":     preflight,
		"command_count": len(commands),
		"rollback_plan": jobPayload["rollback_plan"],
	}
	if err := c.post(ctx, "/printer/gcode/script", map[string]any{"script": strings.Join(commands, "\n")}, "moonraker_response", result); err != nil {
		result["status"] = "failed"
		result["detail"] = err.Error()
	}
	return sanitizeMap(result)
}

func (c *MoonrakerClient) RemoteGcodePreflight(ctx context.Context, jobPayload map[string]any) map[string]any {
	payload := map[string]any{
		"safe_mode":   "remote_gcode_preflight",
		"kind":        "gcode_preflight",
		"action_id":   stringValue(jobPayload["action_id"]),
		"criticality": stringValue(jobPayload["criticality"]),
	}
	c.get(ctx, "/server/info", "server_info", payload)
	c.get(ctx, "/printer/info", "printer_info", payload)
	payload["objects_list"] = c.objectList(ctx)
	c.get(ctx, "/printer/objects/query?print_stats&toolhead&gcode_move&extruder", "object_status", payload)
	blockers := remotePreflightBlockers(payload, stringValue(jobPayload["action_id"]))
	if blockers == nil {
		blockers = []string{}
	}
	payload["connected"] = !hasMoonrakerError(payload)
	payload["printing"] = remotePrintState(payload) != "" && !remotePrintIdle(remotePrintState(payload))
	payload["print_state"] = remotePrintState(payload)
	payload["klipper_state"] = nestedString(payload["printer_info"], "result", "state")
	payload["klippy_state"] = nestedString(payload["server_info"], "result", "klippy_state")
	payload["blockers"] = blockers
	payload["can_execute"] = len(blockers) == 0
	return sanitizeMap(payload)
}

func (c *MoonrakerClient) RemoteGcodeExecute(ctx context.Context, jobPayload map[string]any) map[string]any {
	preflight := c.RemoteGcodePreflight(ctx, jobPayload)
	if preflight["can_execute"] != true {
		return sanitizeMap(map[string]any{
			"safe_mode": "remote_gcode_blocked",
			"kind":      "gcode_execute",
			"status":    "blocked",
			"detail":    "preflight remoto bloqueou a execução",
			"preflight": preflight,
		})
	}
	commands := stringList(jobPayload["commands"])
	if len(commands) == 0 {
		commands = stringList(jobPayload["command_preview"])
	}
	if len(commands) == 0 {
		return sanitizeMap(map[string]any{
			"safe_mode": "remote_gcode_blocked",
			"kind":      "gcode_execute",
			"status":    "blocked",
			"detail":    "job remoto sem G-code permitido",
			"preflight": preflight,
		})
	}
	results := make([]any, 0, len(commands))
	sent := make([]any, 0, len(commands))
	status := "executed"
	detail := ""
	timeout := payloadTimeout(jobPayload, c.http.Timeout)
	initialConsole := c.gcodeStore(ctx, 20)
	initialMessages := gcodeStoreMessages(initialConsole)
	for _, command := range commands {
		result := map[string]any{"command": command}
		if err := c.postWithTimeout(ctx, "/printer/gcode/script", map[string]any{"script": command}, "moonraker_response", result, timeout); err != nil {
			detail = err.Error()
			if looksLikeAwaitingHeadersTimeout(detail) {
				result["accepted"] = true
				result["confirmation"] = "timeout_awaiting_headers"
				status = "dispatched_unconfirmed"
				results = append(results, result)
				sent = append(sent, command)
				break
			}
			result["accepted"] = false
			status = "failed_partial"
			if len(sent) == 0 {
				status = "failed"
			}
			results = append(results, result)
			break
		}
		result["accepted"] = true
		results = append(results, result)
		sent = append(sent, command)
	}
	time.Sleep(350 * time.Millisecond)
	finalConsole := c.gcodeStore(ctx, 30)
	finalMessages := gcodeStoreMessages(finalConsole)
	return sanitizeMap(map[string]any{
		"safe_mode":       "remote_gcode_execute",
		"kind":            "gcode_execute",
		"status":          status,
		"detail":          detail,
		"preflight":       preflight,
		"sent_commands":   sent,
		"results":         results,
		"console_before":  initialConsole,
		"console_after":   finalConsole,
		"console_excerpt": gcodeStoreDelta(initialMessages, finalMessages),
	})
}

func payloadTimeout(payload map[string]any, fallback time.Duration) time.Duration {
	seconds := intNumber(payload["timeout_seconds"])
	if seconds <= 0 {
		return fallback
	}
	if seconds < 5 {
		seconds = 5
	}
	if seconds > 180 {
		seconds = 180
	}
	return time.Duration(seconds) * time.Second
}

func looksLikeAwaitingHeadersTimeout(detail string) bool {
	detail = strings.ToLower(detail)
	return strings.Contains(detail, "awaiting headers") && (strings.Contains(detail, "timeout") || strings.Contains(detail, "deadline exceeded"))
}

func (c *MoonrakerClient) RemoteGcodeUpload(ctx context.Context, jobPayload map[string]any) map[string]any {
	return c.RemoteGcodeUploadReader(ctx, jobPayload, strings.NewReader(stringValue(jobPayload["gcode_content"])))
}

func (c *MoonrakerClient) RemoteGcodeUploadReader(ctx context.Context, jobPayload map[string]any, content io.Reader) map[string]any {
	startPrint := jobPayload["start_print"] == true
	preflightPayload := make(map[string]any, len(jobPayload)+1)
	for key, value := range jobPayload {
		preflightPayload[key] = value
	}
	if startPrint {
		preflightPayload["action_id"] = "gcode_file_print"
	} else if jobPayload["overwrite"] == true {
		preflightPayload["action_id"] = "gcode_file_overwrite"
	} else {
		preflightPayload["action_id"] = "gcode_file_upload"
	}
	preflight := c.RemoteGcodePreflight(ctx, preflightPayload)
	if preflight["can_execute"] != true {
		return sanitizeMap(map[string]any{
			"safe_mode": "remote_gcode_upload_blocked",
			"kind":      "gcode_upload",
			"status":    "blocked",
			"detail":    "preflight remoto bloqueou o envio",
			"preflight": preflight,
		})
	}
	remoteName := safeRemoteGcodePath(stringValue(jobPayload["remote_filename"]))
	if content == nil || remoteName == "" {
		return sanitizeMap(map[string]any{
			"safe_mode": "remote_gcode_upload_blocked",
			"kind":      "gcode_upload",
			"status":    "blocked",
			"detail":    "job remoto sem arquivo G-code válido",
			"preflight": preflight,
		})
	}
	exists, err := c.gcodeFileExists(ctx, remoteName)
	if err != nil {
		return sanitizeMap(map[string]any{
			"safe_mode":       "remote_gcode_upload_failed",
			"kind":            "gcode_upload",
			"status":          "failed",
			"detail":          "não foi possível verificar se o arquivo já existe",
			"remote_filename": remoteName,
			"preflight":       preflight,
		})
	}
	if exists && jobPayload["overwrite"] != true {
		return sanitizeMap(map[string]any{
			"safe_mode":       "remote_gcode_upload_blocked",
			"kind":            "gcode_upload",
			"status":          "blocked",
			"detail":          "arquivo já existe; confirme a sobrescrita",
			"remote_filename": remoteName,
			"preflight":       preflight,
		})
	}
	result := map[string]any{
		"safe_mode":       "remote_gcode_upload",
		"kind":            "gcode_upload",
		"status":          "uploaded",
		"remote_filename": remoteName,
		"started":         startPrint,
		"preflight":       preflight,
	}
	if err := c.uploadGcodeReader(ctx, remoteName, content, startPrint, result); err != nil {
		result["status"] = "failed"
		result["detail"] = err.Error()
		return sanitizeMap(result)
	}
	if startPrint {
		result["status"] = "started"
	}
	return sanitizeMap(result)
}

func (c *MoonrakerClient) RemoteGcodeDelete(ctx context.Context, jobPayload map[string]any) map[string]any {
	remoteName := safeRemoteGcodePath(stringValue(jobPayload["remote_filename"]))
	result := map[string]any{
		"safe_mode":       "remote_gcode_delete",
		"kind":            "gcode_delete",
		"status":          "deleted",
		"remote_filename": remoteName,
	}
	if remoteName == "" {
		result["status"] = "failed"
		result["detail"] = "arquivo remoto inválido"
		return sanitizeMap(result)
	}
	if err := c.delete(ctx, "/server/files/gcodes/"+escapePathSegments(remoteName), "moonraker_response", result); err != nil {
		result["status"] = "failed"
		result["detail"] = err.Error()
	}
	return sanitizeMap(result)
}

func (c *MoonrakerClient) gcodeStore(ctx context.Context, count int) any {
	payload := map[string]any{}
	if count <= 0 {
		count = 20
	}
	if err := c.get(ctx, fmt.Sprintf("/server/gcode_store?count=%d", count), "gcode_store", payload); err != nil {
		return map[string]any{"error": err.Error()}
	}
	return payload["gcode_store"]
}

func (c *MoonrakerClient) uploadGcodeReader(ctx context.Context, remoteName string, content io.Reader, print bool, result map[string]any) error {
	reader, writer := io.Pipe()
	form := multipart.NewWriter(writer)
	contentType := form.FormDataContentType()
	fileName := remoteName
	directory := ""
	if idx := strings.LastIndex(remoteName, "/"); idx >= 0 {
		directory = remoteName[:idx]
		fileName = remoteName[idx+1:]
	}
	go func() {
		var writeErr error
		if writeErr = form.WriteField("root", "gcodes"); writeErr == nil && directory != "" {
			writeErr = form.WriteField("path", directory)
		}
		if writeErr == nil {
			writeErr = form.WriteField("print", fmt.Sprintf("%t", print))
		}
		var part io.Writer
		if writeErr == nil {
			part, writeErr = form.CreateFormFile("file", fileName)
		}
		if writeErr == nil {
			_, writeErr = io.Copy(part, content)
		}
		if closeErr := form.Close(); writeErr == nil {
			writeErr = closeErr
		}
		_ = writer.CloseWithError(writeErr)
	}()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, c.baseURL+"/server/files/upload", reader)
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", contentType)
	resp, err := c.http.Do(req)
	if err != nil {
		result["moonraker_response_error"] = err.Error()
		return err
	}
	defer resp.Body.Close()
	var payload any
	_ = json.NewDecoder(resp.Body).Decode(&payload)
	result["moonraker_response"] = payload
	if resp.StatusCode >= 400 {
		err := fmt.Errorf("moonraker /server/files/upload: status %d", resp.StatusCode)
		result["moonraker_response_error"] = err.Error()
		return err
	}
	return nil
}

func (c *MoonrakerClient) gcodeFileExists(ctx context.Context, remoteName string) (bool, error) {
	requestURL := c.baseURL + "/server/files/metadata?filename=" + url.QueryEscape(remoteName)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, requestURL, nil)
	if err != nil {
		return false, err
	}
	resp, err := c.http.Do(req)
	if err != nil {
		return false, err
	}
	defer resp.Body.Close()
	switch resp.StatusCode {
	case http.StatusOK:
		return true, nil
	case http.StatusNotFound:
		return false, nil
	default:
		return false, fmt.Errorf("moonraker /server/files/metadata: status %d", resp.StatusCode)
	}
}

func safeRemoteGcodePath(value string) string {
	return cleanRelativeGcodeFilePath(value)
}

func gcodeStoreMessages(value any) []string {
	root, ok := value.(map[string]any)
	if !ok {
		return nil
	}
	entries, ok := nestedAny(root, "result", "gcode_store").([]any)
	if !ok {
		return nil
	}
	result := make([]string, 0, len(entries))
	for _, entry := range entries {
		mapped, ok := entry.(map[string]any)
		if !ok {
			continue
		}
		message := strings.TrimSpace(stringValue(mapped["message"]))
		if message != "" {
			result = append(result, message)
		}
	}
	return result
}

func gcodeStoreDelta(before []string, after []string) []string {
	if len(after) == 0 {
		return nil
	}
	if len(before) == 0 {
		return after
	}
	start := 0
	for overlap := minInt(len(before), len(after)); overlap > 0; overlap-- {
		beforeSuffix := before[len(before)-overlap:]
		for offset := 0; offset+overlap <= len(after); offset++ {
			if !stringSlicesEqual(beforeSuffix, after[offset:offset+overlap]) {
				continue
			}
			start = offset + overlap
		}
		if start > 0 {
			break
		}
	}
	if start >= len(after) {
		return nil
	}
	return after[start:]
}

func stringSlicesEqual(left []string, right []string) bool {
	if len(left) != len(right) {
		return false
	}
	for index := range left {
		if left[index] != right[index] {
			return false
		}
	}
	return true
}

func minInt(left int, right int) int {
	if left < right {
		return left
	}
	return right
}

func (c *MoonrakerClient) Doctor(ctx context.Context) error {
	payload := map[string]any{}
	if err := c.get(ctx, "/server/info", "server_info", payload); err != nil {
		return err
	}
	return nil
}

func snapshotErrors(snapshot map[string]any) []string {
	var errors []string
	for key, value := range snapshot {
		if strings.HasSuffix(key, "_error") {
			errors = append(errors, fmt.Sprintf("%s=%v", key, value))
		}
	}
	sort.Strings(errors)
	return errors
}

func (c *MoonrakerClient) objectList(ctx context.Context) []string {
	payload := map[string]any{}
	if err := c.get(ctx, "/printer/objects/list", "objects", payload); err != nil {
		return nil
	}
	values, ok := payload["objects"].(map[string]any)
	if !ok {
		return nil
	}
	result, ok := values["result"].(map[string]any)
	if !ok {
		return nil
	}
	return stringList(result["objects"])
}

func operationQuery(objects []string) string {
	parts := []string{}
	for _, object := range objects {
		if fields, ok := operationObjectFields(object); ok {
			parts = append(parts, moonrakerQueryEscape(object)+"="+fields)
		}
	}
	sort.Strings(parts)
	return strings.Join(parts, "&")
}

func operationObjectFields(object string) (string, bool) {
	switch object {
	case "print_stats", "toolhead", "gcode_move", "extruder", "heater_bed", "fan", "virtual_sdcard", "display_status", "webhooks":
		return "", true
	}
	switch {
	case strings.HasPrefix(object, "fan_generic "):
		return "", true
	case strings.HasPrefix(object, "heater_fan "):
		return "", true
	case strings.HasPrefix(object, "controller_fan "):
		return "", true
	case strings.HasPrefix(object, "temperature_sensor "):
		return "temperature,target,power", true
	case strings.HasPrefix(object, "heater_generic "):
		return "temperature,target,power", true
	case strings.HasPrefix(object, "output_pin "):
		return "", true
	case strings.HasPrefix(object, "led "):
		return "color_data", true
	case strings.HasPrefix(object, "neopixel "):
		return "color_data", true
	case strings.HasPrefix(object, "dotstar "):
		return "color_data", true
	case strings.HasPrefix(object, "pca9533 "):
		return "color_data", true
	case strings.HasPrefix(object, "pca9632 "):
		return "color_data", true
	default:
		return "", false
	}
}

func moonrakerQueryEscape(value string) string {
	return strings.ReplaceAll(url.QueryEscape(value), "+", "%20")
}

func operationFilename(payload map[string]any) string {
	return strings.TrimSpace(nestedString(payload["operation_objects"], "result", "status", "print_stats", "filename"))
}

func operationPrintIdle(payload map[string]any) bool {
	return remotePrintIdle(nestedString(payload["operation_objects"], "result", "status", "print_stats", "state"))
}

func (c *MoonrakerClient) enrichOperationGcodeFiles(ctx context.Context, payload map[string]any) {
	if err := c.get(ctx, "/server/files/list?root=gcodes", "gcode_files", payload); err != nil {
		return
	}
	payload["gcode_files"] = map[string]any{"result": compactGcodeFiles(payload["gcode_files"], operationGcodeFileLimit)}
}

func compactGcodeFiles(value any, limit int) []any {
	items := unwrapGcodeFileItems(value)
	files := make([]map[string]any, 0, len(items))
	for _, item := range items {
		file := compactGcodeFile(item)
		filename := stringValue(file["filename"])
		if filename == "" || !isGcodeFileName(filename) {
			continue
		}
		files = append(files, file)
	}
	sort.SliceStable(files, func(i, j int) bool {
		left, _ := numberFromAny(files[i]["modified"])
		right, _ := numberFromAny(files[j]["modified"])
		return left > right
	})
	if limit > 0 && len(files) > limit {
		files = files[:limit]
	}
	result := make([]any, 0, len(files))
	for _, file := range files {
		result = append(result, file)
	}
	return result
}

func unwrapGcodeFileItems(value any) []any {
	switch typed := value.(type) {
	case []any:
		items := make([]any, 0, len(typed))
		for _, item := range typed {
			if mapped := mapValue(item); len(mapped) > 0 {
				if children := unwrapGcodeFileItems(mapped["children"]); len(children) > 0 {
					items = append(items, children...)
				}
			}
			items = append(items, item)
		}
		return items
	case []map[string]any:
		items := make([]any, 0, len(typed))
		for _, item := range typed {
			if children := unwrapGcodeFileItems(item["children"]); len(children) > 0 {
				items = append(items, children...)
			}
			items = append(items, item)
		}
		return items
	case map[string]any:
		for _, key := range []string{"result", "files", "items"} {
			if items := unwrapGcodeFileItems(typed[key]); len(items) > 0 {
				return items
			}
		}
		children := unwrapGcodeFileItems(typed["children"])
		if len(children) > 0 {
			return children
		}
		return []any{typed}
	default:
		return nil
	}
}

func compactGcodeFile(value any) map[string]any {
	item := mapValue(value)
	filename := firstString(item, "filename", "path", "name")
	path := firstString(item, "path", "filename", "name")
	return map[string]any{
		"filename":              filename,
		"path":                  path,
		"size":                  firstNumber(item, "size"),
		"modified":              firstNumber(item, "modified"),
		"estimated_time":        firstNumber(item, "estimated_time"),
		"slicer":                firstString(item, "slicer"),
		"slicer_version":        firstString(item, "slicer_version"),
		"object_height":         firstNumber(item, "object_height"),
		"layer_height":          firstNumber(item, "layer_height"),
		"first_layer_height":    firstNumber(item, "first_layer_height"),
		"nozzle_diameter":       firstNumber(item, "nozzle_diameter"),
		"filament_total":        firstNumber(item, "filament_total"),
		"filament_weight_total": firstNumber(item, "filament_weight_total"),
		"filament_type":         firstString(item, "filament_type"),
		"filament_name":         firstString(item, "filament_name"),
		"print_start_time":      firstNumber(item, "print_start_time"),
		"print_end_time":        firstNumber(item, "print_end_time"),
		"last_print_duration":   firstNumber(item, "last_print_duration"),
	}
}

func firstString(item map[string]any, keys ...string) string {
	for _, key := range keys {
		value := strings.TrimSpace(stringValue(item[key]))
		if value != "" {
			return value
		}
	}
	return ""
}

func firstNumber(item map[string]any, keys ...string) any {
	for _, key := range keys {
		if value, ok := numberFromAny(item[key]); ok {
			return value
		}
	}
	return nil
}

func isGcodeFileName(value string) bool {
	lowered := strings.ToLower(strings.TrimSpace(value))
	return strings.HasSuffix(lowered, ".gcode") ||
		strings.HasSuffix(lowered, ".gcode.gz") ||
		strings.HasSuffix(lowered, ".gco") ||
		strings.HasSuffix(lowered, ".g") ||
		strings.HasSuffix(lowered, ".gc") ||
		strings.HasSuffix(lowered, ".nc") ||
		strings.HasSuffix(lowered, ".ngc") ||
		strings.HasSuffix(lowered, ".tap")
}

func hasObject(objects []string, target string) bool {
	for _, object := range objects {
		if object == target {
			return true
		}
	}
	return false
}

func updatePath(target string) (string, bool) {
	switch target {
	case "all":
		return "/machine/update/full", true
	case "system":
		return "/machine/update/system", true
	case "klipper", "moonraker":
		return "/machine/update/" + target, true
	case "":
		return "", false
	default:
		return "/machine/update/client?name=" + url.QueryEscape(target), true
	}
}

func firmwareQuery(objects []string) string {
	parts := []string{}
	for _, object := range objects {
		if object == "mcu" || strings.HasPrefix(object, "mcu ") {
			parts = append(parts, url.QueryEscape(object)+"=mcu_version,mcu_build_versions")
		}
		if object == "configfile" {
			parts = append(parts, "configfile=settings")
		}
	}
	sort.Strings(parts)
	return strings.Join(parts, "&")
}

func compactFirmwareObjectPayload(payload map[string]any) {
	objectPayload := mapValue(payload["object_payload"])
	result := mapValue(objectPayload["result"])
	status := mapValue(result["status"])
	if len(status) == 0 {
		return
	}
	compactStatus := map[string]any{}
	for key, value := range status {
		if key == "mcu" || strings.HasPrefix(key, "mcu ") {
			compactStatus[key] = value
		}
	}
	configfile := mapValue(status["configfile"])
	settings := mapValue(configfile["settings"])
	if len(settings) > 0 {
		compactSettings := map[string]any{}
		for key, value := range settings {
			if key == "mcu" || strings.HasPrefix(key, "mcu ") {
				compactSettings[key] = value
			}
		}
		if len(compactSettings) > 0 {
			compactStatus["configfile"] = map[string]any{"settings": compactSettings}
		}
	}
	result["status"] = compactStatus
	objectPayload["result"] = result
	payload["object_payload"] = objectPayload
}

func remotePreflightBlockers(payload map[string]any, actionID string) []string {
	var blockers []string
	if hasMoonrakerError(payload) {
		blockers = append(blockers, "Moonraker indisponível no preflight remoto.")
	}
	klipperState := nestedString(payload["printer_info"], "result", "state")
	if klipperState != "" && klipperState != "ready" {
		blockers = append(blockers, fmt.Sprintf("Klipper não está ready (%s).", klipperState))
	}
	klippyState := nestedString(payload["server_info"], "result", "klippy_state")
	if klippyState != "" && klippyState != "ready" {
		blockers = append(blockers, fmt.Sprintf("Klippy não está ready (%s).", klippyState))
	}
	printState := remotePrintState(payload)
	if actionBlocksWhilePrinting(actionID) && printState != "" && !remotePrintIdle(printState) {
		blockers = append(blockers, fmt.Sprintf("Impressão em andamento (%s).", printState))
	}
	return blockers
}

func actionBlocksWhilePrinting(actionID string) bool {
	switch actionID {
	case "set_fan", "set_led", "set_output_pin", "gcode_file_upload", "gcode_file_metadata_scan",
		"gcode_directory_create", "gcode_queue_add", "gcode_queue_remove", "gcode_queue_pause", "gcode_queue_resume", "gcode_queue_start":
		return false
	default:
		return true
	}
}

func hasMoonrakerError(payload map[string]any) bool {
	for key := range payload {
		if strings.HasSuffix(key, "_error") {
			return true
		}
	}
	return false
}

func remotePrintState(payload map[string]any) string {
	return nestedString(payload["object_status"], "result", "status", "print_stats", "state")
}

func remotePrintIdle(state string) bool {
	switch state {
	case "", "standby", "complete", "cancelled", "error":
		return true
	default:
		return false
	}
}

func nestedString(value any, path ...string) string {
	return stringValue(nestedAny(value, path...))
}

func nestedAny(value any, path ...string) any {
	current := value
	for _, key := range path {
		mapped, ok := current.(map[string]any)
		if !ok {
			return nil
		}
		current = mapped[key]
	}
	return current
}

func stringList(value any) []string {
	items, ok := value.([]any)
	if !ok {
		if strings, ok := value.([]string); ok {
			return strings
		}
		return nil
	}
	result := make([]string, 0, len(items))
	for _, item := range items {
		if text := strings.TrimSpace(stringValue(item)); text != "" {
			result = append(result, text)
		}
	}
	return result
}

func sanitizePayload(value any) any {
	switch typed := value.(type) {
	case map[string]any:
		cleaned := map[string]any{}
		for key, item := range typed {
			lowerKey := strings.ToLower(key)
			if strings.Contains(lowerKey, "password") || strings.Contains(lowerKey, "token") || strings.Contains(lowerKey, "secret") || strings.Contains(lowerKey, "credential") || strings.Contains(lowerKey, "private_key") {
				cleaned[key] = "[redacted]"
				continue
			}
			cleaned[key] = sanitizePayload(item)
		}
		return cleaned
	case []any:
		cleaned := make([]any, 0, len(typed))
		for _, item := range typed {
			cleaned = append(cleaned, sanitizePayload(item))
		}
		return cleaned
	default:
		return typed
	}
}

func sanitizeMap(value map[string]any) map[string]any {
	if mapped, ok := sanitizePayload(value).(map[string]any); ok {
		return mapped
	}
	return map[string]any{}
}

func (c *MoonrakerClient) post(ctx context.Context, path string, payload map[string]any, key string, out map[string]any) error {
	return c.postWithTimeout(ctx, path, payload, key, out, 0)
}

func (c *MoonrakerClient) postWithTimeout(ctx context.Context, path string, payload map[string]any, key string, out map[string]any, timeout time.Duration) error {
	target, err := moonrakerEndpointURL(c.baseURL, path)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	var body *bytes.Reader
	if payload != nil {
		bodyBytes, err := json.Marshal(payload)
		if err != nil {
			out[key+"_error"] = err.Error()
			return err
		}
		body = bytes.NewReader(bodyBytes)
	} else {
		body = bytes.NewReader(nil)
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, target, body)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	client := c.http
	if timeout > 0 && timeout != c.http.Timeout {
		client = &http.Client{Timeout: timeout, Transport: c.http.Transport}
	}
	resp, err := client.Do(req)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		err := fmt.Errorf("moonraker %s: status %d", path, resp.StatusCode)
		out[key+"_error"] = err.Error()
		return err
	}
	var decoded any
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	out[key] = decoded
	return nil
}

func (c *MoonrakerClient) get(ctx context.Context, path string, key string, out map[string]any) error {
	target, err := moonrakerEndpointURL(c.baseURL, path)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target, nil)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	resp, err := c.http.Do(req)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		err := fmt.Errorf("moonraker %s: status %d", path, resp.StatusCode)
		out[key+"_error"] = err.Error()
		return err
	}
	var decoded any
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	out[key] = decoded
	return nil
}

func (c *MoonrakerClient) delete(ctx context.Context, path string, key string, out map[string]any) error {
	target, err := moonrakerEndpointURL(c.baseURL, path)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	req, err := http.NewRequestWithContext(ctx, http.MethodDelete, target, nil)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	resp, err := c.http.Do(req)
	if err != nil {
		out[key+"_error"] = err.Error()
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		err := fmt.Errorf("moonraker %s: status %d", path, resp.StatusCode)
		out[key+"_error"] = err.Error()
		return err
	}
	var decoded any
	if err := json.NewDecoder(resp.Body).Decode(&decoded); err == nil {
		out[key] = decoded
	}
	return nil
}

func moonrakerEndpointURL(baseURL string, endpoint string) (string, error) {
	pathPart, query, hasQuery := strings.Cut(endpoint, "?")
	target, err := url.JoinPath(baseURL, strings.TrimPrefix(pathPart, "/"))
	if err != nil {
		return "", err
	}
	if hasQuery {
		target += "?" + query
	}
	return target, nil
}
