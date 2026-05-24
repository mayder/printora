import { apiResponse } from "./http";

export const backupApi = {
  policies: (printerId: number) => apiResponse(`/api/printers/${printerId}/backup/policies`),
  runs: (printerId: number) => apiResponse(`/api/printers/${printerId}/backup/runs`),
  createPolicy: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/backup/policies`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  executeLocal: (policyId: number) => apiResponse(`/api/backup/policies/${policyId}/execute-local`, { method: "POST" }),
  dryRun: (policyId: number) => apiResponse(`/api/backup/policies/${policyId}/dry-run`, { method: "POST" }),
  compareArchives: (body: unknown) =>
    apiResponse("/api/backup/archives/compare", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  restorePlan: (body: unknown) =>
    apiResponse("/api/backup/restore-plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  restoreGate: (body: unknown) =>
    apiResponse("/api/backup/restore-gate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
