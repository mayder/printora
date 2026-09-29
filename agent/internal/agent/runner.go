package agent

import (
	"context"
	"log"
	"sync"
	"time"
)

type Runner struct {
	Config    Config
	API       *APIClient
	Moonraker *MoonrakerClient
	Queue     Queue
	Journal   *JobJournal
	Logger    *log.Logger
	startedAt time.Time
	metrics   hostMetricsCache
	jobsMu    sync.Mutex
	inFlight  map[int]struct{}
}

func (r *Runner) claimJob(jobID int) bool {
	r.jobsMu.Lock()
	defer r.jobsMu.Unlock()
	if r.inFlight == nil {
		r.inFlight = make(map[int]struct{})
	}
	if _, exists := r.inFlight[jobID]; exists {
		return false
	}
	r.inFlight[jobID] = struct{}{}
	return true
}

func (r *Runner) releaseJob(jobID int) {
	r.jobsMu.Lock()
	defer r.jobsMu.Unlock()
	delete(r.inFlight, jobID)
}

func NewRunner(cfg Config, credential string, logger *log.Logger) *Runner {
	return &Runner{
		Config:    cfg,
		API:       NewAPIClient(cfg.APIBaseURL, credential, Timeout(cfg)),
		Moonraker: NewMoonrakerClient(cfg.MoonrakerURL, Timeout(cfg)),
		Queue:     NewQueue(cfg.QueueFile),
		Journal:   NewJobJournal(cfg.JobJournalFile),
		Logger:    logger,
		startedAt: time.Now(),
	}
}

func (r *Runner) RunOnce(ctx context.Context) error {
	r.MaybeCheckAgentUpdate(ctx)
	if err := r.flushQueue(ctx); err != nil {
		r.Logger.Printf("queue flush pendente: %v", err)
	}
	heartbeat := HeartbeatPayload{
		AgentVersion: Version,
		Platform:     Platform(),
		Capabilities: r.capabilities(ctx, true),
	}
	if err := r.API.Heartbeat(ctx, heartbeat); err != nil {
		_ = r.Queue.Append(QueueItem{Type: "heartbeat", Payload: heartbeat.Capabilities})
		return err
	}
	snapshot := r.Moonraker.Snapshot(ctx)
	if err := r.API.Snapshot(ctx, SnapshotPayload{Payload: snapshot}); err != nil {
		_ = r.Queue.Append(QueueItem{Type: "snapshot", Payload: compactSnapshot(snapshot)})
		return err
	}
	return nil
}

func (r *Runner) HeartbeatOnly(ctx context.Context) error {
	r.MaybeCheckAgentUpdate(ctx)
	if err := r.flushQueue(ctx); err != nil {
		r.Logger.Printf("queue flush pendente: %v", err)
	}
	heartbeat := HeartbeatPayload{
		AgentVersion: Version,
		Platform:     Platform(),
		Capabilities: r.capabilities(ctx, false),
	}
	if err := r.API.Heartbeat(ctx, heartbeat); err != nil {
		_ = r.Queue.Append(QueueItem{Type: "heartbeat", Payload: heartbeat.Capabilities})
		return err
	}
	return nil
}

func (r *Runner) capabilities(ctx context.Context, includeSnapshot bool) map[string]any {
	capabilities := map[string]any{
		"heartbeat":    true,
		"read_only":    true,
		"uptime_s":     int(time.Since(r.startedAt).Seconds()),
		"protocol_v":   ProtocolVersion,
		"host_metrics": r.CachedHostMetrics(ctx),
	}
	if includeSnapshot {
		capabilities["snapshot"] = true
	}
	return capabilities
}

func (r *Runner) Run(ctx context.Context) error {
	if r.Config.WebSocketEnabled {
		go r.updateLoop(ctx)
		return r.RunChannel(ctx)
	}
	ticker := time.NewTicker(time.Duration(r.Config.IntervalSeconds) * time.Second)
	defer ticker.Stop()
	for {
		if err := r.RunOnce(ctx); err != nil {
			r.Logger.Printf("cycle failed: %v", err)
		}
		if r.Config.PollingEnabled {
			if err := r.PollJobsOnce(ctx); err != nil {
				r.Logger.Printf("polling failed: %v", err)
			}
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
		}
	}
}

func (r *Runner) updateLoop(ctx context.Context) {
	ticker := time.NewTicker(time.Duration(r.Config.UpdateCheckIntervalSeconds) * time.Second)
	defer ticker.Stop()
	r.MaybeCheckAgentUpdate(ctx)
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			r.MaybeCheckAgentUpdate(ctx)
		}
	}
}

func (r *Runner) flushQueue(ctx context.Context) error {
	items, err := r.Queue.Load()
	if err != nil || len(items) == 0 {
		return err
	}
	var pending []QueueItem
	for _, item := range items {
		switch item.Type {
		case "heartbeat":
			err = r.API.Heartbeat(ctx, HeartbeatPayload{AgentVersion: Version, Platform: Platform(), Capabilities: item.Payload})
		case "snapshot":
			err = r.API.Snapshot(ctx, SnapshotPayload{Payload: item.Payload})
		default:
			err = nil
		}
		if err != nil {
			pending = append(pending, item)
		}
	}
	return r.Queue.Replace(pending)
}

func compactSnapshot(snapshot map[string]any) map[string]any {
	result := map[string]any{"safe_mode": "read_only", "queued": true}
	for _, key := range []string{"server_info_error", "printer_info_error", "print_stats_error", "temperatures_error", "update_status_error"} {
		if value, ok := snapshot[key]; ok {
			result[key] = value
		}
	}
	return result
}
