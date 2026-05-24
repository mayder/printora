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

export type SnapshotRecord = {
  id: number;
  printer_id: number;
  created_at: string;
  snapshot_type: string;
  summary: Record<string, unknown>;
};

export type SnapshotDiffItem = {
  field: string;
  title: string;
  severity: "info" | "monitorar" | "risco" | "bloqueio";
  before: unknown;
  after: unknown;
  detail: string;
};

export type SnapshotDiff = {
  printer_id: number;
  from_snapshot_id: number;
  to_snapshot_id: number;
  summary: string;
  highest_severity: "info" | "monitorar" | "risco" | "bloqueio";
  changes: SnapshotDiffItem[];
};

export type OperationMetric = {
  label: string;
  value: unknown;
  unit?: string | null;
};

export type OperationTemperature = {
  name: string;
  temperature?: number | null;
  target?: number | null;
  power?: number | null;
};

export type OperationFan = {
  name: string;
  speed?: number | null;
  rpm?: number | null;
};

export type OperationTemperatureHistoryRow = {
  snapshot_id: number | null;
  created_at: string;
  readings: Array<{
    name: string;
    temperature?: number | null;
    target?: number | null;
  }>;
};

export type OperationAction = {
  id: string;
  group: string;
  label: string;
  command: string;
  risk: string;
  compatibility?: string[];
  enabled: boolean;
  confirmation_required: boolean;
  block_reason: string;
};

export type OperationCapability = {
  action_id: string;
  status: "supported" | "unknown" | "blocked";
  reason: string;
};

export type OperationActionPreview = {
  printer_id: number;
  moonraker_url: string;
  history_id?: number;
  created_at?: string;
  safe_mode: string;
  action: OperationAction;
  parameters: Record<string, unknown>;
  expected_parameters: OperationActionParameterSpec[];
  command_preview: string[];
  would_send_gcode: boolean;
  executable: boolean;
  confirmation_phrase: string;
  blockers: string[];
  rollback_plan: string | string[];
  can_execute?: boolean;
  preflight?: Record<string, unknown>;
  capability?: OperationCapability;
};

export type OperationActionParameterSpec = {
  name: string;
  type: "number" | "enum" | "text";
  default?: number | string;
  min?: number;
  max?: number;
  values?: string[];
};

export type OperationActionPreviewRecord = {
  id: number;
  printer_id: number;
  created_at: string;
  action_id: string;
  action_label: string;
  safe_mode: string;
  executable: boolean;
  would_send_gcode: boolean;
  command_preview: string[];
  blockers: string[];
};

export type OperationActionExecutionAttempt = {
  id: number;
  printer_id: number;
  preview_id: number;
  created_at: string;
  action_id: string;
  status: string;
  confirmation_matched: boolean;
  executable: boolean;
  would_send_gcode: boolean;
  block_reason: string;
  payload: {
    rollback_plan?: string;
    command_preview?: string[];
    preflight?: {
      connected?: boolean | null;
      printing?: boolean | null;
      print_state?: string;
      summary?: string;
      error?: string;
    };
  };
};

export type OperationStatusResponse = {
  connected: boolean;
  safe_mode: string;
  data_state: "live" | "offline" | "fixture" | "last_snapshot";
  printer_id: number;
  moonraker_url: string;
  summary: string;
  error?: string;
  last_snapshot?: {
    id: number;
    created_at: string;
    snapshot_type: string;
  };
  can_send_commands: boolean;
  system_loads: OperationMetric[];
  temperatures: OperationTemperature[];
  temperature_history: OperationTemperatureHistoryRow[];
  actions: OperationAction[];
  capabilities: OperationCapability[];
  toolhead: Record<string, unknown>;
  extruder: Record<string, unknown>;
  miscellaneous: {
    fans?: OperationFan[];
    progress?: number | null;
    message?: string | null;
    print_state?: string | null;
    filename?: string | null;
    total_print_hours?: number | null;
  };
};

