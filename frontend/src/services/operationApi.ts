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

const GCODE_CACHE_RETRY_DELAYS_MS = [1500, 3000, 6000] as const;
const RECOVERABLE_GCODE_CACHE_STATUSES = new Set([409, 425, 429, 500, 502, 503, 504, 524]);

class GcodeCacheRequestError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "GcodeCacheRequestError";
  }
}

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
  ensureGcodeCache: async (printerId: number, filename: string, signal?: AbortSignal) => {
    const response = await apiResponse(`/api/printers/${printerId}/operation/gcode-cache`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename }),
      signal,
    });
    if (!response.ok) {
      throw new GcodeCacheRequestError(await readApiError(response), response.status);
    }
    return response.json() as Promise<GcodeCacheEntry>;
  },
  gcodeCacheText: async (printerId: number, cacheKey: string, signal?: AbortSignal) => {
    const response = await apiResponse(`/api/printers/${printerId}/operation/gcode-cache/${encodeURIComponent(cacheKey)}`, {
      signal,
    });
    if (!response.ok) {
      throw new GcodeCacheRequestError(await readApiError(response), response.status);
    }
    return response.text();
  },
  gcodeCacheTextWithRecovery: async (
    printerId: number,
    filename: string,
    options?: {
      signal?: AbortSignal;
      onRetry?: (attempt: number, maximum: number) => void;
    },
  ) => {
    let lastError: unknown;
    for (let attempt = 0; attempt <= GCODE_CACHE_RETRY_DELAYS_MS.length; attempt += 1) {
      try {
        const cache = await operationApi.ensureGcodeCache(printerId, filename, options?.signal);
        return await operationApi.gcodeCacheText(printerId, cache.cache_key, options?.signal);
      } catch (error) {
        lastError = error;
        const delay = GCODE_CACHE_RETRY_DELAYS_MS[attempt];
        if (delay === undefined || !isRecoverableGcodeCacheError(error) || options?.signal?.aborted) {
          throw error;
        }
        options?.onRetry?.(attempt + 1, GCODE_CACHE_RETRY_DELAYS_MS.length);
        await waitForGcodeCacheRetry(delay, options?.signal);
      }
    }
    throw lastError;
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

function isRecoverableGcodeCacheError(error: unknown) {
  return (
    error instanceof TypeError ||
    (error instanceof GcodeCacheRequestError && RECOVERABLE_GCODE_CACHE_STATUSES.has(error.status))
  );
}

function waitForGcodeCacheRetry(delayMs: number, signal?: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    if (signal?.aborted) {
      reject(new DOMException("Operação cancelada", "AbortError"));
      return;
    }
    const handleAbort = () => {
      globalThis.clearTimeout(timeout);
      reject(new DOMException("Operação cancelada", "AbortError"));
    };
    const timeout = globalThis.setTimeout(() => {
      signal?.removeEventListener("abort", handleAbort);
      resolve();
    }, delayMs);
    signal?.addEventListener("abort", handleAbort, { once: true });
  });
}
