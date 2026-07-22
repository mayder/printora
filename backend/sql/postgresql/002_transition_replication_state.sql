CREATE TABLE IF NOT EXISTS printora_transition_replication_state (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    watermark BIGINT NOT NULL DEFAULT 0 CHECK (watermark >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO printora_transition_replication_state (id, watermark)
VALUES (1, 0)
ON CONFLICT (id) DO NOTHING;

