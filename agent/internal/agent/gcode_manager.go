package agent

import (
	"context"
	"fmt"
	"net/url"
	"path"
	"strings"
)

func (c *MoonrakerClient) RemoteGcodeManager(ctx context.Context, jobPayload map[string]any) map[string]any {
	action := strings.TrimSpace(stringValue(jobPayload["action"]))
	result := map[string]any{
		"safe_mode": "remote_gcode_manager",
		"kind":      "gcode_manager",
		"action":    action,
	}
	switch action {
	case "queue_status":
		if err := c.get(ctx, "/server/job_queue/status", "queue", result); err != nil {
			return gcodeFileActionFailed(result, err.Error())
		}
		result["status"] = "executed"
		return sanitizeMap(result)
	case "metadata_scan":
		filename := cleanRelativeGcodeFilePath(stringValue(jobPayload["filename"]))
		if filename == "" {
			return gcodeFileActionFailed(result, "arquivo G-code inválido")
		}
		if !c.managerPreflight(ctx, "gcode_file_metadata_scan", result) {
			return gcodeFileActionBlocked(result, "preflight remoto bloqueou a atualização de metadados")
		}
		if err := c.post(ctx, "/server/files/metascan?filename="+url.QueryEscape(filename), nil, "moonraker_response", result); err != nil {
			return gcodeFileActionFailed(result, err.Error())
		}
	case "preheat":
		hotend := intNumber(jobPayload["hotend_temperature"])
		bed := intNumber(jobPayload["bed_temperature"])
		if hotend < 0 || hotend > 300 || bed < 0 || bed > 130 || hotend+bed == 0 {
			return gcodeFileActionFailed(result, "temperaturas de pré-aquecimento inválidas")
		}
		commands := []any{}
		if bed > 0 {
			commands = append(commands, fmt.Sprintf("SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET=%d", bed))
		}
		if hotend > 0 {
			commands = append(commands, fmt.Sprintf("SET_HEATER_TEMPERATURE HEATER=extruder TARGET=%d", hotend))
		}
		execution := c.RemoteGcodeExecute(ctx, map[string]any{
			"action_id": "gcode_preheat",
			"commands":  commands,
		})
		result["execution"] = execution
		if execution["status"] != "executed" && execution["status"] != "dispatched_unconfirmed" {
			return gcodeFileActionFailed(result, stringValue(execution["detail"]))
		}
	case "directory_create", "directory_delete", "directory_move":
		preflightAction := "gcode_directory_action"
		if action == "directory_create" {
			preflightAction = "gcode_directory_create"
		}
		if !c.managerPreflight(ctx, preflightAction, result) {
			return gcodeFileActionBlocked(result, "preflight remoto bloqueou a ação de pasta")
		}
		if managerResult := c.executeGcodeDirectoryAction(ctx, action, jobPayload, result); managerResult != nil {
			return managerResult
		}
	case "queue_add", "queue_remove", "queue_pause", "queue_resume", "queue_start":
		preflightAction := "gcode_queue_" + strings.TrimPrefix(action, "queue_")
		if !c.managerPreflight(ctx, preflightAction, result) {
			return gcodeFileActionBlocked(result, "preflight remoto bloqueou a ação da fila")
		}
		if managerResult := c.executeGcodeQueueAction(ctx, action, jobPayload, result); managerResult != nil {
			return managerResult
		}
	case "batch_delete", "batch_duplicate", "batch_move":
		return c.executeGcodeBatchAction(ctx, action, jobPayload, result)
	default:
		return gcodeFileActionFailed(result, "ação do gerenciador G-code não suportada")
	}
	result["status"] = "executed"
	return sanitizeMap(result)
}

func (c *MoonrakerClient) managerPreflight(ctx context.Context, actionID string, result map[string]any) bool {
	preflight := c.RemoteGcodePreflight(ctx, map[string]any{"action_id": actionID, "criticality": "gcode_manager"})
	result["preflight"] = preflight
	return preflight["can_execute"] == true
}

func (c *MoonrakerClient) executeGcodeDirectoryAction(ctx context.Context, action string, payload map[string]any, result map[string]any) map[string]any {
	directory := cleanRelativeGcodeDirectory(stringValue(payload["directory"]))
	target := cleanRelativeGcodeDirectory(stringValue(payload["target_directory"]))
	if directory == "" {
		return gcodeFileActionFailed(result, "pasta G-code inválida")
	}
	var err error
	switch action {
	case "directory_create":
		err = c.post(ctx, "/server/files/directory", map[string]any{"path": "gcodes/" + directory}, "moonraker_response", result)
	case "directory_delete":
		err = c.delete(ctx, "/server/files/directory?path="+url.QueryEscape("gcodes/"+directory)+"&force=false", "moonraker_response", result)
	case "directory_move":
		if target == "" {
			return gcodeFileActionFailed(result, "destino da pasta inválido")
		}
		err = c.post(ctx, "/server/files/move", map[string]any{"source": "gcodes/" + directory, "dest": "gcodes/" + target}, "moonraker_response", result)
	}
	if err != nil {
		return gcodeFileActionFailed(result, err.Error())
	}
	result["directory"] = directory
	result["target_directory"] = target
	return nil
}

