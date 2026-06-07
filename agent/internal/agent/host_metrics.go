package agent

import (
	"bufio"
	"context"
	"os"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"
)

const hostMetricsInterval = 5 * time.Minute
const hostMetricsCPUSampleWindow = 200 * time.Millisecond

type hostMetricsCache struct {
	collectedAt time.Time
	payload     map[string]any
	network     networkCounters
}

type processSample struct {
	pid       int
	service   string
	command   string
	cpuTicks  uint64
	rssBytes  uint64
	vszBytes  uint64
	totalTick uint64
}

type serviceMetric struct {
	name        string
	command     string
	pids        int
	cpuPercent  float64
	rssBytes    uint64
	vszBytes    uint64
	networkNote string
}

type networkCounters struct {
	rxBytes uint64
	txBytes uint64
}

func (r *Runner) CachedHostMetrics(ctx context.Context) map[string]any {
	if runtime.GOOS != "linux" {
		return map[string]any{
			"safe_mode": "host_metrics_current",
			"status":    "unsupported",
			"detail":    "métricas de host disponíveis somente em Linux",
		}
	}
	if r.metrics.payload != nil && time.Since(r.metrics.collectedAt) < hostMetricsInterval {
		return r.metrics.payload
	}
	payload, network := collectHostMetrics(ctx, r.metrics.network, r.metrics.collectedAt)
	r.metrics.collectedAt = time.Now().UTC()
	r.metrics.payload = payload
	r.metrics.network = network
	return payload
}

func collectHostMetrics(ctx context.Context, previousNetwork networkCounters, previousAt time.Time) (map[string]any, networkCounters) {
	first := sampleProcesses()
	select {
	case <-ctx.Done():
	case <-time.After(hostMetricsCPUSampleWindow):
	}
	second := sampleProcesses()
	network := readNetworkCounters()
	payload := map[string]any{
		"safe_mode":        "host_metrics_current",
		"status":           "ok",
		"collected_at":     time.Now().UTC().Format(time.RFC3339),
		"interval_seconds": int(hostMetricsInterval.Seconds()),
		"host":             readHostMemory(),
		"network":          networkPayload(network, previousNetwork, previousAt),
		"services":         serviceMetricsPayload(first, second),
	}
	return sanitizeMap(payload), network
}

func sampleProcesses() map[int]processSample {
	entries, err := os.ReadDir("/proc")
	if err != nil {
		return map[int]processSample{}
	}
	totalTicks := readTotalCPUTicks()
	result := map[int]processSample{}
	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		pid, err := strconv.Atoi(entry.Name())
		if err != nil {
			continue
		}
		command := processCommand(pid)
		service := classifyService(command)
		if service == "" {
			continue
		}
		cpuTicks, _ := processCPUTicks(pid)
		rssBytes, vszBytes := processMemory(pid)
		result[pid] = processSample{
			pid:       pid,
			service:   service,
			command:   command,
			cpuTicks:  cpuTicks,
			rssBytes:  rssBytes,
			vszBytes:  vszBytes,
			totalTick: totalTicks,
		}
	}
	return result
}

func serviceMetricsPayload(first map[int]processSample, second map[int]processSample) []any {
	grouped := map[string]*serviceMetric{}
	for pid, current := range second {
		item := grouped[current.service]
		if item == nil {
			item = &serviceMetric{name: current.service, command: trimCommand(current.command), networkNote: "rede por processo não disponível via /proc; veja rede agregada do host"}
			grouped[current.service] = item
		}
		item.pids++
		item.rssBytes += current.rssBytes
		item.vszBytes += current.vszBytes
		if item.command == "" {
			item.command = trimCommand(current.command)
		}
		previous, ok := first[pid]
		if !ok || current.totalTick <= previous.totalTick || current.cpuTicks < previous.cpuTicks {
			continue
		}
		cpuDelta := float64(current.cpuTicks - previous.cpuTicks)
		totalDelta := float64(current.totalTick - previous.totalTick)
		item.cpuPercent += (cpuDelta / totalDelta) * float64(runtime.NumCPU()) * 100
	}
	order := []string{"printora-agent", "moonraker", "klipper", "crowsnest", "mainsail/nginx", "spoolman", "klipperscreen"}
	var services []any
	seen := map[string]bool{}
	for _, name := range order {
		if item := grouped[name]; item != nil {
			services = append(services, serviceMetricMap(item))
			seen[name] = true
		}
	}
	for name, item := range grouped {
		if !seen[name] {
			services = append(services, serviceMetricMap(item))
		}
	}
	return services
}

func serviceMetricMap(item *serviceMetric) map[string]any {
	return map[string]any{
		"name":         item.name,
		"command":      item.command,
		"pid_count":    item.pids,
		"cpu_percent":  roundMetric(item.cpuPercent),
		"rss_bytes":    item.rssBytes,
		"vsz_bytes":    item.vszBytes,
		"network_note": item.networkNote,
	}
}

func classifyService(command string) string {
	text := strings.ToLower(command)
	switch {
	case strings.Contains(text, "printora-agent"):
		return "printora-agent"
	case strings.Contains(text, "moonraker"):
		return "moonraker"
	case strings.Contains(text, "klippy") || strings.Contains(text, "klipper/klippy"):
		return "klipper"
	case strings.Contains(text, "crowsnest") || strings.Contains(text, "ustreamer") || strings.Contains(text, "camera-streamer"):
		return "crowsnest"
	case strings.Contains(text, "nginx") || strings.Contains(text, "mainsail"):
		return "mainsail/nginx"
	case strings.Contains(text, "spoolman"):
		return "spoolman"
	case strings.Contains(text, "klipperscreen"):
		return "klipperscreen"
	default:
		return ""
	}
}

