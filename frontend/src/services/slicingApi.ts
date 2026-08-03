import { apiRequest, apiResponse, readApiError } from "./http";

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
  slicing_profile_revision_id?: number | null;
  slicing_profile_sha256?: string | null;
  slicing_profile_engine_version?: string | null;
  engine: "orcaslicer" | "prusaslicer";
  model_reference: string;
  model_version_reference: string;
  model_dimensions: Record<string, unknown>;
  quality_reference: string;
  print_project_id?: number | null;
  print_project_version_id?: number | null;
  selected_project_files?: Array<Record<string, any>>;
  project_snapshot?: Record<string, any>;
  gcode_approved_at?: string | null;
  gcode_approved_checksum?: string | null;
  reprint_of_job_id?: number | null;
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

export type PrintJobFeedback = {
  id: number;
  history_id: number;
  outcome: "worked" | "failed" | "needs_adjustment";
  visibility: "private" | "public";
  note: string;
  photo_url: string | null;
  created_at: string;
  updated_at: string;
};

export type MeshPhysicalValidation = {
  id: number;
  review_id: number;
  history_id: number;
  outcome: "passed" | "needs_adjustment" | "failed";
  instrument_label: string;
  expected_dimensions_mm: Record<"x" | "y" | "z", number | null>;
  measured_dimensions_mm: Record<"x" | "y" | "z", number | null>;
  error_percent: Record<"x" | "y" | "z", number | null>;
  max_error_percent: number;
  printer_snapshot: Record<string, unknown>;
  material_snapshot: Record<string, unknown>;
  profile_snapshot: Record<string, unknown>;
  revision_sha256: string;
  note: string;
  created_at: string;
};

export type PrintJobHistory = {
  id: number;
  owner_user_id: number | null;
  printer_id: number | null;
  slicing_job_id: number | null;
  delivery_id: number | null;
  library_item_id: number | null;
  model_reference: string;
  model_version_reference: string;
  profile_reference: string | null;
  quality_reference: string;
  status: "sent" | "started" | "completed" | "failed" | "canceled";
  visibility: "private" | "public";
  telemetry: Record<string, any>;
  result: Record<string, any>;
  retention_days: number;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
  feedback: PrintJobFeedback[];
  mesh_physical_validation: MeshPhysicalValidation | null;
};

export type SlicingJobCreate = {
  printer_id: number;
  material_profile_id?: number | null;
  slicing_profile_revision_id?: number | null;
  engine: "orcaslicer" | "prusaslicer";
  model_reference: string;
  model_version_reference?: string;
  model_dimensions: { x_mm?: number | null; y_mm?: number | null; z_mm?: number | null };
  quality_reference: string;
  profile_reference?: string | null;
};

export type ProjectSlicingJobCreate = {
  project_id: number;
  selected_file_ids: number[];
  file_quantities?: Record<number, number>;
  printer_id: number;
  spool_id?: number | null;
  material_profile_id?: number | null;
  slicing_profile_revision_id?: number | null;
  engine: "orcaslicer" | "prusaslicer";
  model_dimensions: { x_mm?: number | null; y_mm?: number | null; z_mm?: number | null };
  quality_reference: string;
  profile_reference?: string | null;
};

export type NativeSlicingProfileBundle = {
  machine: Record<string, unknown>;
  process: Record<string, unknown>;
  filament: Record<string, unknown>;
};

export type SlicingProfileRevision = {
  id: number;
  bundle_id: number;
  revision_number: number;
  parent_revision_id: number | null;
  sha256: string;
  native_bundle: NativeSlicingProfileBundle;
  canonical: Record<string, unknown>;
  overrides: Record<string, unknown>;
  loss_report: string[];
  created_at: string;
};

export type SlicingProfileBundle = {
  id: number;
  title: string;
  engine: string;
  engine_version: string;
  schema_version: string;
  source_format: string;
  compatibility: Record<string, string>;
  current_revision_id: number | null;
  current_sha256: string | null;
  revisions: SlicingProfileRevision[];
  created_at: string;
  updated_at: string;
};

export type SlicingProfileImport = {
  title: string;
  engine_version: string;
  schema_version?: string;
  compatibility?: Record<string, string>;
  native_bundle: NativeSlicingProfileBundle;
  bundle_id?: number | null;
  parent_revision_id?: number | null;
};

export type SlicingProfileDiff = {
  from_revision_id: number;
  to_revision_id: number;
  added: Record<string, unknown>;
  changed: Record<string, { before: unknown; after: unknown }>;
  removed: Record<string, unknown>;
  loss_report: string[];
};

