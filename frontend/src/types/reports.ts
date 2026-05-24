export type SanitizedReport = {
  printer_id: number;
  safe_mode: string;
  format: "markdown";
  data_state: string;
  source: string;
  redactions: string[];
  markdown: string;
};