func (c *MoonrakerClient) executeGcodeQueueAction(ctx context.Context, action string, payload map[string]any, result map[string]any) map[string]any {
	var err error
	switch action {
	case "queue_add":
		filenames := cleanGcodeFilenameList(payload["filenames"])
		if len(filenames) == 0 {
			return gcodeFileActionFailed(result, "selecione arquivos G-code para a fila")
		}
		err = c.post(ctx, "/server/job_queue/job", map[string]any{"filenames": filenames}, "moonraker_response", result)
	case "queue_remove":
		jobIDs := cleanStringList(payload["job_ids"], 100)
		if len(jobIDs) == 0 {
			return gcodeFileActionFailed(result, "selecione itens da fila")
		}
		err = c.delete(ctx, "/server/job_queue/job?job_ids="+url.QueryEscape(strings.Join(jobIDs, ",")), "moonraker_response", result)
	case "queue_pause", "queue_resume", "queue_start":
		queueAction := strings.TrimPrefix(action, "queue_")
		if queueAction == "resume" {
			queueAction = "start"
		}
		err = c.post(ctx, "/server/job_queue/"+queueAction, nil, "moonraker_response", result)
	}
	if err != nil {
		return gcodeFileActionFailed(result, err.Error())
	}
	return nil
}

func (c *MoonrakerClient) executeGcodeBatchAction(ctx context.Context, action string, payload map[string]any, result map[string]any) map[string]any {
	filenames := cleanGcodeFilenameList(payload["filenames"])
	if len(filenames) == 0 {
		return gcodeFileActionFailed(result, "selecione arquivos G-code")
	}
	if len(filenames) > 50 {
		return gcodeFileActionFailed(result, "o lote aceita no máximo 50 arquivos")
	}
	targetDirectory := cleanRelativeGcodeDirectory(stringValue(payload["target_directory"]))
	itemAction := strings.TrimPrefix(action, "batch_")
	items := make([]any, 0, len(filenames))
	for _, filename := range filenames {
		target := ""
		switch itemAction {
		case "move":
			if targetDirectory == "" {
				return gcodeFileActionFailed(result, "destino do lote inválido")
			}
			target = path.Join(targetDirectory, path.Base(filename))
		case "duplicate":
			extension := path.Ext(filename)
			target = strings.TrimSuffix(filename, extension) + "-copia" + extension
		}
		item := c.RemoteGcodeFileAction(ctx, map[string]any{
			"action":          itemAction,
			"filename":        filename,
			"target_filename": target,
		})
		items = append(items, item)
		if item["status"] == "failed" || item["status"] == "blocked" {
			result["items"] = items
			return gcodeFileActionFailed(result, fmt.Sprintf("lote interrompido em %s", filename))
		}
	}
	result["items"] = items
	result["processed"] = len(items)
	result["status"] = "executed"
	return sanitizeMap(result)
}

func cleanRelativeGcodeDirectory(value string) string {
	value = strings.Trim(strings.TrimSpace(strings.ReplaceAll(value, "\\", "/")), "/")
	value = strings.TrimPrefix(value, "gcodes/")
	if value == "" {
		return ""
	}
	for _, part := range strings.Split(value, "/") {
		if part == "" || part == "." || part == ".." {
			return ""
		}
	}
	clean := path.Clean(value)
	if clean == "." || strings.HasPrefix(clean, "../") {
		return ""
	}
	return clean
}

func cleanGcodeFilenameList(value any) []string {
	raw, ok := value.([]any)
	if !ok {
		if stringsList, stringsOK := value.([]string); stringsOK {
			raw = make([]any, len(stringsList))
			for index, item := range stringsList {
				raw[index] = item
			}
		}
	}
	result := make([]string, 0, len(raw))
	for _, item := range raw {
		if clean := cleanRelativeGcodeFilePath(stringValue(item)); clean != "" {
			result = append(result, clean)
		}
	}
	return result
}

func cleanStringList(value any, limit int) []string {
	raw, ok := value.([]any)
	if !ok {
		return nil
	}
	result := make([]string, 0, len(raw))
	for _, item := range raw {
		clean := strings.TrimSpace(stringValue(item))
		if clean != "" {
			result = append(result, clean)
			if len(result) >= limit {
				break
			}
		}
	}
	return result
}
