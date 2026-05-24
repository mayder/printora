import { apiResponse } from "./http";

export const pluginApi = {
  audit: (printerId: number) => apiResponse(`/api/printers/${printerId}/plugins/audit`),
};
