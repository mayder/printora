export type MeshRepairOperation =
  | "clean"
  | "orient_normals"
  | "close_holes"
  | "remove_small_components"
  | "decimate"
  | "convert";

export type MeshRevisionStatus = "queued" | "processing" | "succeeded" | "failed" | "cancelled";

export interface MeshRevision {
  id: number;
  reconstruction_job_id: number;
  source_artifact_id: number;
  parent_revision_id: number | null;
  operation: MeshRepairOperation;
  parameters: Record<string, unknown>;
  status: MeshRevisionStatus;
  output_format: string | null;
  sha256: string | null;
  size_bytes: number | null;
  unit: string;
  manifest: Record<string, unknown>;
  qualification: {
    blockers?: string[];
    dimensions?: { x: number; y: number; z: number };
    checks?: Record<string, unknown>;
  };
  error_message: string | null;
  can_cancel: boolean;
  next_action: string;
  created_at: string;
  updated_at: string;
}

export interface MeshRepairRequest {
  operation: MeshRepairOperation;
  source_revision_id?: number;
  parameters: Record<string, unknown>;
}
