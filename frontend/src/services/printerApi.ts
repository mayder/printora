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
};
