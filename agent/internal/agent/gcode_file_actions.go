package agent

import (
	"context"
	"net/url"
	"path"
	"strings"
	"time"
)

const gcodeFileActionTimeout = 45 * time.Second

func (c *MoonrakerClient) RemoteGcodeFileAction(ctx context.Context, jobPayload map[string]any) map[string]any {
	action := strings.TrimSpace(stringValue(jobPayload["action"]))
	filename := cleanRelativeGcodeFilePath(stringValue(jobPayload["filename"]))
	target := cleanRelativeGcodeFilePath(stringValue(jobPayload["target_filename"]))
	result := map[string]any{
		"safe_mode":       "remote_gcode_file_action",
		"kind":            "gcode_file_action",
		"action":          action,
		"filename":        filename,
		"target_filename": target,
	}
	if filename == "" {
		return gcodeFileActionFailed(result, "arquivo G-code inválido")
	}
	if action == "" {
		return gcodeFileActionFailed(result, "ação de arquivo G-code inválida")
	}
	if actionRequiresTarget(action) && target == "" {
		return gcodeFileActionFailed(result, "ação exige destino G-code válido")
	}

	preflight := c.RemoteGcodePreflight(ctx, map[string]any{
		"action_id":   "gcode_file_" + action,
		"criticality": "gcode_file_action",
	})
	result["preflight"] = preflight
	if preflight["can_execute"] != true {
		return gcodeFileActionBlocked(result, "preflight remoto bloqueou a ação")
	}

	switch action {
	case "print":
		return c.executeGcodeFilePrint(ctx, filename, result)
	case "rename", "move":
		return c.executeGcodeFileMove(ctx, filename, target, action, result)
	case "duplicate":
		return c.executeGcodeFileCopy(ctx, filename, target, result)
	case "delete":
		return c.executeGcodeFileDelete(ctx, filename, result)
	default:
		return gcodeFileActionFailed(result, "ação de arquivo G-code não suportada")
	}
}

func (c *MoonrakerClient) executeGcodeFilePrint(ctx context.Context, filename string, result map[string]any) map[string]any {
	if err := c.postWithTimeout(ctx, "/printer/print/start?filename="+url.QueryEscape(filename), nil, "moonraker_response", result, gcodeFileActionTimeout); err != nil {
		return gcodeFileActionFailed(result, err.Error())
	}
	result["status"] = "printed"
	result["started"] = true
	return sanitizeMap(result)
}

func (c *MoonrakerClient) executeGcodeFileMove(ctx context.Context, filename string, target string, action string, result map[string]any) map[string]any {
	payload := map[string]any{"source": "gcodes/" + filename, "dest": "gcodes/" + target}
	if err := c.postWithTimeout(ctx, "/server/files/move", payload, "moonraker_response", result, gcodeFileActionTimeout); err != nil {
		return gcodeFileActionFailed(result, err.Error())
	}
	if action == "rename" {
		result["status"] = "renamed"
	} else {
		result["status"] = "moved"
	}
	return sanitizeMap(result)
}

func (c *MoonrakerClient) executeGcodeFileCopy(ctx context.Context, filename string, target string, result map[string]any) map[string]any {
	payload := map[string]any{"source": "gcodes/" + filename, "dest": "gcodes/" + target}
	if err := c.postWithTimeout(ctx, "/server/files/copy", payload, "moonraker_response", result, gcodeFileActionTimeout); err != nil {
		return gcodeFileActionFailed(result, err.Error())
	}
	result["status"] = "duplicated"
	return sanitizeMap(result)
}

func (c *MoonrakerClient) executeGcodeFileDelete(ctx context.Context, filename string, result map[string]any) map[string]any {
	if err := c.delete(ctx, "/server/files/gcodes/"+escapePathSegments(filename), "moonraker_response", result); err != nil {
		return gcodeFileActionFailed(result, err.Error())
	}
	result["status"] = "deleted"
	return sanitizeMap(result)
}

func gcodeFileActionBlocked(result map[string]any, detail string) map[string]any {
	result["status"] = "blocked"
	result["detail"] = detail
	return sanitizeMap(result)
}

func gcodeFileActionFailed(result map[string]any, detail string) map[string]any {
	result["status"] = "failed"
	result["detail"] = detail
	return sanitizeMap(result)
}

func actionRequiresTarget(action string) bool {
	switch action {
	case "rename", "move", "duplicate":
		return true
	default:
		return false
	}
}

func cleanRelativeGcodeFilePath(value string) string {
	value = strings.TrimSpace(strings.ReplaceAll(value, "\\", "/"))
	value = strings.TrimPrefix(value, "/")
	value = strings.TrimPrefix(value, "gcodes/")
	for _, part := range strings.Split(value, "/") {
		if strings.TrimSpace(part) == ".." {
			return ""
		}
	}
	clean := normalizedMoonrakerGcodePath(value)
	if clean == "" || !isGcodeFileName(clean) {
		return ""
	}
	if path.Clean(clean) != clean {
		return ""
	}
	return clean
}
