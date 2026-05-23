import { apiResponse } from "./http";

export const canApi = {
  records: (printerId: number) => apiResponse(`/api/printers/${printerId}/can/records`),
  summary: (printerId: number) => apiResponse(`/api/printers/${printerId}/can/summary`),
  createRecord: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/can/records`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  parse: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/can/parse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  compare: (printerId: number, params: URLSearchParams) =>
    apiResponse(`/api/printers/${printerId}/can/compare?${params.toString()}`),
};
