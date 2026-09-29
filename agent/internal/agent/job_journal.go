package agent

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sync"
	"time"
)

const maxJobJournalEntries = 200

type JobJournalEntry struct {
	JobID         int            `json:"job_id"`
	CorrelationID string         `json:"correlation_id"`
	JobType       string         `json:"job_type"`
	State         string         `json:"state"`
	Result        map[string]any `json:"result,omitempty"`
	ErrorMessage  string         `json:"error_message,omitempty"`
	UpdatedAt     string         `json:"updated_at"`
}

type JobJournal struct {
	path string
	mu   sync.Mutex
}

func NewJobJournal(path string) *JobJournal {
	return &JobJournal{path: path}
}

func (journal *JobJournal) MarkReceived(job AgentJob) error {
	return journal.store(JobJournalEntry{
		JobID:         job.ID,
		CorrelationID: job.CorrelationID,
		JobType:       job.JobType,
		State:         "received",
	})
}

func (journal *JobJournal) Find(jobID int, correlationID string) (JobJournalEntry, bool) {
	if journal == nil || journal.path == "" {
		return JobJournalEntry{}, false
	}
	journal.mu.Lock()
	defer journal.mu.Unlock()
	entries, err := journal.load()
	if err != nil {
		return JobJournalEntry{}, false
	}
	for index := len(entries) - 1; index >= 0; index-- {
		entry := entries[index]
		if entry.JobID == jobID && entry.CorrelationID == correlationID {
			return entry, true
		}
	}
	return JobJournalEntry{}, false
}

func (journal *JobJournal) MarkStarted(job AgentJob) error {
	return journal.store(JobJournalEntry{
		JobID:         job.ID,
		CorrelationID: job.CorrelationID,
		JobType:       job.JobType,
		State:         "started",
	})
}

func (journal *JobJournal) MarkResult(job AgentJob, result map[string]any) error {
	return journal.store(JobJournalEntry{
		JobID:         job.ID,
		CorrelationID: job.CorrelationID,
		JobType:       job.JobType,
		State:         "succeeded",
		Result:        result,
	})
}

func (journal *JobJournal) MarkError(job AgentJob, message string, result map[string]any) error {
	return journal.store(JobJournalEntry{
		JobID:         job.ID,
		CorrelationID: job.CorrelationID,
		JobType:       job.JobType,
		State:         "failed",
		Result:        result,
		ErrorMessage:  message,
	})
}

func (journal *JobJournal) store(entry JobJournalEntry) error {
	if journal == nil || journal.path == "" {
		return nil
	}
	journal.mu.Lock()
	defer journal.mu.Unlock()
	entries, err := journal.load()
	if err != nil {
		return err
	}
	entry.UpdatedAt = time.Now().UTC().Format(time.RFC3339)
	replaced := false
	for index := range entries {
		if entries[index].JobID == entry.JobID && entries[index].CorrelationID == entry.CorrelationID {
			entries[index] = entry
			replaced = true
			break
		}
	}
	if !replaced {
		entries = append(entries, entry)
	}
	if len(entries) > maxJobJournalEntries {
		entries = entries[len(entries)-maxJobJournalEntries:]
	}
	return journal.replace(entries)
}

func (journal *JobJournal) load() ([]JobJournalEntry, error) {
	data, err := os.ReadFile(journal.path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var entries []JobJournalEntry
	if err := json.Unmarshal(data, &entries); err != nil {
		return nil, err
	}
	return entries, nil
}

func (journal *JobJournal) replace(entries []JobJournalEntry) error {
	if err := os.MkdirAll(filepath.Dir(journal.path), 0o700); err != nil {
		return err
	}
	data, err := json.Marshal(entries)
	if err != nil {
		return err
	}
	tempPath := journal.path + ".new"
	file, err := os.OpenFile(tempPath, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	if _, err := file.Write(append(data, '\n')); err != nil {
		_ = file.Close()
		_ = os.Remove(tempPath)
		return err
	}
	if err := file.Sync(); err != nil {
		_ = file.Close()
		_ = os.Remove(tempPath)
		return err
	}
	if err := file.Close(); err != nil {
		_ = os.Remove(tempPath)
		return err
	}
	if err := os.Rename(tempPath, journal.path); err != nil {
		_ = os.Remove(tempPath)
		return err
	}
	directory, err := os.Open(filepath.Dir(journal.path))
	if err != nil {
		return err
	}
	defer directory.Close()
	return directory.Sync()
}
