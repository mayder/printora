export type HealthResponse = {
  decision: "ok_para_imprimir" | "monitorar" | "nao_imprimir";
  counts: Record<string, number>;
};

export type CanBusSummary = {
  data_state: "manual_records" | "no_data";
  overall_alert: "ok" | "monitorar" | "problema";
  counts: Record<string, number>;
};

export type CanBusRecord = {
  id: number;
  interface_name: string;
  recorded_at: string;
  rx_error: number;
  tx_error: number;
  tx_retries: number;
  alert_level: "ok" | "monitorar" | "problema";
  diagnosis: string;
};

export type CanBusRecordComparison = {
  before_record_id: number;
  after_record_id: number;
  interface_name: string;
  delta_rx_error: number | null;
  delta_tx_error: number | null;
  delta_tx_retries: number | null;
  alert_level: "ok" | "monitorar" | "problema";
  diagnosis: string;
};
