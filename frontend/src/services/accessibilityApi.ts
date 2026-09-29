import { apiRequest, apiResponse } from "./http";
import type {
  AccessibilityCatalog,
  AccessibilityPreferences,
  AccessibilityPreferenceValues,
} from "../types/accessibility";


export class AccessibilityConflictError extends Error {}

export const accessibilityApi = {
  catalog: () => apiRequest<AccessibilityCatalog>("/api/accessibility/v1/capabilities"),
  preferences: () => apiRequest<AccessibilityPreferences>("/api/accessibility/v1/preferences"),
  async save(
    values: AccessibilityPreferenceValues,
    expectedRevision: number,
  ): Promise<AccessibilityPreferences> {
    const response = await apiResponse("/api/accessibility/v1/preferences", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify({ ...values, expected_revision: expectedRevision }),
    });
    if (response.status === 409) {
      throw new AccessibilityConflictError("Preferências alteradas em outro dispositivo.");
    }
    if (!response.ok) {
      const payload = await response.json().catch(() => null) as { detail?: string } | null;
      throw new Error(payload?.detail || "Não foi possível sincronizar as preferências.");
    }
    return await response.json() as AccessibilityPreferences;
  },
};
