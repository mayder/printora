import { apiRequest, apiResponse, getStoredStepUpToken, readApiError } from "./http";

export type GcodeCacheEntry = {
  status: "cached";
  cache_key: string;
  printer_id: number;
  filename: string;
  size_bytes: number;
  sha256: string;
  created_at: string;
};

function withStepUp(body: unknown): unknown {
  const stepUpToken = getStoredStepUpToken();
  if (!stepUpToken || typeof body !== "object" || body === null || Array.isArray(body)) {
    return body;
  }
  return { ...body, step_up_token: stepUpToken };
}

export const operationApi = {
  status: (printerId: number) => apiResponse(`/api/printers/${printerId}/operation/status`),
  actionHistory: (printerId: number) => apiResponse(`/api/printers/${printerId}/operation/actions/history`),
  executionHistory: (printerId: number) => apiResponse(`/api/printers/${printerId}/operation/actions/executions`),
  offlineFixture: () => apiResponse("/api/operation/fixtures/voron-offline"),
  ensureGcodeCache: (printerId: number, filename: string) =>
    apiRequest<GcodeCacheEntry>(`/api/printers/${printerId}/operation/gcode-cache`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename }),
    }),
  gcodeCacheText: async (printerId: number, cacheKey: string) => {
    const response = await apiResponse(`/api/printers/${printerId}/operation/gcode-cache/${encodeURIComponent(cacheKey)}`);
    if (!response.ok) {
      throw new Error(await readApiError(response));
    }
    return response.text();
  },
  preview: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/operation/actions/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
  preflight: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/operation/actions/preflight`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
  execute: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/operation/actions/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
  executeDirect: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/operation/actions/execute-direct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
};
