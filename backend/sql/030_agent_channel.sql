CREATE TABLE IF NOT EXISTS agent_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    printer_id INTEGER NOT NULL,
    agent_id INTEGER,
    correlation_id TEXT NOT NULL,
    job_type TEXT NOT NULL,
    payload_json TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    result_json TEXT,
    error_message TEXT,
    available_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT,
    acked_at TEXT,
    finished_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(printer_id) REFERENCES printers(id) ON DELETE CASCADE,
    FOREIGN KEY(agent_id) REFERENCES printer_agents(id) ON DELETE SET NULL,
    UNIQUE(correlation_id)
);

CREATE INDEX IF NOT EXISTS idx_agent_jobs_printer_status ON agent_jobs(printer_id, status, available_at);
CREATE INDEX IF NOT EXISTS idx_agent_jobs_agent_status ON agent_jobs(agent_id, status, available_at);
CREATE INDEX IF NOT EXISTS idx_agent_jobs_correlation ON agent_jobs(correlation_id);
