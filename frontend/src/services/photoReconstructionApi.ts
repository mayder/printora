import { apiRequest, apiResponse, readApiError } from "./http";
import type { ReconstructionEnginePolicy, ReconstructionJob } from "../types/photoReconstruction";

export const photoReconstructionApi = {
  list: (captureSessionId: number) =>
    apiRequest<ReconstructionJob[]>(`/api/photo-reconstructions?capture_session_id=${captureSessionId}`),
  create: (captureSessionId: number, policy: ReconstructionEnginePolicy) =>
    apiRequest<ReconstructionJob>("/api/photo-reconstructions", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Idempotency-Key": `capture-${captureSessionId}-${policy}`,
      },
      body: JSON.stringify({ capture_session_id: captureSessionId, engine_policy: policy }),
    }),
  get: (jobId: number) => apiRequest<ReconstructionJob>(`/api/photo-reconstructions/${jobId}`),
  cancel: (jobId: number) =>
    apiRequest<ReconstructionJob>(`/api/photo-reconstructions/${jobId}/cancel`, { method: "POST" }),
  retry: (jobId: number) =>
    apiRequest<ReconstructionJob>(`/api/photo-reconstructions/${jobId}/retry`, {
      method: "POST",
      headers: { "Idempotency-Key": `retry-${jobId}-${Date.now()}` },
    }),
  download: async (jobId: number, artifactId: number) => {
    const response = await apiResponse(`/api/photo-reconstructions/${jobId}/artifacts/${artifactId}`);
    if (!response.ok) throw new Error(await readApiError(response));
    return response.blob();
  },
};
