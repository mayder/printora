export type ReconstructionStatus = "queued" | "processing" | "succeeded" | "failed" | "cancelled";
export type ReconstructionEnginePolicy = "auto" | "local" | "provider";

export interface ReconstructionArtifact {
  id: number;
  artifact_type: "raw_mesh" | "preview" | "coverage";
  file_format: string;
  sha256: string;
  size_bytes: number;
  unit: string;
  observed_ratio: number | null;
  inferred_ratio: number | null;
  provenance: Record<string, unknown>;
}

export interface ReconstructionAttempt {
  id: number;
  attempt_number: number;
  engine_key: string;
  adapter_version: string;
  status: string;
  stage: string;
  estimated_cost_cents: number | null;
  actual_cost_cents: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface ReconstructionJob {
  id: number;
  capture_session_id: number;
  project_id: number;
  status: ReconstructionStatus;
  stage: string;
  progress_percent: number | null;
  engine_policy: ReconstructionEnginePolicy;
  engine_key: string | null;
  correlation_id: string;
  error_code: string | null;
  error_message: string | null;
  estimated_cost_cents: number | null;
  actual_cost_cents: number | null;
  can_cancel: boolean;
  can_retry: boolean;
  next_action: string;
  created_at: string;
  updated_at: string;
  attempts: ReconstructionAttempt[];
  artifacts: ReconstructionArtifact[];
}
