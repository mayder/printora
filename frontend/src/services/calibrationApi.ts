import { apiResponse, getStoredStepUpToken } from "./http";

function withStepUp(body: unknown): unknown {
  const stepUpToken = getStoredStepUpToken();
  if (!stepUpToken || typeof body !== "object" || body === null || Array.isArray(body)) {
    return body;
  }
  return { ...body, step_up_token: stepUpToken };
}

export const calibrationApi = {
  availableTests: (printerId?: number) =>
    apiResponse(printerId ? `/api/printers/${printerId}/calibration/available-tests` : "/api/calibration/tests"),
  runs: (printerId: number) => apiResponse(`/api/printers/${printerId}/calibration/runs`),
  summary: (printerId: number) => apiResponse(`/api/printers/${printerId}/calibration/summary`),
  sequence: (printerId: number) => apiResponse(`/api/printers/${printerId}/calibration/sequence`),
  executions: (printerId: number) => apiResponse(`/api/printers/${printerId}/calibration/executions`),
  createRun: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/calibration/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  preflight: (printerId: number, testKey: string) =>
    apiResponse(`/api/printers/${printerId}/calibration/tests/${encodeURIComponent(testKey)}/preflight`),
  execute: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/calibration/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  configRemediationPreview: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/calibration/config-remediation/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  configRemediationApply: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/calibration/config-remediation/apply`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
  deleteExecution: (printerId: number, attemptId: number) =>
    apiResponse(`/api/printers/${printerId}/calibration/executions/${attemptId}`, { method: "DELETE" }),
  deleteRun: (printerId: number, runId: number) =>
    apiResponse(`/api/printers/${printerId}/calibration/runs/${runId}`, { method: "DELETE" }),
};
