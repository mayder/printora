export type CanBusRecord = {
  id: number;
  printer_id: number;
  recorded_at: string;
  interface_name: string;
  rx_error: number;
  tx_error: number;
  tx_retries: number;
  bus_state?: string | null;
  bitrate?: number | null;
  previous_rx_error?: number | null;
  previous_tx_error?: number | null;
  previous_tx_retries?: number | null;
  delta_rx_error?: number | null;
  delta_tx_error?: number | null;
  delta_tx_retries?: number | null;
  alert_level: "ok" | "monitorar" | "problema";
  diagnosis: string;
  recommended_actions: string[];
  notes: string;
  created_at: string;
};

export type CanBusSummary = {
  printer_id: number;
  safe_mode: string;
  data_state: "manual_records" | "no_data";
  source: string;
  counts: Record<string, number>;
  overall_alert: CanBusRecord["alert_level"];
  recommended_actions: string[];
  interfaces: Array<{
    interface_name: string;
    latest_alert: CanBusRecord["alert_level"];
    record_count: number;
    latest_recorded_at: string;
    rx_error: number;
    tx_error: number;
    tx_retries: number;
    delta_rx_error?: number | null;
    delta_tx_error?: number | null;
    delta_tx_retries?: number | null;
    diagnosis: string;
  }>;
};

export type CanBusRecordComparison = {
  safe_mode: string;
  printer_id: number;
  interface_name: string;
  before_record_id: number;
  after_record_id: number;
  delta_rx_error: number;
  delta_tx_error: number;
  delta_tx_retries: number;
  alert_level: CanBusRecord["alert_level"];
  diagnosis: string;
  recommended_actions: string[];
};