export const slicingApi = {
  engine: () => apiRequest<SlicingEngineInfo>("/api/slicing/engine"),
  jobs: () => apiRequest<SlicingJob[]>("/api/slicing/jobs"),
  preflights: () => apiRequest<PrintPreflight[]>("/api/slicing/preflights"),
  deliveries: () => apiRequest<PrintDelivery[]>("/api/slicing/deliveries"),
  history: () => apiRequest<PrintJobHistory[]>("/api/slicing/history"),
  profileBundles: () => apiRequest<SlicingProfileBundle[]>("/api/slicing/profile-bundles"),
  importProfileBundle: (body: SlicingProfileImport) =>
    apiRequest<SlicingProfileBundle>("/api/slicing/profile-bundles/import", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  exportProfileRevision: (revisionId: number) =>
    apiRequest<{ format: string; engine: string; sha256: string; native_bundle: NativeSlicingProfileBundle }>(
      `/api/slicing/profile-revisions/${revisionId}/export`,
    ),
  compareProfileRevisions: (fromRevisionId: number, toRevisionId: number) =>
    apiRequest<SlicingProfileDiff>(`/api/slicing/profile-revisions/${fromRevisionId}/diff/${toRevisionId}`),
  createJob: (body: SlicingJobCreate) =>
    apiRequest<SlicingJob>("/api/slicing/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  projectJobs: (projectId: number) => apiRequest<SlicingJob[]>(`/api/slicing/projects/${projectId}/jobs`),
  createProjectJob: (projectId: number, body: ProjectSlicingJobCreate) =>
    apiRequest<SlicingJob>(`/api/slicing/projects/${projectId}/jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  runJob: (jobId: number) => apiRequest<SlicingJob>(`/api/slicing/jobs/${jobId}/run`, { method: "POST" }),
  approvePreview: (jobId: number) => apiRequest<SlicingJob>(`/api/slicing/jobs/${jobId}/approve-preview`, { method: "POST" }),
  reprintJob: (jobId: number) => apiRequest<SlicingJob>(`/api/slicing/jobs/${jobId}/reprint`, { method: "POST" }),
  gcodeText: async (jobId: number) => {
    const response = await apiResponse(`/api/slicing/jobs/${jobId}/gcode`);
    if (!response.ok) throw new Error(await readApiError(response));
    return response.text();
  },
  cancelJob: (jobId: number) => apiRequest<SlicingJob>(`/api/slicing/jobs/${jobId}/cancel`, { method: "POST" }),
  createPreflight: (jobId: number) => apiRequest<PrintPreflight>(`/api/slicing/jobs/${jobId}/preflight`, { method: "POST" }),
  refreshPreflight: (preflightId: number) => apiRequest<PrintPreflight>(`/api/slicing/preflights/${preflightId}/refresh`, { method: "POST" }),
  createDelivery: (body: { preflight_id: number; mode: "save_only" | "save_and_print"; confirmation_phrase?: string; step_up_token?: string | null }) =>
    apiRequest<PrintDelivery>("/api/slicing/deliveries", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  cancelDelivery: (deliveryId: number) => apiRequest<PrintDelivery>(`/api/slicing/deliveries/${deliveryId}/cancel`, { method: "POST" }),
  rollbackDelivery: (deliveryId: number) => apiRequest<PrintDelivery>(`/api/slicing/deliveries/${deliveryId}/rollback`, { method: "POST" }),
  recordHistoryEvent: (historyId: number, body: { status: PrintJobHistory["status"]; telemetry?: Record<string, any>; result?: Record<string, any> }) =>
    apiRequest<PrintJobHistory>(`/api/slicing/history/${historyId}/events`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  addHistoryFeedback: (historyId: number, body: { outcome: PrintJobFeedback["outcome"]; visibility: PrintJobFeedback["visibility"]; note?: string; photo_url?: string | null }) =>
    apiRequest<PrintJobHistory>(`/api/slicing/history/${historyId}/feedback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  createMeshPhysicalValidation: (historyId: number, body: { outcome: MeshPhysicalValidation["outcome"]; instrument_label: string; measured_x_mm?: number; measured_y_mm?: number; measured_z_mm?: number; note?: string }) =>
    apiRequest<MeshPhysicalValidation>(`/api/slicing/history/${historyId}/mesh-physical-validation`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": `mesh-pilot-${historyId}-${crypto.randomUUID()}` },
      body: JSON.stringify(body),
    }),
};
