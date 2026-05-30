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
