from __future__ import annotations

from app.modules.accessibility.contracts import (
    AccessibilityPreferenceValues,
    AccessibilityPreferencesContract,
    AccessibilityPreferencesUpdateRequest,
)
from app.modules.accessibility.repository import AccessibilityPreferencesRepository


class AccessibilityPreferencesService:
    def __init__(self, repository: AccessibilityPreferencesRepository):
        self.repository = repository

    def get(self, user_id: int) -> AccessibilityPreferencesContract:
        stored = self.repository.get(user_id)
        if stored is None:
            return AccessibilityPreferencesContract(
                **AccessibilityPreferenceValues().model_dump(),
                revision=0,
            )
        return AccessibilityPreferencesContract(
            **stored.values.model_dump(),
            revision=stored.revision,
            updated_at=stored.updated_at,
        )

    def save(
        self,
        user_id: int,
        request: AccessibilityPreferencesUpdateRequest,
    ) -> AccessibilityPreferencesContract:
        values = AccessibilityPreferenceValues.model_validate(
            request.model_dump(exclude={"expected_revision"})
        )
        stored = self.repository.save(user_id, values, request.expected_revision)
        return AccessibilityPreferencesContract(
            **stored.values.model_dump(),
            revision=stored.revision,
            updated_at=stored.updated_at,
        )