export type BackupPolicyRecord = {
  id: number;
  printer_id: number;
  name: string;
  source_path: string;
  destination_path: string;
  include_patterns: string[];
  exclude_patterns: string[];
  dry_run_only: boolean;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type BackupRunRecord = {
  id: number;
  printer_id: number;
  policy_id: number;
  created_at: string;
  status: string;
  dry_run: boolean;
  source_path: string;
  destination_path: string;
  include_patterns: string[];
  exclude_patterns: string[];
  total_files: number;
  total_bytes: number;
  message: string;
};

export type BackupArchiveCompareResponse = {
  safe_mode: string;
  base_archive_path: string;
  target_archive_path: string;
  added: string[];
  removed: string[];
  changed: string[];
  unchanged_count: number;
  summary: string;
};

export type BackupRestorePlanResponse = {
  safe_mode: string;
  archive_path: string;
  restore_root: string;
  selected_files: string[];
  missing_files: string[];
  planned_commands: string[];
  blocked: boolean;
  message: string;
};

export type SanitizedReport = {
  printer_id: number;
  safe_mode: string;
  format: "markdown";
  data_state: string;
  source: string;
  redactions: string[];
  markdown: string;
};

export type MaintenanceEventRecord = {
  id: number;
  printer_id: number;
  performed_at: string;
  event_type: "maintenance" | "failure" | "adjustment" | "note";
  component?: string | null;
  title: string;
  notes: string;
  created_at: string;
  print_hours_at?: number | null;
  print_hours_read_at?: string | null;
};

export type MaintenanceTaskRecord = {
  id: number;
  printer_id: number;
  name: string;
  component: string;
  interval_days: number;
  interval_kind: "days" | "print_hours";
  interval_value: number;
  last_done_at?: string | null;
  last_done_print_hours?: number | null;
  last_print_hours_read_at?: string | null;
  current_print_hours?: number | null;
  current_print_hours_read_at?: string | null;
  current_print_hours_source?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  due_status: "due" | "soon" | "ok" | "unknown" | "not_validated" | "needs_review";
  days_until_due?: number | null;
  print_hours_delta?: number | null;
  print_hours_until_due?: number | null;
  due_detail?: string | null;
};

export type MaintenanceSummary = {
  printer_id: number;
  safe_mode: string;
  counts: Record<string, number>;
  due_components: string[];
  next_due_task?: MaintenanceTaskRecord | null;
  recommended_tasks: Array<{ name: string; component: string; interval_days: number; interval_kind?: "days" | "print_hours"; interval_value?: number }>;
  print_hours_source?: string | null;
  print_hours_read_at?: string | null;
};

export type MaintenancePrintHoursStatus = {
  available: boolean;
  total_print_hours?: number | null;
  read_at?: string | null;
  source?: string | null;
};

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

export type PluginAuditItem = {
  name: string;
  title: string;
  detected: boolean;
  classification:
    | "necessario"
    | "opcional"
    | "legado_lixo_tecnico"
    | "perigoso_remover_agora"
    | "seguro_remover_depois_backup"
    | "precisa_confirmacao";
  version?: string | null;
  dirty?: boolean | null;
  commits_behind?: number | null;
  risk: string;
  recommendation: string;
  action: "manter" | "investigar" | "remover_depois_backup" | "nao_remover_agora";
  evidence: string[];
  removal_gates: string[];
};

export type PluginAuditResponse = {
  printer_id: number;
  safe_mode: string;
  source: string;
  summary: string;
  counts: Record<string, number>;
  unknown_update_manager_components: string[];
  items: PluginAuditItem[];
};

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
  action: "refresh" | "update";
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
  phase: "confirm" | "running" | "done" | "failed";
};

export type BoardPreset = {
  id: string;
  vendor: string;
  name: string;
  mcu: string;
  architecture: string;
  connection_type: "usb" | "can" | "usb_can_bridge";
  communication: string;
  bootloader_offset: string;
  canbus_pins?: string | null;
  build_output: string;
  default_flash_method: "katapult_can" | "katapult_usb_can" | "dfu_usb" | "manual";
  notes: string;
};

