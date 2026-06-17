import { apiRequest } from "./http";

export type SlicingEngineInfo = {
  engine: "orcaslicer" | "prusaslicer";
  status: "ready" | "blocked";
  configured_path: string | null;
  detected_path: string | null;
  version_text: string | null;
  warnings: string[];
  installation_hint: string;
  safe_mode: string;
};

export type SlicingJob = {
  id: number;
  owner_user_id: number | null;
  printer_id: number | null;
  material_profile_id: number | null;
  engine: "orcaslicer" | "prusaslicer";
  model_reference: string;
  model_version_reference: string;
  model_dimensions: Record<string, unknown>;
  quality_reference: string;
  status: "planned" | "running" | "completed" | "failed" | "canceled";
  compatibility: Record<string, unknown>;
  input: Record<string, any>;
  output: Record<string, any>;
  error_message: string | null;
  artifacts: Array<{
    id: number;
    artifact_kind: "gcode" | "log" | "metadata" | "preview";
    storage_key: string;
    checksum_sha256: string | null;
    size_bytes: number;
  }>;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  canceled_at: string | null;
};

export type PrintPreflight = {
  id: number;
  owner_user_id: number | null;
  printer_id: number;
  slicing_job_id: number;
  remote_agent_job_id: number | null;
  status: "approved" | "blocked" | "pending_remote" | "failed";
  local_metadata: Record<string, any>;
  remote_preflight: Record<string, any>;
  blockers: string[];
  warnings: string[];
  checklist: string[];
  created_at: string;
  updated_at: string;
  approved_at: string | null;
};

export type PrintDelivery = {
  id: number;
  owner_user_id: number | null;
  printer_id: number;
  slicing_job_id: number;
  preflight_id: number;
  remote_agent_job_id: number | null;
  rollback_agent_job_id: number | null;
  mode: "save_only" | "save_and_print";
  status: "pending_remote" | "saved" | "printing" | "blocked" | "failed" | "canceled" | "rollback_pending" | "rolled_back" | "rollback_failed";
  remote_filename: string;
  gcode_checksum_sha256: string;
  gcode_size_bytes: number;
  confirmation_phrase: string;
  confirmation_matched: boolean;
  preflight_snapshot: Record<string, any>;
  remote_result: Record<string, any>;
  rollback_result: Record<string, any>;
  blockers: string[];
  audit: Record<string, any>;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  canceled_at: string | null;
  rolled_back_at: string | null;
};

export type SlicingJobCreate = {
  printer_id: number;
  material_profile_id?: number | null;
  engine: "orcaslicer" | "prusaslicer";
  model_reference: string;
  model_version_reference?: string;
  model_dimensions: { x_mm?: number | null; y_mm?: number | null; z_mm?: number | null };
  quality_reference: string;
  profile_reference?: string | null;
};

export const slicingApi = {
  engine: () => apiRequest<SlicingEngineInfo>("/api/slicing/engine"),
  jobs: () => apiRequest<SlicingJob[]>("/api/slicing/jobs"),
  preflights: () => apiRequest<PrintPreflight[]>("/api/slicing/preflights"),
  deliveries: () => apiRequest<PrintDelivery[]>("/api/slicing/deliveries"),
  createJob: (body: SlicingJobCreate) =>
    apiRequest<SlicingJob>("/api/slicing/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  runJob: (jobId: number) => apiRequest<SlicingJob>(`/api/slicing/jobs/${jobId}/run`, { method: "POST" }),
  cancelJob: (jobId: number) => apiRequest<SlicingJob>(`/api/slicing/jobs/${jobId}/cancel`, { method: "POST" }),
  createPreflight: (jobId: number) => apiRequest<PrintPreflight>(`/api/slicing/jobs/${jobId}/preflight`, { method: "POST" }),
  refreshPreflight: (preflightId: number) => apiRequest<PrintPreflight>(`/api/slicing/preflights/${preflightId}/refresh`, { method: "POST" }),
  createDelivery: (body: { preflight_id: number; mode: "save_only" | "save_and_print"; confirmation_phrase?: string; step_up_token?: string | null }) =>
    apiRequest<PrintDelivery>("/api/slicing/deliveries", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  cancelDelivery: (deliveryId: number) => apiRequest<PrintDelivery>(`/api/slicing/deliveries/${deliveryId}/cancel`, { method: "POST" }),
  rollbackDelivery: (deliveryId: number) => apiRequest<PrintDelivery>(`/api/slicing/deliveries/${deliveryId}/rollback`, { method: "POST" }),
};
