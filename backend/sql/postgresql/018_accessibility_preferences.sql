-- Execução privilegiada antes da release que consome o schema.
-- Impacto: DDL aditivo, sem backfill, exclusão ou alteração de tabela existente.
-- Validação: \d+ accessibility_preferences; repetir em transação e validar constraints.
-- Rollback: preservar tabela/dados e restaurar release N-1; não executar DROP ou DELETE.
CREATE TABLE IF NOT EXISTS accessibility_preferences (
    user_id BIGINT PRIMARY KEY REFERENCES auth_users(id) ON DELETE RESTRICT,
    theme TEXT NOT NULL DEFAULT 'system'
        CHECK(theme IN ('system','light','dark','high-contrast')),
    text_scale_percent BIGINT NOT NULL DEFAULT 100
        CHECK(text_scale_percent BETWEEN 100 AND 200),
    reduce_motion BIGINT NOT NULL DEFAULT 0 CHECK(reduce_motion IN (0,1)),
    screen_reader_announcements BIGINT NOT NULL DEFAULT 1
        CHECK(screen_reader_announcements IN (0,1)),
    keyboard_navigation BIGINT NOT NULL DEFAULT 1 CHECK(keyboard_navigation IN (0,1)),
    voice_navigation BIGINT NOT NULL DEFAULT 0 CHECK(voice_navigation IN (0,1)),
    captions BIGINT NOT NULL DEFAULT 1 CHECK(captions IN (0,1)),
    audio_descriptions BIGINT NOT NULL DEFAULT 0 CHECK(audio_descriptions IN (0,1)),
    simple_language BIGINT NOT NULL DEFAULT 0 CHECK(simple_language IN (0,1)),
    low_cognitive_load BIGINT NOT NULL DEFAULT 0 CHECK(low_cognitive_load IN (0,1)),
    three_d_text_alternative BIGINT NOT NULL DEFAULT 1
        CHECK(three_d_text_alternative IN (0,1)),
    tactile_format TEXT NOT NULL DEFAULT 'svg' CHECK(tactile_format IN ('svg','brf')),
    revision BIGINT NOT NULL DEFAULT 1 CHECK(revision > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

