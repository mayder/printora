import { apiResponse } from "./http";

export const updatesApi = {
  status: (printerId: number) => apiResponse(`/api/printers/${printerId}/updates/status`),
  refresh: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/updates/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  run: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/updates/run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
