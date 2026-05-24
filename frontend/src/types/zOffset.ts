export type ZOffsetRecord = {
  id: number;
  printer_id: number;
  recorded_at: string;
  plate_name: string;
  material: string;
  nozzle: string;
  offset_value: number;
  previous_offset_value?: number | null;
  delta_value?: number | null;
  alert_level: "ok" | "monitorar" | "revisar";
  notes: string;
  created_at: string;
};

export type ZOffsetWizardPlan = {
  safe_mode: string;
  plate_name: string;
  material: string;
  nozzle: string;
  proposed_offset_value: number;
  previous_offset_value?: number | null;
  delta_value?: number | null;
  alert_level: "ok" | "monitorar" | "revisar";
  recommendation: string;
  can_save_record: boolean;
  steps: Array<{
    key: string;
    title: string;
    detail: string;
    command?: string | null;
    must_confirm: boolean;
  }>;
};
