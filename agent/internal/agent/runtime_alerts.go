package agent

import (
	"regexp"
	"strings"
)

const (
	runtimeAlertStoreLimit = 200
	runtimeAlertMaxCount   = 20
	runtimeAlertMaxLength  = 1200
)

var runtimeAlertMarkers = []string{
	"klipper warning",
	"has deprecated code",
	"recompiling and flashing is recommended",
	"mcu protocol error",
	"command format mismatch",
	"lost communication with mcu",
	"unable to connect to mcu",
	"timer too close",
	"adc out of range",
	"heater extruder not heating",
	"heater heater_bed not heating",
	"verify_heater",
	"internal error on command",
	"transition to shutdown state",
	"klipper state: shutdown",
}

var (
	runtimeAlertSecretPattern = regexp.MustCompile(`(?i)\b(token|password|passwd|secret|api[_-]?key)\s*[=:]\s*\S+`)
	runtimeAlertURLPattern    = regexp.MustCompile(`https?://\S+`)
	runtimeAlertHomePattern   = regexp.MustCompile(`/home/[A-Za-z0-9._-]+/\S*`)
)

func klipperRuntimeAlertMessages(value any) []string {
	messages := gcodeStoreMessages(value)
	if len(messages) == 0 {
		return []string{}
	}

	alerts := make([]string, 0, minInt(len(messages), runtimeAlertMaxCount))
	seen := map[string]struct{}{}
	for index := len(messages) - 1; index >= 0 && len(alerts) < runtimeAlertMaxCount; index-- {
		message := compactRuntimeAlertMessage(messages[index])
		if !isKlipperRuntimeAlert(message) {
			continue
		}
		key := strings.ToLower(message)
		if _, exists := seen[key]; exists {
			continue
		}
		seen[key] = struct{}{}
		alerts = append(alerts, message)
	}
	reverseStrings(alerts)
	return alerts
}

func runtimeAlertCollectionState(value any) string {
	root, ok := value.(map[string]any)
	if !ok {
		return "unavailable"
	}
	if strings.TrimSpace(stringValue(root["error"])) != "" {
		return "unavailable"
	}
	return "loaded"
}

func isKlipperRuntimeAlert(message string) bool {
	lowered := strings.ToLower(strings.TrimSpace(message))
	if strings.HasPrefix(lowered, "!!") {
		return true
	}
	for _, marker := range runtimeAlertMarkers {
		if strings.Contains(lowered, marker) {
			return true
		}
	}
	return false
}

func compactRuntimeAlertMessage(message string) string {
	message = strings.Join(strings.Fields(strings.TrimSpace(message)), " ")
	message = runtimeAlertSecretPattern.ReplaceAllString(message, "$1=<redacted>")
	message = runtimeAlertURLPattern.ReplaceAllString(message, "<url>")
	message = runtimeAlertHomePattern.ReplaceAllString(message, "<path>")
	if len(message) <= runtimeAlertMaxLength {
		return message
	}
	return message[:runtimeAlertMaxLength-3] + "..."
}

func reverseStrings(values []string) {
	for left, right := 0, len(values)-1; left < right; left, right = left+1, right-1 {
		values[left], values[right] = values[right], values[left]
	}
}
