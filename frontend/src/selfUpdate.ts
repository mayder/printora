export type SelfUpdateStepRecord = {
  id: number;
  run_id: number;
  step_key: string;
  title: string;
  status: "pending" | "running" | "succeeded" | "failed" | "skipped";
  log_excerpt?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
};

export type SelfUpdateRunRecord = {
  id: number;
  target_version: string;
  target_tag: string;
  source_url?: string | null;
  environment: "android_termux" | "unix" | "windows" | "unknown";
  status: "planned" | "running" | "succeeded" | "failed" | "rolled_back";
  started_at?: string | null;
  finished_at?: string | null;
  backup_db_path?: string | null;
  backup_project_path?: string | null;
  previous_project_path?: string | null;
  current_project_path?: string | null;
  error_message?: string | null;
  created_at: string;
  steps: SelfUpdateStepRecord[];
};

export type SelfUpdatePlanResponse = {
  safe_mode: string;
  update_supported: boolean;
  can_apply: boolean;
  message: string;
  run: SelfUpdateRunRecord;
};

export type SelfUpdateApplyResponse = {
  accepted: boolean;
  message: string;
  run: SelfUpdateRunRecord;
  script_stdout?: string | null;
  script_stderr?: string | null;
};

export type SelfUpdateRollbackResponse = {
  accepted: boolean;
  message: string;
  source_run: SelfUpdateRunRecord;
  rollback_run: SelfUpdateRunRecord;
  script_stdout?: string | null;
  script_stderr?: string | null;
};

export type SelfUpdateHistoryResponse = {
  runs: SelfUpdateRunRecord[];
};

export function formatSelfUpdateEnvironment(environment: SelfUpdateRunRecord["environment"]) {
  const labels: Record<SelfUpdateRunRecord["environment"], string> = {
    android_termux: "Android/Termux",
    unix: "Unix/macOS/Linux",
    windows: "Windows",
    unknown: "desconhecido",
  };
  return labels[environment];
}

export function isSelfUpdateEnvironmentSupported(environment: SelfUpdateRunRecord["environment"]) {
  return environment === "android_termux" || environment === "unix" || environment === "windows";
}

export function canRollbackSelfUpdateRun(run: SelfUpdateRunRecord) {
  return run.status === "succeeded" && Boolean(run.previous_project_path);
}

export function formatSelfUpdateStatus(status: SelfUpdateRunRecord["status"]) {
  const labels: Record<SelfUpdateRunRecord["status"], string> = {
    planned: "planejado",
    running: "em execução",
    succeeded: "concluído",
    failed: "falhou",
    rolled_back: "rollback aplicado",
  };
  return labels[status];
}

export function formatSelfUpdateStepStatus(status: SelfUpdateStepRecord["status"]) {
  const labels: Record<SelfUpdateStepRecord["status"], string> = {
    pending: "pendente",
    running: "rodando",
    succeeded: "ok",
    failed: "falhou",
    skipped: "pulado",
  };
  return labels[status];
}

export function selfUpdateRunClass(status: SelfUpdateRunRecord["status"]) {
  if (status === "succeeded") return "up_to_date";
  if (status === "failed") return "warning";
  if (status === "running") return "update_available";
  return "";
}

export function selfUpdateStepClass(status: SelfUpdateStepRecord["status"]) {
  if (status === "succeeded") return "success";
  if (status === "failed") return "error";
  if (status === "running") return "warning";
  return "";
}
