export type CalibrationTestRecord = {
  id: number;
  test_key: string;
  category: string;
  title: string;
  objective: string;
  source: string;
  execution_mode: "read_only" | "manual" | "gcode_review_required" | "blocked_while_printing";
  risk_level: "low" | "medium" | "high";
  blocked_while_printing: boolean;
  prerequisites: string[];
  gcode: string[];
  success_criteria: string[];
  notes: string;
  sort_order: number;
};

export type CalibrationAvailableTestsResponse = {
  safe_mode: string;
  printer_id: number;
  data_state: "live" | "offline";
  tests: CalibrationTestRecord[];
  hidden_tests: Array<{
    test_key: string;
    title: string;
    reason: string;
  }>;
};

export type CalibrationRunRecord = {
  id: number;
  printer_id: number;
  test_key: string;
  test_title: string;
  created_at: string;
  result_status: "passed" | "warning" | "failed" | "skipped";
  material: string;
  plate_name: string;
  nozzle: string;
  observed_value: string;
  notes: string;
  gcode_reviewed: boolean;
  photo_reference?: string | null;
};

export type CalibrationResultFormConfig = {
  summary: string;
  observedLabel: string;
  observedPlaceholder: string;
  notesLabel: string;
  notesPlaceholder: string;
  showMaterial: boolean;
  showPlate: boolean;
  showNozzle: boolean;
};

export type CalibrationSummary = {
  printer_id: number;
  safe_mode: string;
  catalog_count: number;
  run_count: number;
  category_counts: Record<string, number>;
  risk_counts: Record<string, number>;
  execution_mode_counts: Record<string, number>;
  result_counts: Record<string, number>;
  blocked_while_printing_count: number;
  gcode_review_required_count: number;
  latest_runs: CalibrationRunRecord[];
  recommended_next_tests: Array<{
    test_key: string;
    title: string;
    category: string;
    risk_level: CalibrationTestRecord["risk_level"];
    reason: string;
  }>;
};

export type CalibrationSequencePlan = {
  safe_mode: string;
  printer_id: number;
  total_steps: number;
  completed_steps: number;
  blocked_while_printing_count: number;
  steps: Array<{
    order: number;
    phase: string;
    test_key: string;
    title: string;
    status: "completed" | "pending" | "skipped";
    risk_level: CalibrationTestRecord["risk_level"];
    execution_mode: CalibrationTestRecord["execution_mode"];
    reason: string;
  }>;
};

export type CalibrationPreflight = {
  safe_mode: string;
  printer_id: number;
  test_key: string;
  test_title: string;
  data_state: "live" | "offline";
  connected: boolean;
  printing: boolean;
  print_state: string;
  klipper_state?: string | null;
  klippy_state?: string | null;
  blocked: boolean;
  can_execute_gcode: boolean;
  block_reasons: string[];
  checklist: string[];
  gcode_preview: string[];
  rollback_plan: string;
  summary: string;
};

export type CalibrationExecutionRecord = {
  id: number;
  printer_id: number;
  test_key: string;
  created_at: string;
  status: string;
  confirmation_matched: boolean;
  operator_present: boolean;
  gcode_reviewed: boolean;
  connected: boolean;
  printing: boolean;
  print_state: string;
  klipper_state?: string | null;
  klippy_state?: string | null;
  commands: string[];
  sent_commands: string[];
  result: Array<Record<string, unknown>>;
  block_reasons: string[];
  message: string;
};

export type ConfigRemediationOption = {
  option: string;
  value: string;
};

export type ConfigRemediationCandidate = {
  id: string;
  path: string;
  section: string;
  start_line: number;
  end_line: number;
  current: string;
  proposed: string;
  diff: string[];
  changed: boolean;
  status?: string;
  error?: string;
};

export type ConfigRemediationResult = {
  printer_id?: number;
  status: string;
  config_root?: string;
  section?: string;
  options?: ConfigRemediationOption[];
  candidates?: ConfigRemediationCandidate[];
  target_ids?: string[];
  backup_path?: string;
  applied?: Array<{
    id: string;
    path: string;
    start_line: number;
    end_line: number;
  }>;
  firmware_restart?: Record<string, unknown>;
  error?: string;
};