export type FirmwareBoardRecord = {
  id: number;
  printer_id: number;
  name: string;
  preset_id: string;
  can_uuid?: string | null;
  can_interface: string;
  connection_type: "usb" | "can" | "usb_can_bridge";
  mcu: string;
  flash_method: "katapult_can" | "katapult_usb_can" | "dfu_usb" | "manual";
  config_file: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type FirmwareHardwareItem = {
  id: string;
  name: string;
  role: "mainboard" | "toolhead" | "can_adapter" | "unknown";
  status: "detected" | "registered" | "needs_mapping";
  source: string;
  connection: "can" | "usb" | "usb_can_bridge" | "dedicated_usb_can" | "unknown";
  mcu_name?: string | null;
  current_version?: string | null;
  can_uuid?: string | null;
  can_interface?: string | null;
  registered_board_id?: number | null;
  matched_catalog_ids: string[];
  matched_preset_ids: string[];
  guide_url?: string | null;
  action_label: string;
  detail: string;
};

export type FirmwareHardwareInventory = {
  printer_id: number;
  safe_mode: string;
  source: string;
  summary: string;
  catalog_source: {
    name: string;
    url: string;
    retrieved_at: string;
    notes: string[];
  };
  catalog_counts: Record<string, number>;
  items: FirmwareHardwareItem[];
};

export type FirmwareBuildRunRecord = {
  id: number;
  printer_id: number;
  board_id: number;
  created_at: string;
  status: string;
  klipper_path: string;
  output_dir: string;
  config_backup_path: string;
  binary_output_path: string;
  commands: string[];
  checklist: string[];
  message: string;
};

export type FirmwareBuildPreflight = {
  safe_mode: string;
  printer_id: number;
  board_id: number;
  board_name: string;
  klipper_path: string;
  output_root: string;
  config_file: string;
  expected_build_output: string;
  checks: {
    key: string;
    label: string;
    status: "ok" | "warning" | "blocked";
    detail: string;
  }[];
  commands_preview: string[];
  blocked: boolean;
  can_execute_build: boolean;
  message: string;
};

export type FirmwareFlashRunRecord = {
  id: number;
  printer_id: number;
  board_id: number;
  build_run_id?: number | null;
  created_at: string;
  status: string;
  flash_method: "katapult_can" | "katapult_usb_can" | "dfu_usb" | "manual";
  can_uuid?: string | null;
  can_interface: string;
  binary_path: string;
  commands: string[];
  checklist: string[];
  message: string;
};

export type FirmwareFlashPreflight = {
  safe_mode: string;
  printer_id: number;
  board_id: number;
  board_name: string;
  flash_method: FirmwareBoardRecord["flash_method"];
  can_uuid?: string | null;
  can_interface: string;
  binary_path: string;
  connected: boolean;
  printing: boolean;
  print_state: string;
  klipper_state?: string | null;
  klippy_state?: string | null;
  checks: {
    key: string;
    label: string;
    status: "ok" | "warning" | "blocked";
    detail: string;
  }[];
  commands_preview: string[];
  rollback_plan: string[];
  blocked: boolean;
  can_execute_flash: boolean;
  message: string;
};

export type FirmwareRecoveryPlan = {
  safe_mode: string;
  printer_id: number;
  board_id: number;
  board_name: string;
  flash_method: FirmwareBoardRecord["flash_method"];
  can_uuid?: string | null;
  can_interface: string;
  prerequisites: string[];
  recovery_steps: string[];
  validation_steps: string[];
  rollback_notes: string[];
  blocked: boolean;
};

export type BackupRestoreGateResponse = {
  safe_mode: string;
  accepted_confirmation: boolean;
  blocked: boolean;
  plan: BackupRestorePlanResponse;
  rollback_plan: string[];
  message: string;
};

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
export type ThemeMode = "dark" | "light";
