import { apiResponse, getStoredStepUpToken } from "./http";

const protectedHeaders = (stepUpToken?: string) => ({
  "Content-Type": "application/json",
  "X-Printora-Step-Up": stepUpToken ?? getStoredStepUpToken() ?? "",
});

export const updatesApi = {
  status: (printerId: number) => apiResponse(`/api/printers/${printerId}/updates/status`),
  refresh: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/updates/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  run: (printerId: number, body: unknown, stepUpToken?: string) =>
    apiResponse(`/api/printers/${printerId}/updates/run`, {
      method: "POST",
      headers: protectedHeaders(stepUpToken),
      body: JSON.stringify(body),
    }),
  rollback: (printerId: number, body: unknown, stepUpToken?: string) =>
    apiResponse(`/api/printers/${printerId}/updates/rollback`, {
      method: "POST",
      headers: protectedHeaders(stepUpToken),
      body: JSON.stringify(body),
    }),
  silence: (printerId: number, body: unknown, init?: RequestInit) =>
    apiResponse(`/api/printers/${printerId}/updates/silences`, {
      ...init,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  clearSilence: (printerId: number, body: unknown, init?: RequestInit) =>
    apiResponse(`/api/printers/${printerId}/updates/silences/clear`, {
      ...init,
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
