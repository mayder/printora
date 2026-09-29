import { apiRequest, apiResponse, readApiError } from "./http";
import type { PhotoCaptureSession, PhotoHeightBand, PhotoScaleMethod } from "../types/photoCapture";

export const photoCaptureApi = {
  list: () => apiRequest<PhotoCaptureSession[]>("/api/photo-captures"),
  create: (projectId: number, targetPhotoCount = 24) =>
    apiRequest<PhotoCaptureSession>("/api/photo-captures", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ project_id: projectId, target_photo_count: targetPhotoCount, consent_confirmed: true }),
    }),
  upload: async (sessionId: number, file: File, captureIndex: number, heightBand: PhotoHeightBand) => {
    const query = new URLSearchParams({
      file_name: file.name,
      capture_index: String(captureIndex),
      height_band: heightBand,
    });
    const response = await apiResponse(`/api/photo-captures/${sessionId}/photos?${query}`, {
      method: "POST",
      headers: { "Content-Type": "application/octet-stream", "Idempotency-Key": `${sessionId}-${captureIndex}-${file.name}-${file.size}` },
      body: file,
    });
    if (!response.ok) throw new Error(await readApiError(response));
    return response.json() as Promise<PhotoCaptureSession>;
  },
  updateScale: (sessionId: number, method: PhotoScaleMethod, valueMm: number | null, uncertaintyMm: number | null) =>
    apiRequest<PhotoCaptureSession>(`/api/photo-captures/${sessionId}/scale`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ method, value_mm: valueMm, uncertainty_mm: uncertaintyMm }),
    }),
  complete: (sessionId: number) => apiRequest<PhotoCaptureSession>(`/api/photo-captures/${sessionId}/complete`, { method: "POST" }),
  cancel: (sessionId: number) => apiRequest<PhotoCaptureSession>(`/api/photo-captures/${sessionId}/cancel`, { method: "POST" }),
  exportBlob: async (sessionId: number) => {
    const response = await apiResponse(`/api/photo-captures/${sessionId}/export`);
    if (!response.ok) throw new Error(await readApiError(response));
    return response.blob();
  },
};
