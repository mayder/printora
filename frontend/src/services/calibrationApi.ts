import { apiResponse } from "./http";

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
};
