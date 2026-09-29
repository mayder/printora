import { apiRequest } from "./http";
import type {
  IntelligenceDashboard,
  IntelligenceModel,
  ModerationCase,
  RetentionPreview,
} from "../types/dataIntelligence";

export const dataIntelligenceApi = {
  dashboard: () => apiRequest<IntelligenceDashboard>("/api/admin/data-intelligence/dashboard"),
  moderation: () =>
    apiRequest<{ count: number; items: ModerationCase[] }>("/api/admin/data-intelligence/moderation"),
  retentionPreview: () =>
    apiRequest<RetentionPreview>("/api/admin/data-intelligence/retention/preview"),
  reviewCase: (caseKey: string, decision: "approved" | "rejected" | "closed", rationale: string) =>
    apiRequest<ModerationCase>(
      `/api/admin/data-intelligence/moderation/${encodeURIComponent(caseKey)}/review`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ decision, rationale }),
      },
    ),
  controlModel: (
    model: IntelligenceModel,
    changes: Pick<IntelligenceModel, "enabled" | "kill_switch" | "canary_percent" | "drift_score">,
  ) =>
    apiRequest<IntelligenceModel>(
      `/api/admin/data-intelligence/models/${encodeURIComponent(model.model_key)}/${encodeURIComponent(model.version)}/control`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(changes),
      },
    ),
};
