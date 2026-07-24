import { apiInput, apiRequest, apiResponse, getStoredAuthToken, getStoredStepUpToken, readApiError } from "./http";
import type { GcodeFileActionName, GcodeFileActionResponse, GcodeFileDetailResponse, GcodeFilesResponse, GcodeFileUploadResponse, GcodeManagerAction, GcodeManagerResponse } from "../types";

export type GcodeCacheEntry = {
  status: "cached";
  cache_key: string;
  printer_id: number;
  filename: string;
  size_bytes: number;
  sha256: string;
  created_at: string;
};

function withStepUp(body: unknown): unknown {
  const stepUpToken = getStoredStepUpToken();
  if (!stepUpToken || typeof body !== "object" || body === null || Array.isArray(body)) {
    return body;
  }
  return { ...body, step_up_token: stepUpToken };
}

export const operationApi = {
  status: (printerId: number) => apiResponse(`/api/printers/${printerId}/operation/status`),
  gcodeFiles: (
    printerId: number,
    options?: {
      refresh?: boolean;
      limit?: number;
      offset?: number;
      directory?: string;
      query?: string;
      sort?: "modified" | "name" | "size";
      direction?: "asc" | "desc";
      signal?: AbortSignal;
    },
  ) => {
    const params = new URLSearchParams();
    if (options?.refresh) params.set("refresh", "true");
    if (options?.limit) params.set("limit", String(options.limit));
    if (options?.offset) params.set("offset", String(options.offset));
    if (options?.directory) params.set("directory", options.directory);
    if (options?.query) params.set("query", options.query);
    if (options?.sort) params.set("sort", options.sort);
    if (options?.direction) params.set("direction", options.direction);
    const query = params.toString();
    return apiRequest<GcodeFilesResponse>(`/api/printers/${printerId}/gcode-files${query ? `?${query}` : ""}`, {
      signal: options?.signal,
    });
  },
  gcodeFileDetail: (printerId: number, filename: string) => {
    const params = new URLSearchParams({ filename });
    return apiRequest<GcodeFileDetailResponse>(`/api/printers/${printerId}/gcode-files/detail?${params.toString()}`);
  },
  gcodeFileAction: (
    printerId: number,
    body: {
      action: GcodeFileActionName;
      filename: string;
      target_filename?: string | null;
      confirmation_phrase?: string;
      step_up_token?: string | null;
    },
  ) =>
    apiRequest<GcodeFileActionResponse>(`/api/printers/${printerId}/gcode-files/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
  uploadGcodeFile: (
    printerId: number,
    file: File | Blob,
    options: {
      filename: string;
      startPrint?: boolean;
      overwrite?: boolean;
      confirmationPhrase?: string;
      onProgress?: (progress: number) => void;
    },
  ) =>
    new Promise<GcodeFileUploadResponse>((resolve, reject) => {
      const params = new URLSearchParams({
        filename: options.filename,
        start_print: String(Boolean(options.startPrint)),
        overwrite: String(Boolean(options.overwrite)),
      });
      const xhr = new XMLHttpRequest();
      xhr.open("POST", String(apiInput(`/api/printers/${printerId}/gcode-files/upload?${params.toString()}`)));
      xhr.setRequestHeader("Content-Type", "application/octet-stream");
      const authToken = getStoredAuthToken();
      const stepUpToken = getStoredStepUpToken();
      if (authToken) xhr.setRequestHeader("Authorization", `Bearer ${authToken}`);
      if (stepUpToken) xhr.setRequestHeader("X-Printora-Step-Up", stepUpToken);
      if (options.confirmationPhrase) xhr.setRequestHeader("X-Printora-Confirmation", options.confirmationPhrase);
      xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable) options.onProgress?.(Math.round((event.loaded / event.total) * 100));
      });
      xhr.addEventListener("load", () => {
        try {
          const payload = JSON.parse(xhr.responseText) as GcodeFileUploadResponse | { detail?: string };
          if (xhr.status < 200 || xhr.status >= 300) {
            reject(new Error("detail" in payload && payload.detail ? payload.detail : `Erro ${xhr.status}`));
            return;
          }
          resolve(payload as GcodeFileUploadResponse);
        } catch {
          reject(new Error(`Resposta inválida no envio do G-code (${xhr.status})`));
        }
      });
      xhr.addEventListener("error", () => reject(new Error("Falha de rede ao enviar o G-code")));
      xhr.addEventListener("abort", () => reject(new Error("Envio cancelado")));
      xhr.send(file);
    }),
  gcodeQueue: (printerId: number) =>
    apiRequest<GcodeManagerResponse>(`/api/printers/${printerId}/gcode-files/queue`),
  manageGcodeFiles: (
    printerId: number,
    body: {
      action: GcodeManagerAction;
      filename?: string;
      filenames?: string[];
      directory?: string;
      target_directory?: string;
      job_ids?: string[];
      hotend_temperature?: number;
      bed_temperature?: number;
      confirmation_phrase?: string;
      step_up_token?: string | null;
    },
  ) =>
    apiRequest<GcodeManagerResponse>(`/api/printers/${printerId}/gcode-files/manage`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
  actionHistory: (printerId: number) => apiResponse(`/api/printers/${printerId}/operation/actions/history`),
  executionHistory: (printerId: number) => apiResponse(`/api/printers/${printerId}/operation/actions/executions`),
  offlineFixture: () => apiResponse("/api/operation/fixtures/voron-offline"),
  ensureGcodeCache: (printerId: number, filename: string) =>
    apiRequest<GcodeCacheEntry>(`/api/printers/${printerId}/operation/gcode-cache`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename }),
    }),
  gcodeCacheText: async (printerId: number, cacheKey: string) => {
    const response = await apiResponse(`/api/printers/${printerId}/operation/gcode-cache/${encodeURIComponent(cacheKey)}`);
    if (!response.ok) {
      throw new Error(await readApiError(response));
    }
    return response.text();
  },
  preview: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/operation/actions/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
  preflight: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/operation/actions/preflight`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
  execute: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/operation/actions/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
  executeDirect: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/operation/actions/execute-direct`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(withStepUp(body)),
    }),
};
