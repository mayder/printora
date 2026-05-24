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
  location?: string | null;
  notes?: string | null;
  is_active: boolean;
};
