import { apiRequest, apiResponse, readApiError } from "./http";
import type { MeshRepairRequest, MeshRevision } from "../types/meshRevision";

const basePath = (jobId: number) => `/api/photo-reconstructions/${jobId}/mesh-revisions`;

export const meshRevisionApi = {
  list: (jobId: number) => apiRequest<MeshRevision[]>(basePath(jobId)),
  get: (jobId: number, revisionId: number) =>
    apiRequest<MeshRevision>(`${basePath(jobId)}/${revisionId}`),
  create: (jobId: number, payload: MeshRepairRequest) =>
    apiRequest<MeshRevision>(basePath(jobId), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": `mesh-${jobId}-${crypto.randomUUID()}`,
      },
      body: JSON.stringify(payload),
    }),
  cancel: (jobId: number, revisionId: number) =>
    apiRequest<MeshRevision>(`${basePath(jobId)}/${revisionId}/cancel`, { method: "POST" }),
  download: async (jobId: number, revisionId: number) => {
    const response = await apiResponse(`${basePath(jobId)}/${revisionId}/download`);
    if (!response.ok) throw new Error(await readApiError(response));
    return response.blob();
  },
};
