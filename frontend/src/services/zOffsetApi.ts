import { apiResponse } from "./http";

export const zOffsetApi = {
  list: (printerId: number) => apiResponse(`/api/printers/${printerId}/z-offsets`),
  create: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/z-offsets`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  wizardPlan: (printerId: number, query: URLSearchParams) =>
    apiResponse(`/api/printers/${printerId}/z-offsets/wizard-plan?${query.toString()}`),
};
