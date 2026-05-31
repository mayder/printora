export type MoonrakerStatus = {
  connected: boolean;
  moonraker_url: string;
  error?: string;
  printer?: {
    state?: string;
    state_message?: string;
    software_version?: string;
  };
  server?: {
    moonraker_version?: string;
    klippy_connected?: boolean;
    klippy_state?: string;
  };
};

export type DiscoveredPrinter = {
  name: string;
  moonraker_url: string;
  address: string;
  klippy_connected: boolean | null;
  klippy_state: string | null;
  moonraker_version: string | null;
  already_registered: boolean;
};

export type PrinterDiscoveryResponse = {
  cidr: string;
  safe_mode: string;
  scanned_hosts: number;
  candidates: DiscoveredPrinter[];
  warnings: string[];
};

export type ConnectionCheckResult = {
  ok: boolean;
  target: string;
  detail: string;
};

export type PrinterConnectionTestResponse = {
  safe_mode: string;
  moonraker: ConnectionCheckResult;
  ssh?: ConnectionCheckResult | null;
};

export type PrinterRecord = {
  id: number;
  name: string;
  moonraker_url: string;
  host_audit_mode: "disabled" | "local" | "ssh";
  host_audit_ssh_target?: string | null;
  ssh_host?: string | null;
  ssh_port?: number | null;
  ssh_username?: string | null;
  ssh_credential_configured: boolean;
  cloud_model?: string | null;
  cloud_tags: string[];
  cloud_status: "sem_agente" | "aguardando_pareamento" | "online" | "offline" | "degradado" | "revogado";
  active_agent_count: number;
  latest_agent_version?: string | null;
  latest_agent_last_seen_at?: string | null;
  latest_snapshot_at?: string | null;
  location?: string | null;
  notes?: string | null;
  owner_user_id?: number | null;
  organization_id?: number | null;
  is_active: boolean;
};

export type PairingTokenRecord = {
  id: number;
  printer_id: number;
  token_prefix: string;
  status: "active" | "used" | "revoked" | "expired" | "removed";
  expires_at: string;
  created_at: string;
  consumed_at?: string | null;
  revoked_at?: string | null;
  removed_at?: string | null;
};

export type PrinterAgentRecord = {
  id: number;
  printer_id: number;
  stable_id: string;
  credential_prefix: string;
  agent_version?: string | null;
  platform?: string | null;
  capabilities: Record<string, unknown>;
  status: "active" | "revoked" | "removed";
  paired_at: string;
  last_seen_at?: string | null;
  revoked_at?: string | null;
  removed_at?: string | null;
  rotated_at?: string | null;
};

export type AgentPairingOverview = {
  printer_id: number;
  pairing_tokens: PairingTokenRecord[];
  agents: PrinterAgentRecord[];
};

export type AgentInstallPlanResponse = {
  printer_id: number;
  token_id: number;
  token_prefix: string;
  expires_at: string;
  expected_agent_version: string;
  script_url: string;
  preflight_command: string;
  install_command: string;
  uninstall_command: string;
};

export type AgentInstallStatusResponse = {
  printer_id: number;
  expected_agent_version: string;
  ready: boolean;
  active_agents: number;
  latest_agent_id?: number | null;
  latest_stable_id?: string | null;
  latest_version?: string | null;
  latest_platform?: string | null;
  latest_last_seen_at?: string | null;
  diagnostic: string;
};

export type PairingTokenResponse = PairingTokenRecord & {
  token: string;
};

export type AgentCredentialExchangeResponse = {
  agent_id: number;
  printer_id: number;
  credential: string;
  credential_prefix: string;
  status: "active" | "revoked" | "removed";
};

export type AgentJobRecord = {
  id: number;
  printer_id: number;
  agent_id?: number | null;
  correlation_id: string;
  job_type: string;
  payload: Record<string, unknown>;
  status: "pending" | "in_progress" | "succeeded" | "failed" | "canceled";
  attempts: number;
  result?: Record<string, unknown> | null;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  acked_at?: string | null;
  finished_at?: string | null;
};

export type RemoteOperationAction = {
  action_id: string;
  label: string;
  risk: string;
  criticality: "low" | "high" | "critical";
  confirmation_required: boolean;
  blocks_when_printing: boolean;
  rollback_plan: string[];
};

export type RemoteOperationOverview = {
  printer_id: number;
  safe_mode: string;
  actions: RemoteOperationAction[];
  recent_jobs: AgentJobRecord[];
};

export type AgentSupportAlert = {
  severity: "info" | "warning" | "critical";
  code: string;
  title: string;
  detail: string;
  action: string;
};

export type AgentHealthSummary = {
  agent: PrinterAgentRecord;
  state: "online" | "offline" | "revoked" | "outdated" | "unknown";
  online: boolean;
  heartbeat_age_seconds?: number | null;
  expected_version: string;
  protocol_version?: number | null;
  protocol_compatible: boolean;
  pending_jobs: number;
  in_progress_jobs: number;
  failed_jobs_24h: number;
  latest_job?: AgentJobRecord | null;
  latest_failure?: AgentJobRecord | null;
  diagnostic: string;
};

export type AgentSupportOverview = {
  printer_id: number;
  safe_mode: string;
  generated_at: string;
  retention_days: number;
  agents: AgentHealthSummary[];
  alerts: AgentSupportAlert[];
  recent_events: Array<{
    id: number;
    printer_id: number;
    agent_id?: number | null;
    event_type: string;
    status: string;
    detail?: string | null;
    created_at: string;
  }>;
  latest_doctor?: AgentJobRecord | null;
};

export type AgentSupportBundle = {
  printer_id: number;
  safe_mode: string;
  generated_at: string;
  retention_policy: Record<string, unknown>;
  overview: AgentSupportOverview;
  recent_jobs: AgentJobRecord[];
  support_notes: string[];
};