func processCommand(pid int) string {
	data, err := os.ReadFile(filepath.Join("/proc", strconv.Itoa(pid), "cmdline"))
	if err == nil {
		text := strings.TrimSpace(strings.ReplaceAll(string(data), "\x00", " "))
		if text != "" {
			return text
		}
	}
	data, err = os.ReadFile(filepath.Join("/proc", strconv.Itoa(pid), "comm"))
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(data))
}

func processCPUTicks(pid int) (uint64, bool) {
	data, err := os.ReadFile(filepath.Join("/proc", strconv.Itoa(pid), "stat"))
	if err != nil {
		return 0, false
	}
	text := string(data)
	closeIndex := strings.LastIndex(text, ")")
	if closeIndex < 0 || closeIndex+2 >= len(text) {
		return 0, false
	}
	fields := strings.Fields(text[closeIndex+2:])
	if len(fields) < 13 {
		return 0, false
	}
	utime, err1 := strconv.ParseUint(fields[11], 10, 64)
	stime, err2 := strconv.ParseUint(fields[12], 10, 64)
	if err1 != nil || err2 != nil {
		return 0, false
	}
	return utime + stime, true
}

func processMemory(pid int) (uint64, uint64) {
	file, err := os.Open(filepath.Join("/proc", strconv.Itoa(pid), "status"))
	if err != nil {
		return 0, 0
	}
	defer file.Close()
	var rss uint64
	var vsz uint64
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		line := scanner.Text()
		switch {
		case strings.HasPrefix(line, "VmRSS:"):
			rss = parseStatusKB(line) * 1024
		case strings.HasPrefix(line, "VmSize:"):
			vsz = parseStatusKB(line) * 1024
		}
	}
	return rss, vsz
}

func readTotalCPUTicks() uint64 {
	data, err := os.ReadFile("/proc/stat")
	if err != nil {
		return 0
	}
	for _, line := range strings.Split(string(data), "\n") {
		if !strings.HasPrefix(line, "cpu ") {
			continue
		}
		var total uint64
		for _, field := range strings.Fields(line)[1:] {
			value, err := strconv.ParseUint(field, 10, 64)
			if err == nil {
				total += value
			}
		}
		return total
	}
	return 0
}

func readHostMemory() map[string]any {
	values := map[string]uint64{}
	data, err := os.ReadFile("/proc/meminfo")
	if err == nil {
		for _, line := range strings.Split(string(data), "\n") {
			parts := strings.SplitN(line, ":", 2)
			if len(parts) != 2 {
				continue
			}
			values[parts[0]] = parseStatusKB(parts[1]) * 1024
		}
	}
	total := values["MemTotal"]
	available := values["MemAvailable"]
	usedPercent := 0.0
	if total > 0 && available <= total {
		usedPercent = (float64(total-available) / float64(total)) * 100
	}
	return map[string]any{
		"memory_total_bytes":     total,
		"memory_available_bytes": available,
		"memory_used_percent":    roundMetric(usedPercent),
	}
}

func readNetworkCounters() networkCounters {
	data, err := os.ReadFile("/proc/net/dev")
	if err != nil {
		return networkCounters{}
	}
	var counters networkCounters
	for _, line := range strings.Split(string(data), "\n") {
		parts := strings.Split(line, ":")
		if len(parts) != 2 {
			continue
		}
		iface := strings.TrimSpace(parts[0])
		if iface == "" || iface == "lo" {
			continue
		}
		fields := strings.Fields(parts[1])
		if len(fields) < 16 {
			continue
		}
		rx, _ := strconv.ParseUint(fields[0], 10, 64)
		tx, _ := strconv.ParseUint(fields[8], 10, 64)
		counters.rxBytes += rx
		counters.txBytes += tx
	}
	return counters
}

func networkPayload(current networkCounters, previous networkCounters, previousAt time.Time) map[string]any {
	payload := map[string]any{
		"scope":    "host",
		"rx_bytes": current.rxBytes,
		"tx_bytes": current.txBytes,
	}
	if !previousAt.IsZero() {
		elapsed := time.Since(previousAt).Seconds()
		if elapsed > 0 && current.rxBytes >= previous.rxBytes && current.txBytes >= previous.txBytes {
			payload["rx_bytes_per_second"] = roundMetric(float64(current.rxBytes-previous.rxBytes) / elapsed)
			payload["tx_bytes_per_second"] = roundMetric(float64(current.txBytes-previous.txBytes) / elapsed)
		}
	}
	return payload
}

func parseStatusKB(line string) uint64 {
	for _, field := range strings.Fields(line) {
		value, err := strconv.ParseUint(field, 10, 64)
		if err == nil {
			return value
		}
	}
	return 0
}

func trimCommand(command string) string {
	fields := strings.Fields(command)
	if len(fields) == 0 {
		return ""
	}
	if len(fields) > 4 {
		fields = fields[:4]
	}
	return strings.Join(fields, " ")
}

func roundMetric(value float64) float64 {
	return float64(int(value*10+0.5)) / 10
}
