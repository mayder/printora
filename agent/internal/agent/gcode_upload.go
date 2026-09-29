package agent

import "context"

func (r *Runner) RemoteGcodeUpload(ctx context.Context, jobPayload map[string]any) map[string]any {
	uploadKey := stringValue(jobPayload["upload_key"])
	if uploadKey == "" {
		return r.Moonraker.RemoteGcodeUpload(ctx, jobPayload)
	}
	body, err := r.API.DownloadGcodeUpload(ctx, uploadKey)
	if err != nil {
		return sanitizeMap(map[string]any{
			"safe_mode": "remote_gcode_upload_failed",
			"kind":      "gcode_upload",
			"status":    "failed",
			"detail":    "não foi possível baixar o G-code preparado pela nuvem",
		})
	}
	defer body.Close()
	return r.Moonraker.RemoteGcodeUploadReader(ctx, jobPayload, body)
}
