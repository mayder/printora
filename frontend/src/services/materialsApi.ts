import { apiRequest } from "./http";
import type {
  MaterialCompatibilityResult,
  MaterialConsumption,
  MaterialQualitySample,
  MaterialSpool,
  MaterialSpoolPayload,
  SpoolmanSyncResult,
} from "../types";

const jsonHeaders = { "Content-Type": "application/json" };

export const materialsApi = {
  spools: () => apiRequest<MaterialSpool[]>("/api/materials/spools"),
  spool: (spoolId: number) => apiRequest<MaterialSpool>(`/api/materials/spools/${spoolId}`),
  createSpool: (payload: MaterialSpoolPayload) => apiRequest<MaterialSpool>("/api/materials/spools", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  }),
  updateSpool: (spoolId: number, payload: MaterialSpoolPayload & { revision: number }) =>
    apiRequest<MaterialSpool>(`/api/materials/spools/${spoolId}`, {
      method: "PUT",
      headers: jsonHeaders,
      body: JSON.stringify(payload),
    }),
  archiveSpool: (spoolId: number) => apiRequest<void>(`/api/materials/spools/${spoolId}`, { method: "DELETE" }),
  syncSpoolman: (printerId: number) => apiRequest<SpoolmanSyncResult>(`/api/materials/spoolman/sync/${printerId}`, { method: "POST" }),
  compatibility: (payload: {
    spool_id: number;
    printer_id: number;
    material_profile_id?: number | null;
    required_weight_g?: number | null;
    ventilation_confirmed?: boolean | null;
  }) => apiRequest<MaterialCompatibilityResult>("/api/materials/compatibility", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  }),
  consumptions: (spoolId: number) => apiRequest<MaterialConsumption[]>(`/api/materials/spools/${spoolId}/consumptions`),
  recordConsumption: (payload: {
    spool_id: number;
    idempotency_key: string;
    predicted_weight_g?: number | null;
    actual_weight_g?: number | null;
    status: "planned" | "confirmed" | "released";
    note?: string;
  }) => apiRequest<MaterialConsumption>("/api/materials/consumptions", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  }),
  quality: (spoolId: number) => apiRequest<MaterialQualitySample[]>(`/api/materials/spools/${spoolId}/quality`),
  createQuality: (payload: {
    spool_id: number;
    sample_type: "dimensional" | "calibration";
    metric_name: string;
    nominal_value_mm: number;
    measured_value_mm: number;
    tolerance_mm: number;
    note?: string;
  }) => apiRequest<MaterialQualitySample>("/api/materials/quality", {
    method: "POST",
    headers: jsonHeaders,
    body: JSON.stringify(payload),
  }),
};
