export type PrintProjectVisibility = "private" | "unlisted" | "public";
export type PrintProjectLifecycleStatus = "draft" | "active" | "archived";
export type PrintProjectPublicationStatus = "draft" | "in_review" | "approved" | "rejected" | "archived";
export type PrintProjectCommercialClass = "free" | "curated" | "premium" | "sponsored";
export type PrintProjectFileKind = "stl" | "3mf" | "zip" | "image" | "documentation" | "link" | "gcode" | "artifact";
export type PrintProjectFileRole = "primary" | "printable" | "optional_part" | "documentation" | "preview" | "external_reference" | "artifact";
export type PrintProjectFileValidationStatus = "metadata_only" | "quarantined" | "validated" | "rejected" | "analysis_failed";
export type PrintProjectFileSliceStatus = "eligible" | "blocked" | "external_no_local" | "pending" | "failure";

export interface PrintProjectContract {
  root_entity: string;
  relations: string[];
  visibility_values: string[];
  publication_values: string[];
  commercial_class_values: string[];
  file_kinds: string[];
  file_roles: string[];
  immutable_snapshot_required_for: string[];
  community_ownership_rule: string;
  external_link_rule: string;
  public_privacy_rule: string;
  legacy_surfaces: string[];
}

export interface PrintProjectFile {
  id: number;
  file_kind: PrintProjectFileKind;
  file_role: PrintProjectFileRole;
  file_name: string;
  external_url: string | null;
  size_bytes: number | null;
  sha256: string | null;
  validation_status: PrintProjectFileValidationStatus;
  can_slice: boolean;
  uploaded_size_bytes: number | null;
  rejection_reason: string | null;
  slice_status: PrintProjectFileSliceStatus;
}

export interface PrintProjectSummary {
  id: number;
  slug: string;
  title: string;
  description: string;
  visibility: PrintProjectVisibility;
  lifecycle_status: PrintProjectLifecycleStatus;
  publication_status: PrintProjectPublicationStatus;
  commercial_class: PrintProjectCommercialClass;
  license: string;
  original_author_name: string;
  source_url: string | null;
  primary_file: PrintProjectFile | null;
  file_count: number;
  printable_file_count: number;
  community_shares: string[];
  tags: string[];
  hosted_in_printora: boolean;
  external_reference_only: boolean;
  can_slice: boolean;
  created_at: string;
  updated_at: string;
}

export interface PrintProjectVersion {
  id: number;
  version_label: string;
  changelog: string;
  project_snapshot: Record<string, unknown>;
  files_snapshot: Array<Record<string, unknown>>;
  created_at: string;
}

export interface PrintProjectDetail extends PrintProjectSummary {
  files: PrintProjectFile[];
  versions: PrintProjectVersion[];
  saved_by_viewer: boolean;
  immutable_snapshot_ready: boolean;
}

export interface PrintProjectCreatePayload {
  title: string;
  description?: string;
  visibility?: PrintProjectVisibility;
  license?: string;
  original_author_name?: string;
  attribution_text?: string;
  source_url?: string | null;
  tags?: string[];
  material?: string;
  component?: string;
}

export interface PrintProjectUpdatePayload extends Partial<PrintProjectCreatePayload> {}

export interface PrintProjectExternalLinkPayload {
  url: string;
  label?: string;
  attribution_text?: string;
}

export interface PrintProjectStorageReport {
  quota_bytes: number;
  used_bytes: number;
  remaining_bytes: number;
  file_count: number;
  hosted_project_count: number;
  external_reference_count: number;
}
