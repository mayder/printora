export type IntelligenceCount = { status: string; total: number };
export type IntelligenceMetric = {
  metric_name: string;
  dimension_key: string;
  samples: number;
  average_value: number;
  latest_bucket: string;
};
export type IntelligenceModel = {
  model_key: string;
  version: string;
  owner: string;
  dataset_name: string;
  dataset_version: string;
  dataset_license: string;
  metrics: Record<string, unknown>;
  bias_assessment: Record<string, unknown>;
  canary_percent: number;
  drift_score: number;
  drift_threshold: number;
  enabled: boolean;
  kill_switch: boolean;
  fallback_strategy: string;
  rollback_version: string | null;
};
export type IntelligenceLineage = {
  source_event_id: string;
  derivative_type: string;
  derivative_key: string;
  transformation_version: string;
  output_sha256: string;
  created_at: string;
};
export type IntelligenceDashboard = {
  pipeline: IntelligenceCount[];
  impact: IntelligenceMetric[];
  moderation: IntelligenceCount[];
  models: IntelligenceModel[];
  temporary_records: number;
  lineage: IntelligenceLineage[];
  replays: Array<Record<string, unknown>>;
  isolation: {
    source: string;
    oltp_writes: boolean;
    transformation_version: string;
  };
};
export type ModerationCase = {
  case_key: string;
  entity_type: string;
  detected_language: string;
  confidence: number;
  labels: string[];
  human_review_required: number;
  status: string;
  rationale: string | null;
  created_at: string;
};
export type RetentionPreview = {
  mode: "preview_only";
  policies: Array<Record<string, unknown>>;
  expired: Array<Record<string, unknown>>;
  data_deleted: false;
};
