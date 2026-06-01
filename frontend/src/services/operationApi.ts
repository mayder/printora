import { apiResponse, getStoredStepUpToken } from "./http";

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
