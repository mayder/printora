-- Ordem: após 085_analytics_intelligence.sql.
-- Impacto: tabela aditiva, uma linha pequena por usuário; sem backfill ou lock de tabela existente.
-- Validação: consultar sqlite_master e repetir o script; constraints devem rejeitar valores inválidos.
-- Rollback: reverter consumidores e preservar tabela/dados; não executar DROP ou DELETE.
CREATE TABLE IF NOT EXISTS accessibility_preferences (
    user_id INTEGER PRIMARY KEY,
    theme TEXT NOT NULL DEFAULT 'system'
        CHECK(theme IN ('system','light','dark','high-contrast')),
    text_scale_percent INTEGER NOT NULL DEFAULT 100
        CHECK(text_scale_percent BETWEEN 100 AND 200),
    reduce_motion INTEGER NOT NULL DEFAULT 0 CHECK(reduce_motion IN (0,1)),
    screen_reader_announcements INTEGER NOT NULL DEFAULT 1
        CHECK(screen_reader_announcements IN (0,1)),
    keyboard_navigation INTEGER NOT NULL DEFAULT 1 CHECK(keyboard_navigation IN (0,1)),
    voice_navigation INTEGER NOT NULL DEFAULT 0 CHECK(voice_navigation IN (0,1)),
    captions INTEGER NOT NULL DEFAULT 1 CHECK(captions IN (0,1)),
    audio_descriptions INTEGER NOT NULL DEFAULT 0 CHECK(audio_descriptions IN (0,1)),
    simple_language INTEGER NOT NULL DEFAULT 0 CHECK(simple_language IN (0,1)),
    low_cognitive_load INTEGER NOT NULL DEFAULT 0 CHECK(low_cognitive_load IN (0,1)),
    three_d_text_alternative INTEGER NOT NULL DEFAULT 1
        CHECK(three_d_text_alternative IN (0,1)),
    tactile_format TEXT NOT NULL DEFAULT 'svg' CHECK(tactile_format IN ('svg','brf')),
    revision INTEGER NOT NULL DEFAULT 1 CHECK(revision > 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES auth_users(id) ON DELETE RESTRICT
);

