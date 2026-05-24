export type NetworkDiagnosticsResponse = {
  safe_mode: "read_only";
  printer_id: number;
  moonraker_url: string;
  host: string;
  dns: {
    ok: boolean;
    duration_ms?: number | null;
    addresses: string[];
    error?: string | null;
  };
  ping: {
    ok: boolean;
    packet_loss_percent?: number | null;
    rtt?: string | null;
    output?: string;
    error?: string;
  };
  configured_http: {
    ok: boolean;
    url: string;
    status_code?: number | null;
    total_ms?: number | null;
    error?: string | null;
  };
  direct_ip_http?: {
    ok: boolean;
    url: string;
    status_code?: number | null;
    total_ms?: number | null;
    error?: string | null;
  } | null;
  ssh?: {
    configured: boolean;
    ok: boolean;
    target: string;
    exit_code?: number | null;
    error?: string | null;
    moonraker_local_ms?: number | null;
    hostname?: string | null;
    wifi?: {
      connected: boolean;
      ssid?: string | null;
      signal?: string | null;
      tx_bitrate?: string | null;
      raw?: string;
    };
    addresses?: string[];
  } | null;
  recommendation: string;
};
