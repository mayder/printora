import { apiResponse } from "./http";

export const printerApi = {
  list: () => apiResponse("/api/printers"),
  save: (printerId: number | null, body: unknown) =>
    apiResponse(printerId ? `/api/printers/${printerId}` : "/api/printers", {
      method: printerId ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  discover: () => apiResponse("/api/printers/discover"),
  testConnection: (body: unknown) =>
    apiResponse("/api/printers/test-connection", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  moonrakerStatus: (printerId: number) => apiResponse(`/api/printers/${printerId}/moonraker/status`),
  checklist: (printerId: number) => apiResponse(`/api/printers/${printerId}/checklist/post-update`),
  audit: (printerId: number) => apiResponse(`/api/printers/${printerId}/audit/read-only`),
  snapshots: (printerId: number) => apiResponse(`/api/printers/${printerId}/snapshots`),
  captureSnapshot: (printerId: number) =>
    apiResponse(`/api/printers/${printerId}/snapshots/moonraker`, { method: "POST" }),
  snapshotDiff: (printerId: number, fromSnapshotId: number, toSnapshotId: number) =>
    apiResponse(`/api/printers/${printerId}/snapshots/diff?from_id=${fromSnapshotId}&to_id=${toSnapshotId}`),
  health: (printerId: number) => apiResponse(`/api/printers/${printerId}/health`),
  networkDiagnostics: (printerId: number) => apiResponse(`/api/printers/${printerId}/network-diagnostics`),
  pairing: (printerId: number) => apiResponse(`/api/printers/${printerId}/pairing`),
  createPairingToken: (printerId: number, ttlMinutes = 15) =>
    apiResponse(`/api/printers/${printerId}/pairing/tokens`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ttl_minutes: ttlMinutes }),
    }),
  revokePairingToken: (printerId: number, tokenId: number) =>
    apiResponse(`/api/printers/${printerId}/pairing/tokens/${tokenId}/revoke`, { method: "POST" }),
  rotateAgentCredential: (printerId: number, agentId: number) =>
    apiResponse(`/api/printers/${printerId}/agents/${agentId}/rotate`, { method: "POST" }),
  revokeAgent: (printerId: number, agentId: number) =>
    apiResponse(`/api/printers/${printerId}/agents/${agentId}/revoke`, { method: "POST" }),
  agentInstallPlan: (printerId: number) =>
    apiResponse(`/api/printers/${printerId}/agent/install-plan`, { method: "POST" }),
  agentInstallStatus: (printerId: number) => apiResponse(`/api/printers/${printerId}/agent/install-status`),
  agentSupport: (printerId: number) => apiResponse(`/api/printers/${printerId}/agent/support`),
  createAgentDoctorJob: (printerId: number) =>
    apiResponse(`/api/printers/${printerId}/agent/support/doctor`, { method: "POST" }),
  agentSupportBundle: (printerId: number) => apiResponse(`/api/printers/${printerId}/agent/support/bundle`),
  remoteOperations: (printerId: number) => apiResponse(`/api/printers/${printerId}/remote/operations`),
  remoteOperationPreflight: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/remote/operations/preflight`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  remoteOperationExecute: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/remote/operations/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  cancelRemoteOperationJob: (printerId: number, jobId: number) =>
    apiResponse(`/api/printers/${printerId}/remote/operations/jobs/${jobId}/cancel`, { method: "POST" }),
};
