export type BackupPolicyRecord = {
  id: number;
  printer_id: number;
  name: string;
  source_path: string;
  destination_path: string;
  include_patterns: string[];
  exclude_patterns: string[];
  dry_run_only: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type BackupRunRecord = {
  id: number;
  printer_id: number;
  policy_id: number;
  created_at: string;
  status: string;
  dry_run: boolean;
  source_path: string;
  destination_path: string;
  include_patterns: string[];
  exclude_patterns: string[];
  total_files: number;
  total_bytes: number;
  message: string;
};

export type BackupArchiveCompareResponse = {
  safe_mode: string;
  base_archive_path: string;
  target_archive_path: string;
  added: string[];
  removed: string[];
  changed: string[];
  unchanged_count: number;
  summary: string;
};

export type BackupRestorePlanResponse = {
  safe_mode: string;
  archive_path: string;
  restore_root: string;
  selected_files: string[];
  missing_files: string[];
  planned_commands: string[];
  blocked: boolean;
  message: string;
};

export type BackupRestoreGateResponse = {
  safe_mode: string;
  accepted_confirmation: boolean;
  blocked: boolean;
  plan: BackupRestorePlanResponse;
  rollback_plan: string[];
  message: string;
};
