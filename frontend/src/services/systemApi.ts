import { apiResponse } from "./http";

export const systemApi = {
  releases: () => apiResponse("/api/system/releases"),
  updateHistory: () => apiResponse("/api/system/update/history"),
  reconcileUpdate: () => apiResponse("/api/system/update/reconcile", { method: "POST" }),
  planUpdate: (body: unknown) =>
    apiResponse("/api/system/update/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  applyUpdate: (body: unknown) =>
    apiResponse("/api/system/update/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  updateRun: (runId: number) => apiResponse(`/api/system/update/runs/${runId}`),
  rollbackUpdate: (body: unknown) =>
    apiResponse("/api/system/update/rollback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
