export type MeshRepairOperation =
  | "clean"
  | "orient_normals"
  | "close_holes"
  | "remove_small_components"
  | "decimate"
  | "scale"
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

export interface MeshReviewRequest {
  decision: "approve" | "reject";
  intended_use: "decorative" | "prototype" | "mechanical";
  known_axis?: "x" | "y" | "z";
  known_dimension_mm?: number;
  shape_reviewed: boolean;
  limitations_accepted: boolean;
  note?: string;
}

export interface MeshRevisionReview {
  id: number;
  revision_id: number;
  reconstruction_job_id: number;
  decision: "approved_for_slicing" | "rejected";
  intended_use: "decorative" | "prototype" | "mechanical";
  known_axis: string | null;
  known_dimension_mm: number | null;
  model_dimension_mm: number | null;
  deviation_percent: number | null;
  revision_sha256: string;
  review_manifest: Record<string, unknown>;
  qualification: Record<string, unknown>;
  project_file_id: number | null;
  note: string;
  created_at: string;
}
