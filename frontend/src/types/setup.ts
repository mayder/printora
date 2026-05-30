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

export type SetupFlashMethod = "can_katapult" | "usb_dfu" | "manual";
export type SetupFlashStatus = SetupRunStatus | "blocked" | "requires_recovery";

export type SetupFlashFinding = {
  key: string;
  status: SetupFlashStatus;
  title: string;
  detail: string;
  action: string;
};

export type SetupFlashPreflightResponse = {
  safe_mode: string;
  connected: boolean;
  status: SetupFlashStatus;
  target: string;
  board_name: string;
  board_role: SetupFirmwareRole;
  flash_method: SetupFlashMethod;
  artifact_path: string;
  artifact_sha256?: string | null;
  expected_uuid?: string | null;
  summary: string;
  findings: SetupFlashFinding[];
  sections: Record<string, string>;
  parsed: Record<string, unknown>;
  rollback: string[];
  history_id?: number | null;
  error?: string | null;
};

export type SetupFlashPlanStep = {
  key: string;
  title: string;
  status: "ready" | "missing" | "manual" | "blocked";
  detail: string;
  commands: SetupCommandPlan[];
  rollback?: string | null;
};

export type SetupFlashPlanResponse = {
  safe_mode: string;
  status: SetupFlashStatus;
  target: string;
  board_name: string;
  board_role: SetupFirmwareRole;
  flash_method: SetupFlashMethod;
  artifact_path: string;
  artifact_sha256?: string | null;
  expected_uuid?: string | null;
  confirmation_phrase: string;
  summary: string;
  preflight: SetupFlashPreflightResponse;
  steps: SetupFlashPlanStep[];
  blocked_reasons: string[];
  rollback: string[];
  history_id?: number | null;
};

export type SetupFlashExecuteResponse = {
  safe_mode: string;
  status: SetupFlashStatus;
  target: string;
  board_name: string;
  board_role: SetupFirmwareRole;
  flash_method: SetupFlashMethod;
  artifact_path: string;
  artifact_sha256?: string | null;
  expected_uuid?: string | null;
  summary: string;
  command_log: string;
  duration_ms?: number | null;
  post_validation?: SetupFlashPreflightResponse | null;
  rollback: string[];
  blocked_reasons: string[];
  history_id?: number | null;
};

export type SetupFlashRunRecord = {
  id: number;
  run_type: "preflight" | "plan" | "flash";
  status: SetupFlashStatus;
  safe_mode: string;
  target_host: string;
  target_port: number;
  target_user: string;
  board_name: string;
  board_role: SetupFirmwareRole;
  flash_method: SetupFlashMethod;
  can_interface?: string | null;
  expected_uuid?: string | null;
  artifact_path: string;
  artifact_sha256?: string | null;
  previous_binary_path?: string | null;
  confirmation_phrase?: string | null;
  duration_ms?: number | null;
  summary: Record<string, unknown>;
  preflight?: Record<string, unknown> | null;
  plan?: Record<string, unknown> | null;
  command_log?: string | null;
  rollback: string[];
  error_message?: string | null;
  created_at: string;
};
