package agent

import (
	"bufio"
	"encoding/json"
	"os"
	"path/filepath"
	"time"
)

type QueueItem struct {
	Type      string         `json:"type"`
	CreatedAt string         `json:"created_at"`
	Payload   map[string]any `json:"payload"`
}

type Queue struct {
	path string
}

func NewQueue(path string) Queue {
	return Queue{path: path}
}

func (q Queue) Append(item QueueItem) error {
	if q.path == "" {
		return nil
	}
	if item.CreatedAt == "" {
		item.CreatedAt = time.Now().UTC().Format(time.RFC3339)
	}
	if err := os.MkdirAll(filepath.Dir(q.path), 0o700); err != nil {
		return err
	}
	file, err := os.OpenFile(q.path, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	defer file.Close()
	data, err := json.Marshal(item)
	if err != nil {
		return err
	}
	if _, err := file.Write(append(data, '\n')); err != nil {
		return err
	}
	return q.trim(200)
}

func (q Queue) Load() ([]QueueItem, error) {
	if q.path == "" {
		return nil, nil
	}
	file, err := os.Open(q.path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	defer file.Close()
	var items []QueueItem
	scanner := bufio.NewScanner(file)
	for scanner.Scan() {
		var item QueueItem
		if err := json.Unmarshal(scanner.Bytes(), &item); err == nil {
			items = append(items, item)
		}
	}
	return items, scanner.Err()
}

func (q Queue) Replace(items []QueueItem) error {
	if q.path == "" {
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(q.path), 0o700); err != nil {
		return err
	}
	file, err := os.OpenFile(q.path, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	defer file.Close()
	for _, item := range items {
		data, err := json.Marshal(item)
		if err != nil {
			return err
		}
		if _, err := file.Write(append(data, '\n')); err != nil {
			return err
		}
	}
	return nil
}

func (q Queue) trim(maxItems int) error {
	items, err := q.Load()
	if err != nil || len(items) <= maxItems {
		return err
	}
	return q.Replace(items[len(items)-maxItems:])
}
