export type ReleaseRecord = {
  tag: string;
  name: string;
  channel: string;
  changelog: string;
  changelog_summary: string;
  url?: string | null;
  published_at?: string | null;
  prerelease: boolean;
  draft: boolean;
  installed: boolean;
};

export type SystemReleasesResponse = {
  safe_mode: string;
  source: "github" | "fixture" | "disabled";
  status: "ok" | "offline" | "rate_limited" | "disabled" | "error";
  channel: string;
  installed_version: string;
  update_status: "up_to_date" | "outdated" | "unknown";
  latest_release_available: boolean;
  latest_release?: ReleaseRecord | null;
  releases: ReleaseRecord[];
  update_supported: boolean;
  message: string;
  error?: string | null;
};

export type UpdateActionResponse = {
  safe_mode: string;
  action: "refresh" | "update" | "rollback";
  target: string;
  accepted: boolean;
  message: string;
  result: Record<string, unknown>;
};

export type UpdateLogEntry = {
  id: number;
  time: string;
  level: "info" | "success" | "warning" | "error";
  message: string;
};

export type UpdateDialogState = {
  open: boolean;
  target: string;
  label: string;
  action: "update" | "rollback";
  phase: "confirm" | "running" | "done" | "failed";
  requiresConfirmation: boolean;
  confirmationPhrase: string;
  riskReason?: string | null;
};
