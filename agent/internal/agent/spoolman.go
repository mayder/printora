package agent

import (
	"context"
	"net/url"
)

func (c *MoonrakerClient) SpoolmanInventory(ctx context.Context) map[string]any {
	payload := map[string]any{
		"safe_mode": "read_only",
		"kind":      "spoolman_inventory",
	}
	c.get(ctx, "/server/spoolman/status", "spoolman_status", payload)
	proxyPath := "/server/spoolman/proxy?request_method=GET&path=" + url.QueryEscape("/v1/spool")
	c.get(ctx, proxyPath, "spools", payload)
	return sanitizeMap(payload)
}
