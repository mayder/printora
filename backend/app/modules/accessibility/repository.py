from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.database import connect_database
from app.modules.accessibility.contracts import AccessibilityPreferenceValues


class AccessibilityPreferencesConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class StoredAccessibilityPreferences:
    values: AccessibilityPreferenceValues
    revision: int
    updated_at: str


class AccessibilityPreferencesRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def get(self, user_id: int) -> StoredAccessibilityPreferences | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM accessibility_preferences WHERE user_id=?",
                (user_id,),
            ).fetchone()
        return _stored_from_row(row) if row is not None else None

    def save(
        self,
        user_id: int,
        values: AccessibilityPreferenceValues,
        expected_revision: int,
    ) -> StoredAccessibilityPreferences:
        with connect_database(self.database_path) as connection:
            current = connection.execute(
                "SELECT * FROM accessibility_preferences WHERE user_id=?",
                (user_id,),
            ).fetchone()
            if current is None:
                if expected_revision != 0:
                    raise AccessibilityPreferencesConflict("preferências foram alteradas")
                self._insert(connection, user_id, values)
            else:
                stored = _stored_from_row(current)
                if stored.revision != expected_revision:
                    raise AccessibilityPreferencesConflict("preferências foram alteradas")
                if stored.values == values:
                    return stored
                cursor = connection.execute(
                    _update_statement(),
                    (*_values_tuple(values), user_id, expected_revision),
                )
                if cursor.rowcount != 1:
                    raise AccessibilityPreferencesConflict("preferências foram alteradas")
            row = connection.execute(
                "SELECT * FROM accessibility_preferences WHERE user_id=?",
                (user_id,),
            ).fetchone()
        if row is None:
            raise RuntimeError("preferências não foram persistidas")
        return _stored_from_row(row)

    @staticmethod
    def _insert(connection, user_id: int, values: AccessibilityPreferenceValues) -> None:
        connection.execute(
            f"""
            INSERT INTO accessibility_preferences (
                user_id, {_column_names()}
            ) VALUES (?, {",".join("?" for _ in _values_tuple(values))})
            """,
            (user_id, *_values_tuple(values)),
        )


def _column_names() -> str:
    return (
        "theme, text_scale_percent, reduce_motion, screen_reader_announcements, "
        "keyboard_navigation, voice_navigation, captions, audio_descriptions, "
        "simple_language, low_cognitive_load, three_d_text_alternative, tactile_format"
    )


def _values_tuple(values: AccessibilityPreferenceValues) -> tuple[object, ...]:
    return (
        values.theme,
        values.text_scale_percent,
        int(values.reduce_motion),
        int(values.screen_reader_announcements),
        int(values.keyboard_navigation),
        int(values.voice_navigation),
        int(values.captions),
        int(values.audio_descriptions),
        int(values.simple_language),
        int(values.low_cognitive_load),
        int(values.three_d_text_alternative),
        values.tactile_format,
    )


def _update_statement() -> str:
    assignments = ", ".join(
        f"{name}=?" for name in _column_names().split(", ")
    )
    return f"""
        UPDATE accessibility_preferences
        SET {assignments}, revision=revision+1, updated_at=CURRENT_TIMESTAMP
        WHERE user_id=? AND revision=?
    """


def _stored_from_row(row) -> StoredAccessibilityPreferences:
    return StoredAccessibilityPreferences(
        values=AccessibilityPreferenceValues(
            theme=row["theme"],
            text_scale_percent=row["text_scale_percent"],
            reduce_motion=bool(row["reduce_motion"]),
            screen_reader_announcements=bool(row["screen_reader_announcements"]),
            keyboard_navigation=bool(row["keyboard_navigation"]),
            voice_navigation=bool(row["voice_navigation"]),
            captions=bool(row["captions"]),
            audio_descriptions=bool(row["audio_descriptions"]),
            simple_language=bool(row["simple_language"]),
            low_cognitive_load=bool(row["low_cognitive_load"]),
            three_d_text_alternative=bool(row["three_d_text_alternative"]),
            tactile_format=row["tactile_format"],
        ),
        revision=row["revision"],
        updated_at=str(row["updated_at"]),
    )

