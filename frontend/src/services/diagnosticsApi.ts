import { apiResponse } from "./http";

export const diagnosticsApi = {
  moonrakerStatus: () => apiResponse("/api/moonraker/status"),
  postUpdateChecklist: () => apiResponse("/api/checklist/post-update"),
  hostReadOnlyAudit: () => apiResponse("/api/audit/host-read-only"),
};
