export type SetupRunStatus = "ok" | "warning" | "error";
export type SetupAuthMethod = "agent" | "key_path";

export type SetupSshTarget = {
  host: string;
  port: number;
  username: string;
  auth_method: SetupAuthMethod;
  key_path?: string | null;
  timeout_seconds: number;
};

export type SetupCheckItem = {
  key: string;
  label: string;
  status: SetupRunStatus;
  detail: string;
};

export type SetupCommandPlan = {
  command: string;
  risk: "read_only" | "mutable" | "manual";
  reason: string;
};

export type SetupPlanStep = {
  key: string;
  title: string;
  status: "ready" | "missing" | "manual" | "blocked";
  detail: string;
  commands: SetupCommandPlan[];
  rollback?: string | null;
};

export type SetupSshPreflightResponse = {
  safe_mode: string;
  connected: boolean;
  status: SetupRunStatus;
  target: string;
  summary: string;
  checks: SetupCheckItem[];
  sections: Record<string, string>;
  redacted_target: Record<string, unknown>;
  history_id?: number | null;
  error?: string | null;
};

export type SetupSshPlanResponse = {
  safe_mode: string;
  status: SetupRunStatus;
  target: string;
  summary: string;
  preflight: SetupSshPreflightResponse;
  steps: SetupPlanStep[];
  blocked_reasons: string[];
  history_id?: number | null;
};

export type SetupSshRunRecord = {
  id: number;
  run_type: "preflight" | "plan";
  status: SetupRunStatus;
  safe_mode: string;
  target_host: string;
  target_port: number;
  target_user: string;
  auth_method: SetupAuthMethod;
  summary: Record<string, unknown>;
  plan?: Record<string, unknown> | null;
  error_message?: string | null;
  created_at: string;
};

export type SetupCanFinding = {
  key: string;
  status: SetupRunStatus | "blocked";
  title: string;
  detail: string;
  action: string;
};

export type SetupCanPreflightResponse = {
  safe_mode: string;
  connected: boolean;
  status: SetupRunStatus | "blocked";
  target: string;
  interface_name: string;
  bitrate: number;
  summary: string;
  findings: SetupCanFinding[];
  sections: Record<string, string>;
  parsed: Record<string, unknown>;
  history_id?: number | null;
  error?: string | null;
};

export type SetupCanPlanStep = {
  key: string;
  title: string;
  status: "ready" | "missing" | "manual" | "blocked";
  detail: string;
  commands: SetupCommandPlan[];
  rollback?: string | null;
};

export type SetupCanPlanResponse = {
  safe_mode: string;
  status: SetupRunStatus | "blocked";
  target: string;
  interface_name: string;
  bitrate: number;
  summary: string;
  preflight: SetupCanPreflightResponse;
  steps: SetupCanPlanStep[];
  blocked_reasons: string[];
  history_id?: number | null;
};

export type SetupCanApplyResponse = {
  safe_mode: string;
  status: SetupRunStatus | "blocked";
  target: string;
  interface_name: string;
  bitrate: number;
  summary: string;
  command_log: string;
  validation?: SetupCanPreflightResponse | null;
  history_id?: number | null;
  blocked_reasons: string[];
};

export type SetupCanRunRecord = {
  id: number;
  run_type: "preflight" | "plan" | "apply";
  status: SetupRunStatus | "blocked";
  safe_mode: string;
  target_host: string;
  target_port: number;
  target_user: string;
  interface_name: string;
  bitrate: number;
  summary: Record<string, unknown>;
  plan?: Record<string, unknown> | null;
  command_log?: string | null;
  error_message?: string | null;
  created_at: string;
};

export type SetupFirmwareRole = "mainboard" | "toolhead" | "can_adapter" | "unknown";

export type SetupFirmwarePlanStep = {
  key: string;
  title: string;
  status: "ready" | "missing" | "manual" | "blocked";
  detail: string;
  commands: SetupCommandPlan[];
  rollback?: string | null;
};

export type SetupFirmwarePlanResponse = {
  safe_mode: string;
  status: SetupRunStatus | "blocked";
  target: string;
  preset_id: string;
  board_name: string;
  board_role: SetupFirmwareRole;
  summary: string;
  config_preview: string;
  config_sha256: string;
  artifact_dir: string;
  expected_binary_path: string;
  steps: SetupFirmwarePlanStep[];
  blocked_reasons: string[];
  history_id?: number | null;
};

export type SetupFirmwareBuildResponse = {
  safe_mode: string;
  status: SetupRunStatus | "blocked";
  target: string;
  preset_id: string;
  board_name: string;
  board_role: SetupFirmwareRole;
  summary: string;
  artifact_dir?: string | null;
  config_path?: string | null;
  binary_path?: string | null;
  config_sha256?: string | null;
  binary_sha256?: string | null;
  uuid_query: string[];
  command_log: string;
  blocked_reasons: string[];
  history_id?: number | null;
};

export type SetupFirmwareRunRecord = {
  id: number;
  run_type: "plan" | "build";
  status: SetupRunStatus | "blocked";
  safe_mode: string;
  target_host: string;
  target_port: number;
  target_user: string;
  board_name: string;
  board_role: SetupFirmwareRole;
  preset_id: string;
  can_interface: string;
  config_path?: string | null;
  artifact_dir?: string | null;
  binary_path?: string | null;
  config_sha256?: string | null;
  binary_sha256?: string | null;
  uuid_query: string[];
  summary: Record<string, unknown>;
  plan?: Record<string, unknown> | null;
  command_log?: string | null;
  error_message?: string | null;
  created_at: string;
};
