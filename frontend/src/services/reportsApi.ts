import { apiResponse } from "./http";

export const reportsApi = {
  sanitized: (printerId: number) => apiResponse(`/api/printers/${printerId}/reports/sanitized`),
};
