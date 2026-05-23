import React from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  Bell,
  Camera,
  CalendarDays,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileText,
  Gauge,
  HelpCircle,
  Home,
  History,
  Hourglass,
  ListChecks,
  Menu,
  Moon,
  Play,
  Plus,
  Printer,
  Radio,
  RefreshCw,
  Search,
  Server,
  Settings,
  ShieldCheck,
  ShieldAlert,
  SkipForward,
  SlidersHorizontal,
  Timer,
  Sun,
  Trash2,
  Undo2,
  Wrench,
  X,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  canRollbackSelfUpdateRun,
  formatSelfUpdateEnvironment,
  formatSelfUpdateStatus,
  formatSelfUpdateStepStatus,
  isSelfUpdateEnvironmentSupported,
  selfUpdateRunClass,
  selfUpdateStepClass,
} from "./selfUpdate";
import type {
  SelfUpdateApplyResponse,
  SelfUpdateHistoryResponse,
  SelfUpdatePlanResponse,
  SelfUpdateRollbackResponse,
  SelfUpdateRunRecord,
} from "./selfUpdate";
import "./styles.css";

type ChecklistItem = {
  key: string;
  title: string;
  ok: boolean;
  severity: string;
  detail: string;
  status: string;
  source: string;
};

type ChecklistResponse = {
  can_print: boolean;
  data_state: string;
  source: string;
  error?: string | null;
  summary: string;
  items: ChecklistItem[];
};

type MoonrakerStatus = {
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

type DiscoveredPrinter = {
  name: string;
  moonraker_url: string;
  address: string;
  klippy_connected: boolean | null;
  klippy_state: string | null;
  moonraker_version: string | null;
  already_registered: boolean;
};

type PrinterDiscoveryResponse = {
  cidr: string;
  safe_mode: string;
  scanned_hosts: number;
  candidates: DiscoveredPrinter[];
  warnings: string[];
};

type ConnectionCheckResult = {
  ok: boolean;
  target: string;
  detail: string;
};

type PrinterConnectionTestResponse = {
  safe_mode: string;
  moonraker: ConnectionCheckResult;
  ssh?: ConnectionCheckResult | null;
};

type PrinterRecord = {
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

type SnapshotRecord = {
  id: number;
  printer_id: number;
  created_at: string;
  snapshot_type: string;
  summary: Record<string, unknown>;
};

type SnapshotDiffItem = {
  field: string;
  title: string;
  severity: "info" | "monitorar" | "risco" | "bloqueio";
  before: unknown;
  after: unknown;
  detail: string;
};

type SnapshotDiff = {
  printer_id: number;
  from_snapshot_id: number;
  to_snapshot_id: number;
  summary: string;
  highest_severity: "info" | "monitorar" | "risco" | "bloqueio";
  changes: SnapshotDiffItem[];
};

type AuditFinding = {
  id: string;
  title: string;
  category: string;
  classification: "corrigir_agora" | "monitorar" | "ignorar" | "precisa_confirmacao";
  severity: "blocker" | "warning" | "info";
  detail: string;
  safe_action: string;
};

type AuditResponse = {
  connected: boolean;
  safe_mode: string;
  data_state?: "live" | "last_snapshot" | "offline";
  source?: string;
  error?: string | null;
  mode?: string;
  executed?: boolean;
  summary: string;
  counts: Record<string, number>;
  findings: AuditFinding[];
  section_summary?: Record<string, unknown>;
};

type HealthItem = {
  key: string;
  title: string;
  ok: boolean;
  severity: "ok" | "info" | "warning" | "blocker";
  detail: string;
  action: string;
};

type HealthResponse = {
  connected: boolean;
  safe_mode: string;
  data_state: string;
  source: string;
  error?: string | null;
  printer_id: number;
  moonraker_url: string;
  decision: "ok_para_imprimir" | "monitorar" | "nao_imprimir";
  summary: string;
  metrics: Record<string, unknown>;
  counts: Record<string, number>;
  items: HealthItem[];
};

type OperationMetric = {
  label: string;
  value: unknown;
  unit?: string | null;
};

type OperationTemperature = {
  name: string;
  temperature?: number | null;
  target?: number | null;
  power?: number | null;
};

type OperationFan = {
  name: string;
  speed?: number | null;
  rpm?: number | null;
};

type OperationTemperatureHistoryRow = {
  snapshot_id: number | null;
  created_at: string;
  readings: Array<{
    name: string;
    temperature?: number | null;
    target?: number | null;
  }>;
};

type OperationAction = {
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

type OperationCapability = {
  action_id: string;
  status: "supported" | "unknown" | "blocked";
  reason: string;
};

type OperationActionPreview = {
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

type OperationActionParameterSpec = {
  name: string;
  type: "number" | "enum" | "text";
  default?: number | string;
  min?: number;
  max?: number;
  values?: string[];
};

type OperationActionPreviewRecord = {
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

type OperationActionExecutionAttempt = {
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

type OperationStatusResponse = {
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
  };
};

type BackupPolicyRecord = {
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

type BackupRunRecord = {
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

type BackupArchiveCompareResponse = {
  safe_mode: string;
  base_archive_path: string;
  target_archive_path: string;
  added: string[];
  removed: string[];
  changed: string[];
  unchanged_count: number;
  summary: string;
};

type BackupRestorePlanResponse = {
  safe_mode: string;
  archive_path: string;
  restore_root: string;
  selected_files: string[];
  missing_files: string[];
  planned_commands: string[];
  blocked: boolean;
  message: string;
};

type SanitizedReport = {
  printer_id: number;
  safe_mode: string;
  format: "markdown";
  data_state: string;
  source: string;
  redactions: string[];
  markdown: string;
};

type MaintenanceEventRecord = {
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

type MaintenanceTaskRecord = {
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

type MaintenanceSummary = {
  printer_id: number;
  safe_mode: string;
  counts: Record<string, number>;
  due_components: string[];
  next_due_task?: MaintenanceTaskRecord | null;
  recommended_tasks: Array<{ name: string; component: string; interval_days: number; interval_kind?: "days" | "print_hours"; interval_value?: number }>;
  print_hours_source?: string | null;
  print_hours_read_at?: string | null;
};

type MaintenancePrintHoursStatus = {
  available: boolean;
  total_print_hours?: number | null;
  read_at?: string | null;
  source?: string | null;
};

type ZOffsetRecord = {
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

type ZOffsetWizardPlan = {
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

type CanBusRecord = {
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

type CanBusSummary = {
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

type CanBusRecordComparison = {
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

type PluginAuditItem = {
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

type PluginAuditResponse = {
  printer_id: number;
  safe_mode: string;
  source: string;
  summary: string;
  counts: Record<string, number>;
  unknown_update_manager_components: string[];
  items: PluginAuditItem[];
};

type UpdateComponent = {
  name: string;
  title: string;
  configured_type: string;
  status: "up_to_date" | "update_available" | "warning" | "busy" | "unknown";
  current_version?: string | null;
  remote_version?: string | null;
  full_version?: string | null;
  is_dirty?: boolean | null;
  is_valid?: boolean | null;
  commits_behind_count: number;
  package_count: number;
  warnings: string[];
  anomalies: string[];
  can_update: boolean;
};

type UpdateStatusResponse = {
  safe_mode: string;
  busy: boolean;
  github_requests_remaining?: number | null;
  github_rate_limit?: number | null;
  summary: string;
  counts: Record<string, number>;
  components: UpdateComponent[];
};

type ReleaseRecord = {
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

type SystemReleasesResponse = {
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

type UpdateActionResponse = {
  safe_mode: string;
  action: "refresh" | "update";
  target: string;
  accepted: boolean;
  message: string;
  result: Record<string, unknown>;
};

type UpdateLogEntry = {
  id: number;
  time: string;
  level: "info" | "success" | "warning" | "error";
  message: string;
};

type AlertCenterItem = {
  id: string;
  source: string;
  title: string;
  detail: string;
  action: string;
  severity: "blocker" | "warning" | "info";
};

type UpdateDialogState = {
  open: boolean;
  target: string;
  label: string;
  phase: "confirm" | "running" | "done" | "failed";
};

type BoardPreset = {
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

type FirmwareBoardRecord = {
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

type FirmwareBuildRunRecord = {
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

type FirmwareBuildPreflight = {
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

type FirmwareFlashRunRecord = {
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

type FirmwareFlashPreflight = {
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

type FirmwareRecoveryPlan = {
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

type BackupRestoreGateResponse = {
  safe_mode: string;
  accepted_confirmation: boolean;
  blocked: boolean;
  plan: BackupRestorePlanResponse;
  rollback_plan: string[];
  message: string;
};

type CalibrationTestRecord = {
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

type CalibrationAvailableTestsResponse = {
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

type CalibrationRunRecord = {
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

type CalibrationResultFormConfig = {
  summary: string;
  observedLabel: string;
  observedPlaceholder: string;
  notesLabel: string;
  notesPlaceholder: string;
  showMaterial: boolean;
  showPlate: boolean;
  showNozzle: boolean;
};

type CalibrationSummary = {
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

type CalibrationSequencePlan = {
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

type CalibrationPreflight = {
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

type CalibrationExecutionRecord = {
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

type AppSection =
  | "overview"
  | "printers"
  | "operation"
  | "monitoring"
  | "updates"
  | "calibration"
  | "tests"
  | "firmware"
  | "maintenance"
  | "reports"
  | "settings";

type ThemeMode = "dark" | "light";

const appSections: Array<{
  key: AppSection;
  icon: LucideIcon;
  label: string;
  detail: string;
  purpose: string;
}> = [
  {
    key: "overview",
    icon: Home,
    label: "Visão geral",
    detail: "Dashboard geral da frota e da impressora selecionada.",
    purpose: "Use esta tela para saber rapidamente se há bloqueios, alertas ou pendências antes de trabalhar na impressora.",
  },
  {
    key: "printers",
    icon: Printer,
    label: "Impressoras",
    detail: "Cadastro, descoberta e seleção da impressora ativa.",
    purpose: "Gerencie as impressoras cadastradas e defina qual delas controla o contexto do restante do sistema.",
  },
  {
    key: "operation",
    icon: Gauge,
    label: "Operação",
    detail: "Painéis read-only no estilo Mainsail.",
    purpose: "Acompanhe estado operacional, temperaturas, toolhead, extrusor e periféricos sem enviar comandos para a impressora.",
  },
  {
    key: "monitoring",
    icon: Activity,
    label: "Monitoramento",
    detail: "Health, logs, CAN, Moonraker, Klipper e host.",
    purpose: "Analise saúde, logs e sinais técnicos antes de imprimir, atualizar ou diagnosticar falhas.",
  },
  {
    key: "updates",
    icon: RefreshCw,
    label: "Atualizações",
    detail: "Update Manager da impressora selecionada.",
    purpose: "Veja componentes desatualizados e execute updates pelo Moonraker, no mesmo modelo do Mainsail.",
  },
  {
    key: "calibration",
    icon: SlidersHorizontal,
    label: "Calibração",
    detail: "Z-offset, primeira camada e ajustes manuais.",
    purpose: "Registre offsets, siga o wizard manual e compare variações por chapa, material e toolhead.",
  },
  {
    key: "tests",
    icon: ListChecks,
    label: "Testes",
    detail: "Centro de testes Voron e histórico de resultados.",
    purpose: "Escolha um teste, revise a ajuda quando precisar e execute com confirmação presencial.",
  },
  {
    key: "firmware",
    icon: Zap,
    label: "Firmware",
    detail: "Placas, presets, dry-runs de build/flash e auditoria de mods.",
    purpose: "Gerencie MCUs, presets, builds e flash planejado para a impressora ativa.",
  },
  {
    key: "maintenance",
    icon: Wrench,
    label: "Manutenção",
    detail: "Backups, tarefas preventivas e diário da impressora.",
    purpose: "Acompanhe manutenção preventiva, eventos e backups locais com histórico por impressora.",
  },
  {
    key: "reports",
    icon: FileText,
    label: "Relatórios",
    detail: "Auditorias, snapshots, diffs e relatórios sanitizados.",
    purpose: "Gere diagnósticos compartilháveis e compare snapshots sem expor dados sensíveis.",
  },
  {
    key: "settings",
    icon: Settings,
    label: "Configurações",
    detail: "Preferências, integrações e contexto da impressora ativa.",
    purpose: "Versão instalada, releases e updates do próprio Printora.",
  },
];

const navGroups: Array<{ title: string; sections: AppSection[] }> = [
  { title: "Principal", sections: ["overview", "printers"] },
  { title: "Impressora ativa", sections: ["operation", "monitoring", "updates", "calibration", "tests", "firmware", "maintenance"] },
  { title: "Diagnóstico", sections: ["reports", "settings"] },
];

const onlinePrinterSections = new Set<AppSection>([
  "operation",
  "monitoring",
  "updates",
  "calibration",
  "tests",
  "firmware",
  "reports",
]);

const selectedPrinterLocalSections = new Set<AppSection>(["maintenance"]);

function getInitialSection(): AppSection {
  const section = new URLSearchParams(window.location.search).get("section") ?? window.location.hash.replace("#", "");
  return appSections.some((candidate) => candidate.key === section) ? (section as AppSection) : "overview";
}

function App() {
  const [printers, setPrinters] = React.useState<PrinterRecord[]>([]);
  const [selectedPrinterId, setSelectedPrinterId] = React.useState<number | null>(null);
  const [activeSection, setActiveSection] = React.useState<AppSection>(() => getInitialSection());
  const [discovery, setDiscovery] = React.useState<PrinterDiscoveryResponse | null>(null);
  const [printerModalOpen, setPrinterModalOpen] = React.useState(false);
  const [printerModalMode, setPrinterModalMode] = React.useState<"create" | "edit">("create");
  const [editingPrinterId, setEditingPrinterId] = React.useState<number | null>(null);
  const [theme, setTheme] = React.useState<ThemeMode>(() => {
    const storedTheme = window.localStorage.getItem("printora-theme");
    return storedTheme === "light" ? "light" : "dark";
  });
  const [newPrinterName, setNewPrinterName] = React.useState("Voron - Mayder");
  const [newPrinterUrl, setNewPrinterUrl] = React.useState("http://voron.local:7125");
  const [newPrinterSshHost, setNewPrinterSshHost] = React.useState("");
  const [newPrinterSshPort, setNewPrinterSshPort] = React.useState(22);
  const [newPrinterSshUser, setNewPrinterSshUser] = React.useState("");
  const [newPrinterSshCredential, setNewPrinterSshCredential] = React.useState("");
  const [printerConnectionTest, setPrinterConnectionTest] = React.useState<PrinterConnectionTestResponse | null>(null);
  const [snapshots, setSnapshots] = React.useState<SnapshotRecord[]>([]);
  const [fromSnapshotId, setFromSnapshotId] = React.useState<number | null>(null);
  const [toSnapshotId, setToSnapshotId] = React.useState<number | null>(null);
  const [snapshotDiff, setSnapshotDiff] = React.useState<SnapshotDiff | null>(null);
  const [status, setStatus] = React.useState<MoonrakerStatus | null>(null);
  const [health, setHealth] = React.useState<HealthResponse | null>(null);
  const [operationStatus, setOperationStatus] = React.useState<OperationStatusResponse | null>(null);
  const [operationActionPreview, setOperationActionPreview] = React.useState<OperationActionPreview | null>(null);
  const [operationActionHistory, setOperationActionHistory] = React.useState<OperationActionPreviewRecord[]>([]);
  const [operationExecutionHistory, setOperationExecutionHistory] = React.useState<OperationActionExecutionAttempt[]>([]);
  const [operationActionParameters, setOperationActionParameters] = React.useState<Record<string, Record<string, string>>>({});
  const [operationExecutionPhrase, setOperationExecutionPhrase] = React.useState("");
  const [operationExecutionAttempt, setOperationExecutionAttempt] = React.useState<OperationActionExecutionAttempt | null>(null);
  const [updateStatus, setUpdateStatus] = React.useState<UpdateStatusResponse | null>(null);
  const [systemReleases, setSystemReleases] = React.useState<SystemReleasesResponse | null>(null);
  const [releaseLoading, setReleaseLoading] = React.useState(false);
  const [releaseError, setReleaseError] = React.useState<string | null>(null);
  const displayedReleaseRows = React.useMemo(() => {
    if (!systemReleases) {
      return [];
    }
    return systemReleases.releases.filter((release) => release.tag !== systemReleases.latest_release?.tag);
  }, [systemReleases]);
  const [selfUpdatePlan, setSelfUpdatePlan] = React.useState<SelfUpdatePlanResponse | null>(null);
  const [selfUpdateHistory, setSelfUpdateHistory] = React.useState<SelfUpdateRunRecord[]>([]);
  const [selfUpdateModalOpen, setSelfUpdateModalOpen] = React.useState(false);
  const [selfUpdateApplying, setSelfUpdateApplying] = React.useState(false);
  const [selfUpdateRollingBack, setSelfUpdateRollingBack] = React.useState(false);
  const [selfUpdateConfirmation, setSelfUpdateConfirmation] = React.useState("");
  const [selfUpdateRollbackConfirmation, setSelfUpdateRollbackConfirmation] = React.useState("");
  const [selfUpdateMessage, setSelfUpdateMessage] = React.useState<string | null>(null);
  const [selfUpdateConnectionLost, setSelfUpdateConnectionLost] = React.useState(false);
  const [updateActionResult, setUpdateActionResult] = React.useState<UpdateActionResponse | null>(null);
  const [updateDialog, setUpdateDialog] = React.useState<UpdateDialogState | null>(null);
  const [updateLogs, setUpdateLogs] = React.useState<UpdateLogEntry[]>([]);
  const [alertCenterOpen, setAlertCenterOpen] = React.useState(false);
  const [mobileNavOpen, setMobileNavOpen] = React.useState(false);
  const [checklist, setChecklist] = React.useState<ChecklistResponse | null>(null);
  const [audit, setAudit] = React.useState<AuditResponse | null>(null);
  const [hostAudit, setHostAudit] = React.useState<AuditResponse | null>(null);
  const [backupPolicies, setBackupPolicies] = React.useState<BackupPolicyRecord[]>([]);
  const [backupRuns, setBackupRuns] = React.useState<BackupRunRecord[]>([]);
  const [backupCompareResult, setBackupCompareResult] = React.useState<BackupArchiveCompareResponse | null>(null);
  const [backupRestorePlan, setBackupRestorePlan] = React.useState<BackupRestorePlanResponse | null>(null);
  const [backupRestoreGate, setBackupRestoreGate] = React.useState<BackupRestoreGateResponse | null>(null);
  const [sanitizedReport, setSanitizedReport] = React.useState<SanitizedReport | null>(null);
  const [maintenanceEvents, setMaintenanceEvents] = React.useState<MaintenanceEventRecord[]>([]);
  const [maintenanceTasks, setMaintenanceTasks] = React.useState<MaintenanceTaskRecord[]>([]);
  const [maintenanceSummary, setMaintenanceSummary] = React.useState<MaintenanceSummary | null>(null);
  const [maintenancePrintHours, setMaintenancePrintHours] = React.useState<MaintenancePrintHoursStatus | null>(null);
  const [zOffsetRecords, setZOffsetRecords] = React.useState<ZOffsetRecord[]>([]);
  const [canRecords, setCanRecords] = React.useState<CanBusRecord[]>([]);
  const [canSummary, setCanSummary] = React.useState<CanBusSummary | null>(null);
  const [canComparison, setCanComparison] = React.useState<CanBusRecordComparison | null>(null);
  const [pluginAudit, setPluginAudit] = React.useState<PluginAuditResponse | null>(null);
  const [boardPresets, setBoardPresets] = React.useState<BoardPreset[]>([]);
  const [firmwareBoards, setFirmwareBoards] = React.useState<FirmwareBoardRecord[]>([]);
  const [firmwareBuildRuns, setFirmwareBuildRuns] = React.useState<FirmwareBuildRunRecord[]>([]);
  const [firmwareFlashRuns, setFirmwareFlashRuns] = React.useState<FirmwareFlashRunRecord[]>([]);
  const [firmwareRecoveryPlan, setFirmwareRecoveryPlan] = React.useState<FirmwareRecoveryPlan | null>(null);
  const [firmwareBuildPreflight, setFirmwareBuildPreflight] = React.useState<FirmwareBuildPreflight | null>(null);
  const [firmwareFlashPreflight, setFirmwareFlashPreflight] = React.useState<FirmwareFlashPreflight | null>(null);
  const [calibrationTests, setCalibrationTests] = React.useState<CalibrationTestRecord[]>([]);
  const [calibrationHiddenTests, setCalibrationHiddenTests] = React.useState<CalibrationAvailableTestsResponse["hidden_tests"]>([]);
  const [calibrationRuns, setCalibrationRuns] = React.useState<CalibrationRunRecord[]>([]);
  const [calibrationSummary, setCalibrationSummary] = React.useState<CalibrationSummary | null>(null);
  const [calibrationSequence, setCalibrationSequence] = React.useState<CalibrationSequencePlan | null>(null);
  const [calibrationPreflight, setCalibrationPreflight] = React.useState<CalibrationPreflight | null>(null);
  const [calibrationExecutions, setCalibrationExecutions] = React.useState<CalibrationExecutionRecord[]>([]);
  const [calibrationExecutionResult, setCalibrationExecutionResult] = React.useState<CalibrationExecutionRecord | null>(null);
  const [calibrationHelpTestKey, setCalibrationHelpTestKey] = React.useState<string | null>(null);
  const [calibrationExecuteTestKey, setCalibrationExecuteTestKey] = React.useState<string | null>(null);
  const [calibrationResultTestKey, setCalibrationResultTestKey] = React.useState<string | null>(null);
  const [calibrationResultFormOpen, setCalibrationResultFormOpen] = React.useState(false);
  const [calibrationActivityCleared, setCalibrationActivityCleared] = React.useState(false);
  const [testFilter, setTestFilter] = React.useState<"all" | "executable" | "manual" | "blocked">("all");
  const [maintenanceFilter, setMaintenanceFilter] = React.useState<"all" | "due" | "soon" | "ok">("all");
  const [firmwareFilter, setFirmwareFilter] = React.useState<"all" | "can" | "usb">("all");
  const [zOffsetWizardPlan, setZOffsetWizardPlan] = React.useState<ZOffsetWizardPlan | null>(null);
  const [zOffsetWizardChecks, setZOffsetWizardChecks] = React.useState<Record<string, boolean>>({});
  const [zOffsetFormOpen, setZOffsetFormOpen] = React.useState(false);
  const [maintenanceEventType, setMaintenanceEventType] =
    React.useState<MaintenanceEventRecord["event_type"] | "">("");
  const [maintenanceComponent, setMaintenanceComponent] = React.useState("");
  const [maintenanceTitle, setMaintenanceTitle] = React.useState("");
  const [maintenanceNotes, setMaintenanceNotes] = React.useState("");
  const [maintenanceDoneTask, setMaintenanceDoneTask] = React.useState<MaintenanceTaskRecord | null>(null);
  const [maintenanceDoneNotes, setMaintenanceDoneNotes] = React.useState("");
  const [maintenanceDoneIntervalKind, setMaintenanceDoneIntervalKind] = React.useState<"days" | "print_hours">("days");
  const [maintenanceDoneIntervalValue, setMaintenanceDoneIntervalValue] = React.useState("");
  const [maintenanceDoneDisableReminder, setMaintenanceDoneDisableReminder] = React.useState(false);
  const [maintenanceFreeModalOpen, setMaintenanceFreeModalOpen] = React.useState(false);
  const [maintenanceFreeReminderEnabled, setMaintenanceFreeReminderEnabled] = React.useState(false);
  const [maintenanceFreeIntervalKind, setMaintenanceFreeIntervalKind] = React.useState<"days" | "print_hours">("days");
  const [maintenanceFreeIntervalValue, setMaintenanceFreeIntervalValue] = React.useState("");
  const [zOffsetPlateName, setZOffsetPlateName] = React.useState("");
  const [zOffsetMaterial, setZOffsetMaterial] = React.useState("");
  const [zOffsetNozzle, setZOffsetNozzle] = React.useState("");
  const [zOffsetValue, setZOffsetValue] = React.useState("");
  const [zOffsetNotes, setZOffsetNotes] = React.useState("");
  const [canInterfaceName, setCanInterfaceName] = React.useState("can0");
  const [canRxError, setCanRxError] = React.useState(0);
  const [canTxError, setCanTxError] = React.useState(0);
  const [canTxRetries, setCanTxRetries] = React.useState(0);
  const [canBusState, setCanBusState] = React.useState("ERROR-ACTIVE");
  const [canBitrate, setCanBitrate] = React.useState(1000000);
  const [canNotes, setCanNotes] = React.useState("");
  const [canRawOutput, setCanRawOutput] = React.useState("");
  const [firmwareBoardName, setFirmwareBoardName] = React.useState("EBB T0");
  const [firmwareBoardPresetId, setFirmwareBoardPresetId] = React.useState("btt_ebb36_g0b1_can");
  const [firmwareBoardCanUuid, setFirmwareBoardCanUuid] = React.useState("");
  const [firmwareBoardCanInterface, setFirmwareBoardCanInterface] = React.useState("can0");
  const [firmwareBoardConfigFile, setFirmwareBoardConfigFile] = React.useState("firmware/ebb_t0.config");
  const [firmwareBoardNotes, setFirmwareBoardNotes] = React.useState("");
  const [firmwareKlipperPath, setFirmwareKlipperPath] = React.useState("~/klipper");
  const [firmwareOutputRoot, setFirmwareOutputRoot] = React.useState("~/printer_data/firmware_builds");
  const [firmwareBuildConfirmation, setFirmwareBuildConfirmation] = React.useState("");
  const [firmwareFlashBinaryPath, setFirmwareFlashBinaryPath] = React.useState("");
  const [firmwareFlashConfirmation, setFirmwareFlashConfirmation] = React.useState("");
  const [calibrationTestKey, setCalibrationTestKey] = React.useState("probe_accuracy_center");
  const [calibrationResultStatus, setCalibrationResultStatus] =
    React.useState<CalibrationRunRecord["result_status"]>("passed");
  const [calibrationMaterial, setCalibrationMaterial] = React.useState("PLA");
  const [calibrationPlateName, setCalibrationPlateName] = React.useState("Texturizada");
  const [calibrationNozzle, setCalibrationNozzle] = React.useState("T0");
  const [calibrationObservedValue, setCalibrationObservedValue] = React.useState("");
  const [calibrationNotes, setCalibrationNotes] = React.useState("");
  const [calibrationGcodeReviewed, setCalibrationGcodeReviewed] = React.useState(false);
  const [calibrationPhotoReference, setCalibrationPhotoReference] = React.useState("");
  const [calibrationOperatorPresent, setCalibrationOperatorPresent] = React.useState(false);
  const [calibrationExecutionConfirmation, setCalibrationExecutionConfirmation] = React.useState("");
  const [backupName, setBackupName] = React.useState("Config backup");
  const [backupSourcePath, setBackupSourcePath] = React.useState("/home/pi/printer_data/config");
  const [backupDestinationPath, setBackupDestinationPath] = React.useState(
    "/home/pi/printer_data/backups/printora",
  );
  const [backupDryRunOnly, setBackupDryRunOnly] = React.useState(true);
  const [backupCompareBasePath, setBackupCompareBasePath] = React.useState("");
  const [backupCompareTargetPath, setBackupCompareTargetPath] = React.useState("");
  const [backupRestoreArchivePath, setBackupRestoreArchivePath] = React.useState("");
  const [backupRestoreRoot, setBackupRestoreRoot] = React.useState("/home/pi/printer_data/config");
  const [backupRestoreFiles, setBackupRestoreFiles] = React.useState("printer.cfg");
  const [backupRestoreConfirmation, setBackupRestoreConfirmation] = React.useState("");
  const updateSocketRef = React.useRef<WebSocket | null>(null);
  const updateLogIdRef = React.useRef(0);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      await Promise.allSettled([
        loadBoardPresets(),
        loadPrinters(),
      ]);
      void loadGlobalDiagnostics();
      void loadSystemReleases();
      void loadSelfUpdateHistory();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadGlobalDiagnostics() {
    const [statusResponse, checklistResponse, hostAuditResponse] = await Promise.allSettled([
      fetch("/api/moonraker/status"),
      fetch("/api/checklist/post-update"),
      fetch("/api/audit/host-read-only"),
    ]);
    if (statusResponse.status === "fulfilled" && statusResponse.value.ok) {
      setStatus((await statusResponse.value.json()) as MoonrakerStatus);
    }
    if (checklistResponse.status === "fulfilled" && checklistResponse.value.ok) {
      setChecklist((await checklistResponse.value.json()) as ChecklistResponse);
    }
    if (hostAuditResponse.status === "fulfilled" && hostAuditResponse.value.ok) {
      setHostAudit((await hostAuditResponse.value.json()) as AuditResponse);
    }
  }

  async function loadSystemReleases() {
    setReleaseLoading(true);
    setReleaseError(null);
    try {
      const response = await fetch("/api/system/releases");
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      setSystemReleases((await response.json()) as SystemReleasesResponse);
    } catch (err) {
      setReleaseError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setReleaseLoading(false);
    }
  }

  async function loadSelfUpdateHistory() {
    try {
      const response = await fetch("/api/system/update/history");
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as SelfUpdateHistoryResponse;
      setSelfUpdateHistory(payload.runs);
    } catch {
      // Histórico não deve bloquear o restante da tela.
    }
  }

  async function planSelfUpdate() {
    const targetTag = systemReleases?.latest_release?.tag;
    if (!targetTag) {
      return;
    }
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    setReleaseLoading(true);
    try {
      const response = await fetch("/api/system/update/plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_tag: targetTag,
          source_url: systemReleases.latest_release?.url ?? null,
        }),
      });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdatePlanResponse;
      setSelfUpdatePlan(payload);
      setSelfUpdateConfirmation("");
      setSelfUpdateRollbackConfirmation("");
      setSelfUpdateModalOpen(true);
      await loadSelfUpdateHistory();
    } catch (err) {
      setSelfUpdateMessage(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setReleaseLoading(false);
    }
  }

  async function applySelfUpdate() {
    const targetTag = selfUpdatePlan?.run.target_tag ?? systemReleases?.latest_release?.tag;
    if (!targetTag) {
      return;
    }
    setSelfUpdateApplying(true);
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    try {
      const response = await fetch("/api/system/update/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_tag: targetTag,
          source_url: systemReleases?.latest_release?.url ?? selfUpdatePlan?.run.source_url ?? null,
          confirmation_phrase: selfUpdateConfirmation,
        }),
      });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdateApplyResponse;
      setSelfUpdatePlan({
        safe_mode: "apply",
        update_supported: isSelfUpdateEnvironmentSupported(payload.run.environment),
        can_apply: false,
        message: payload.message,
        run: payload.run,
      });
      setSelfUpdateMessage(payload.message);
      await pollSelfUpdateRun(payload.run.id);
      await loadSelfUpdateHistory();
    } catch (err) {
      setSelfUpdateConnectionLost(true);
      setSelfUpdateMessage(err instanceof Error ? err.message : "O Printora pode estar reiniciando. Aguarde e recarregue.");
    } finally {
      setSelfUpdateApplying(false);
    }
  }

  async function pollSelfUpdateRun(runId: number) {
    for (let attempt = 0; attempt < 20; attempt += 1) {
      try {
        const response = await fetch(`/api/system/update/runs/${runId}`);
        if (!response.ok) {
          throw new Error(await readApiError(response));
        }
        const run = (await response.json()) as SelfUpdateRunRecord;
        setSelfUpdatePlan((current) =>
          current ? { ...current, run, message: current.message } : { safe_mode: "poll", update_supported: isSelfUpdateEnvironmentSupported(run.environment), can_apply: false, message: "Status atualizado.", run },
        );
        if (run.status !== "running") {
          return;
        }
      } catch {
        setSelfUpdateConnectionLost(true);
        setSelfUpdateMessage("O Printora pode estar reiniciando. Aguarde e recarregue.");
        return;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 2000));
    }
  }

  async function rollbackSelfUpdate(runId: number) {
    setSelfUpdateRollingBack(true);
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    try {
      const response = await fetch("/api/system/update/rollback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          run_id: runId,
          confirmation_phrase: selfUpdateRollbackConfirmation,
        }),
      });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdateRollbackResponse;
      setSelfUpdatePlan({
        safe_mode: "rollback",
        update_supported: isSelfUpdateEnvironmentSupported(payload.rollback_run.environment),
        can_apply: false,
        message: payload.message,
        run: payload.rollback_run,
      });
      setSelfUpdateMessage(payload.message);
      await pollSelfUpdateRun(payload.rollback_run.id);
      await loadSelfUpdateHistory();
    } catch (err) {
      setSelfUpdateConnectionLost(true);
      setSelfUpdateMessage(err instanceof Error ? err.message : "O Printora pode estar reiniciando. Aguarde e recarregue.");
    } finally {
      setSelfUpdateRollingBack(false);
    }
  }

  async function loadPrinters() {
    const response = await fetch("/api/printers");
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { printers: PrinterRecord[] };
    setPrinters(payload.printers);
    const nextSelected = selectedPrinterId ?? payload.printers[0]?.id ?? null;
    setSelectedPrinterId(nextSelected);
    if (nextSelected) {
      await loadPrinterContext(nextSelected);
    }
  }

  async function loadPrinterContext(printerId: number) {
    await loadPrinterLocalContext(printerId);
    void loadPrinterLiveContext(printerId);
  }

  async function loadPrinterLocalContext(printerId: number) {
    await Promise.allSettled([
      loadOperationActionHistory(printerId),
      loadOperationExecutionHistory(printerId),
      loadSnapshots(printerId),
      loadBackups(printerId),
      loadMaintenance(printerId),
      loadZOffsets(printerId),
      loadCanRecords(printerId),
      loadPluginAudit(printerId),
      loadFirmwareBoards(printerId),
      loadFirmwareBuildRuns(printerId),
      loadFirmwareFlashRuns(printerId),
      loadCalibrationRuns(printerId),
    ]);
  }

  async function loadPrinterLiveContext(printerId: number) {
    await Promise.allSettled([
      loadPrinterChecklist(printerId),
      loadOperationStatus(printerId),
      loadPrinterAudit(printerId),
      loadPrinterHealth(printerId),
      loadUpdateStatus(printerId),
      loadCalibrationTests(printerId),
    ]);
  }

  async function loadPrinterChecklist(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/checklist/post-update`);
    if (!response.ok) {
      setChecklist(null);
      return;
    }
    setChecklist((await response.json()) as ChecklistResponse);
  }

  async function loadPrinterAudit(printerId: number) {
    setAudit(null);
    const response = await fetch(`/api/printers/${printerId}/audit/read-only`);
    if (!response.ok) {
      return;
    }
    setAudit((await response.json()) as AuditResponse);
  }

  async function loadOperationStatus(printerId: number) {
    setOperationStatus(null);
    setOperationActionPreview(null);
    setOperationExecutionPhrase("");
    setOperationExecutionAttempt(null);
    const response = await fetch(`/api/printers/${printerId}/operation/status`);
    if (!response.ok) {
      return;
    }
    setOperationStatus((await response.json()) as OperationStatusResponse);
  }

  async function loadOperationActionHistory(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/operation/actions/history`);
    if (!response.ok) {
      setOperationActionHistory([]);
      return;
    }
    const payload = (await response.json()) as { previews: OperationActionPreviewRecord[] };
    setOperationActionHistory(payload.previews);
  }

  async function loadOperationExecutionHistory(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/operation/actions/executions`);
    if (!response.ok) {
      setOperationExecutionHistory([]);
      return;
    }
    const payload = (await response.json()) as { attempts: OperationActionExecutionAttempt[] };
    setOperationExecutionHistory(payload.attempts);
  }

  async function loadOfflineOperationFixture() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/operation/fixtures/voron-offline");
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationStatus((await response.json()) as OperationStatusResponse);
      setOperationActionPreview(null);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
      setActiveSection("operation");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function previewOperationAction(action: OperationAction) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora para gerar a prévia da ação.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/operation/actions/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: action.id, parameters: buildOperationActionPayload(operationActionParameters[action.id] ?? {}) }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationActionPreview((await response.json()) as OperationActionPreview);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
      await loadOperationActionHistory(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function preflightOperationAction(action: OperationAction) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora para validar o preflight da ação.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/operation/actions/preflight`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_id: action.id, parameters: buildOperationActionPayload(operationActionParameters[action.id] ?? {}) }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationActionPreview((await response.json()) as OperationActionPreview);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function updateOperationActionParameter(actionId: string, parameterName: string, value: string) {
    setOperationActionParameters((current) => ({
      ...current,
      [actionId]: {
        ...(current[actionId] ?? {}),
        [parameterName]: value,
      },
    }));
  }

  async function validateOperationExecutionGate() {
    if (!selectedPrinterId || !operationActionPreview?.history_id) {
      setError("Gere uma prévia antes de validar a execução.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/operation/actions/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          preview_id: operationActionPreview.history_id,
          confirmation_phrase: operationExecutionPhrase,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationExecutionAttempt((await response.json()) as OperationActionExecutionAttempt);
      await loadOperationExecutionHistory(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function selectPrinter(printerId: number) {
    setSelectedPrinterId(printerId);
    setSanitizedReport(null);
    setOperationActionHistory([]);
    setOperationExecutionHistory([]);
    setOperationExecutionPhrase("");
    setOperationExecutionAttempt(null);
    void loadPrinterContext(printerId);
  }

  async function createPrinter(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const validationError = validatePrinterConnectionInput(newPrinterUrl, newPrinterSshHost);
      if (validationError) {
        setError(validationError);
        return;
      }
      const payload = {
        name: newPrinterName.trim(),
        moonraker_url: newPrinterUrl.trim(),
        host_audit_mode: newPrinterSshHost && newPrinterSshUser ? "ssh" : "local",
        ssh_host: newPrinterSshHost.trim() || null,
        ssh_port: newPrinterSshPort,
        ssh_username: newPrinterSshUser.trim() || null,
        ssh_credential: newPrinterSshCredential || null,
      };
      const response = await fetch(printerModalMode === "edit" && editingPrinterId ? `/api/printers/${editingPrinterId}` : "/api/printers", {
        method: printerModalMode === "edit" && editingPrinterId ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const created = (await response.json()) as PrinterRecord;
      await loadPrinters();
      setSelectedPrinterId(created.id);
      await loadPrinterContext(created.id);
      setPrinterModalOpen(false);
      setNewPrinterSshCredential("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function discoverPrinters() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/printers/discover");
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setDiscovery((await response.json()) as PrinterDiscoveryResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function testPrinterConnections() {
    setLoading(true);
    setError(null);
    setPrinterConnectionTest(null);
    try {
      const validationError = validatePrinterConnectionInput(newPrinterUrl, newPrinterSshHost);
      if (validationError) {
        setError(validationError);
        return;
      }
      const response = await fetch("/api/printers/test-connection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          moonraker_url: newPrinterUrl.trim(),
          ssh_host: newPrinterSshHost.trim() || null,
          ssh_port: newPrinterSshPort,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setPrinterConnectionTest((await response.json()) as PrinterConnectionTestResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function useDiscoveredPrinter(candidate: DiscoveredPrinter) {
    setNewPrinterName(candidate.name);
    setNewPrinterUrl(candidate.moonraker_url);
    setNewPrinterSshHost(extractHost(candidate.moonraker_url));
    setPrinterConnectionTest(null);
  }

  function openCreatePrinterModal() {
    setPrinterModalMode("create");
    setEditingPrinterId(null);
    setNewPrinterName("Voron - Mayder");
    setNewPrinterUrl("http://voron.local:7125");
    setNewPrinterSshHost("");
    setNewPrinterSshPort(22);
    setNewPrinterSshUser("");
    setNewPrinterSshCredential("");
    setDiscovery(null);
    setPrinterConnectionTest(null);
    setPrinterModalOpen(true);
  }

  function openEditPrinterModal(printer: PrinterRecord) {
    setPrinterModalMode("edit");
    setEditingPrinterId(printer.id);
    setNewPrinterName(printer.name);
    setNewPrinterUrl(printer.moonraker_url);
    setNewPrinterSshHost(printer.ssh_host ?? extractHost(printer.moonraker_url));
    setNewPrinterSshPort(printer.ssh_port ?? 22);
    setNewPrinterSshUser(printer.ssh_username ?? "");
    setNewPrinterSshCredential("");
    setDiscovery(null);
    setPrinterConnectionTest(null);
    setPrinterModalOpen(true);
  }

  async function loadSelectedPrinterStatus() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/moonraker/status`);
      const payload = (await response.json()) as MoonrakerStatus;
      setStatus(payload);
      await loadOperationStatus(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
      await loadUpdateStatus(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function captureSnapshot() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/snapshots/moonraker`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadSnapshots(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadSnapshots(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/snapshots`);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { snapshots: SnapshotRecord[] };
    setSnapshots(payload.snapshots);
    setSnapshotDiff(null);
    if (payload.snapshots.length >= 2) {
      setFromSnapshotId(payload.snapshots[1].id);
      setToSnapshotId(payload.snapshots[0].id);
    } else {
      setFromSnapshotId(payload.snapshots[0]?.id ?? null);
      setToSnapshotId(payload.snapshots[0]?.id ?? null);
    }
  }

  async function loadPrinterHealth(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/health`);
    if (!response.ok) {
      return;
    }
    setHealth((await response.json()) as HealthResponse);
  }

  async function loadUpdateStatus(printerId: number): Promise<UpdateStatusResponse | null> {
    const response = await fetch(`/api/printers/${printerId}/updates/status`);
    if (!response.ok) {
      return null;
    }
    const status = (await response.json()) as UpdateStatusResponse;
    setUpdateStatus(status);
    setError(null);
    return status;
  }

  async function refreshUpdateStatus(componentName?: string) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    setUpdateActionResult(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/updates/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: componentName ?? null }),
      });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      setUpdateActionResult((await response.json()) as UpdateActionResponse);
      await loadUpdateStatus(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function appendUpdateLog(level: UpdateLogEntry["level"], message: string) {
    const id = updateLogIdRef.current + 1;
    updateLogIdRef.current = id;
    setUpdateLogs((currentLogs) => [
      ...currentLogs,
      {
        id,
        level,
        message,
        time: new Date().toLocaleTimeString("pt-BR", { hour12: false }),
      },
    ]);
  }

  function openUpdateDialog(target: string) {
    if (!selectedPrinterId) {
      return;
    }
    const selectedLabel = target === "all" ? "todos os componentes" : target;
    setError(null);
    setUpdateActionResult(null);
    setUpdateLogs([]);
    updateLogIdRef.current = 0;
    setUpdateDialog({ open: true, target, label: selectedLabel, phase: "confirm" });
  }

  function closeUpdateSocket() {
    updateSocketRef.current?.close();
    updateSocketRef.current = null;
  }

  function connectUpdateSocket(printer: PrinterRecord) {
    closeUpdateSocket();
    const websocketUrl = moonrakerWebsocketUrl(printer.moonraker_url);
    if (!websocketUrl) {
      appendUpdateLog("warning", "Nao foi possivel montar a URL WebSocket do Moonraker. O update continua sem log ao vivo.");
      return;
    }
    appendUpdateLog("info", `Conectando ao log ao vivo em ${websocketUrl}`);
    const socket = new WebSocket(websocketUrl);
    updateSocketRef.current = socket;
    socket.onopen = () => {
      socket.send(
        JSON.stringify({
          jsonrpc: "2.0",
          method: "server.connection.identify",
          params: {
            client_name: "Printora",
            version: "0.1.3",
            type: "web",
            url: "https://github.com/printora/printora",
          },
          id: 1,
        }),
      );
      appendUpdateLog("success", "Log ao vivo conectado.");
    };
    socket.onerror = () => appendUpdateLog("warning", "WebSocket do Moonraker indisponivel. O update continua via HTTP.");
    socket.onclose = () => {
      if (updateSocketRef.current === socket) {
        appendUpdateLog("warning", "Conexao de log encerrada. Moonraker pode estar reiniciando.");
      }
    };
    socket.onmessage = (event) => {
      const updateMessage = parseMoonrakerUpdateMessage(event.data);
      if (!updateMessage) {
        return;
      }
      appendUpdateLog(updateMessage.complete ? "success" : "info", updateMessage.message);
      if (updateMessage.complete) {
        setUpdateDialog((currentDialog) =>
          currentDialog && currentDialog.phase === "running" ? { ...currentDialog, phase: "done" } : currentDialog,
        );
      }
    };
  }

  async function runUpdate(target: string) {
    if (!selectedPrinterId || !selectedPrinter) {
      return;
    }
    setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "running" } : currentDialog));
    connectUpdateSocket(selectedPrinter);
    appendUpdateLog("info", `Solicitando update de ${target === "all" ? "todos os componentes" : target}.`);
    setLoading(true);
    setError(null);
    setUpdateActionResult(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/updates/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target }),
      });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const actionResult = (await response.json()) as UpdateActionResponse;
      setUpdateActionResult(actionResult);
      appendUpdateLog("success", actionResult.message);
      await loadUpdateStatus(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
      setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "done" } : currentDialog));
    } catch (err) {
      const latestStatus = await reloadUpdateStatusAfterUpdateError(selectedPrinterId, target);
      await loadPrinterHealth(selectedPrinterId);
      if (isUpdateTargetConfirmedUpdated(latestStatus, target)) {
        setUpdateActionResult({
          safe_mode: "moonraker_update_manager",
          action: "update",
          target,
          accepted: true,
          message:
            "Update aplicado. O Moonraker ficou temporariamente indisponível no fim da operação, mas a reanálise confirmou que está atualizado.",
          result: {},
        });
        appendUpdateLog(
          "success",
          "Update confirmado apos reanalise. O erro HTTP provavelmente veio de reinicio temporario do Moonraker.",
        );
        setError(null);
        setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "done" } : currentDialog));
      } else {
        const errorMessage = err instanceof Error ? err.message : "Erro desconhecido";
        appendUpdateLog("error", errorMessage);
        setError(errorMessage);
        setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "failed" } : currentDialog));
      }
    } finally {
      setLoading(false);
    }
  }

  async function reloadUpdateStatusAfterUpdateError(printerId: number, target: string): Promise<UpdateStatusResponse | null> {
    const retryDelaysMs = [0, 1500, 3500];
    let latestStatus: UpdateStatusResponse | null = null;
    for (const retryDelayMs of retryDelaysMs) {
      if (retryDelayMs > 0) {
        appendUpdateLog("info", "Revalidando status do Update Manager apos indisponibilidade temporaria.");
        await delay(retryDelayMs);
      }
      try {
        latestStatus = await loadUpdateStatus(printerId);
      } catch {
        latestStatus = null;
      }
      if (isUpdateTargetConfirmedUpdated(latestStatus, target)) {
        return latestStatus;
      }
    }
    return latestStatus;
  }

  async function loadBackups(printerId: number) {
    const [policiesResponse, runsResponse] = await Promise.all([
      fetch(`/api/printers/${printerId}/backup/policies`),
      fetch(`/api/printers/${printerId}/backup/runs`),
    ]);
    if (policiesResponse.ok) {
      const payload = (await policiesResponse.json()) as { policies: BackupPolicyRecord[] };
      setBackupPolicies(payload.policies);
    }
    if (runsResponse.ok) {
      const payload = (await runsResponse.json()) as { runs: BackupRunRecord[] };
      setBackupRuns(payload.runs);
    }
  }

  async function loadSanitizedReport() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/reports/sanitized`);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setSanitizedReport((await response.json()) as SanitizedReport);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadMaintenance(printerId: number, refreshPrintHours = true) {
    const [eventsResponse, tasksResponse, summaryResponse] = await Promise.all([
      fetch(`/api/printers/${printerId}/maintenance/events`),
      fetch(`/api/printers/${printerId}/maintenance/tasks`),
      fetch(`/api/printers/${printerId}/maintenance/summary`),
    ]);
    let loadedTasks: MaintenanceTaskRecord[] | null = null;
    let loadedSummary: MaintenanceSummary | null = null;
    if (eventsResponse.ok) {
      const payload = (await eventsResponse.json()) as { events: MaintenanceEventRecord[] };
      setMaintenanceEvents(payload.events);
    }
    if (tasksResponse.ok) {
      const payload = (await tasksResponse.json()) as { tasks: MaintenanceTaskRecord[] };
      loadedTasks = payload.tasks;
      setMaintenanceTasks(payload.tasks);
    }
    if (summaryResponse.ok) {
      loadedSummary = (await summaryResponse.json()) as MaintenanceSummary;
      setMaintenanceSummary(loadedSummary);
    }
    if (loadedTasks?.length === 0 && loadedSummary && loadedSummary.recommended_tasks.length > 0) {
      const response = await fetch(`/api/printers/${printerId}/maintenance/tasks/defaults`, { method: "POST" });
      if (response.ok) {
        await loadMaintenance(printerId);
      }
    }
    if (refreshPrintHours) {
      void fetch(`/api/printers/${printerId}/maintenance/print-hours`)
        .then(async (response) => {
          if (!response.ok) {
            setMaintenancePrintHours({ available: false, total_print_hours: null, source: "unavailable" });
            return undefined;
          }
          const payload = (await response.json()) as MaintenancePrintHoursStatus;
          setMaintenancePrintHours(payload);
          return loadMaintenance(printerId, false);
        })
        .catch(() => setMaintenancePrintHours({ available: false, total_print_hours: null, source: "unavailable" }));
    }
  }

  async function loadZOffsets(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/z-offsets`);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { records: ZOffsetRecord[] };
    setZOffsetRecords(payload.records);
  }

  async function loadCanRecords(printerId: number) {
    const [recordsResponse, summaryResponse] = await Promise.all([
      fetch(`/api/printers/${printerId}/can/records`),
      fetch(`/api/printers/${printerId}/can/summary`),
    ]);
    if (recordsResponse.ok) {
      const payload = (await recordsResponse.json()) as { records: CanBusRecord[] };
      setCanRecords(payload.records);
    }
    if (summaryResponse.ok) {
      setCanSummary((await summaryResponse.json()) as CanBusSummary);
    }
  }

  async function loadPluginAudit(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/plugins/audit`);
    if (!response.ok) {
      return;
    }
    setPluginAudit((await response.json()) as PluginAuditResponse);
  }

  async function loadBoardPresets() {
    const response = await fetch("/api/firmware/board-presets");
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { presets: BoardPreset[] };
    setBoardPresets(payload.presets);
  }

  async function loadFirmwareBoards(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/firmware/boards`);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { boards: FirmwareBoardRecord[] };
    setFirmwareBoards(payload.boards);
  }

  async function loadFirmwareBuildRuns(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/firmware/build-runs`);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { runs: FirmwareBuildRunRecord[] };
    setFirmwareBuildRuns(payload.runs);
  }

  async function loadFirmwareFlashRuns(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/firmware/flash-runs`);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { runs: FirmwareFlashRunRecord[] };
    setFirmwareFlashRuns(payload.runs);
  }

  async function loadCalibrationTests(printerId?: number) {
    const response = await fetch(printerId ? `/api/printers/${printerId}/calibration/available-tests` : "/api/calibration/tests");
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { tests: CalibrationTestRecord[] } | CalibrationAvailableTestsResponse;
    setCalibrationTests(payload.tests);
    setCalibrationHiddenTests("hidden_tests" in payload ? payload.hidden_tests : []);
    setCalibrationTestKey((current) => {
      if (current && payload.tests.some((test) => test.test_key === current)) {
        return current;
      }
      return payload.tests[0]?.test_key || "";
    });
  }

  async function loadCalibrationRuns(printerId: number) {
    const [runsResponse, summaryResponse, sequenceResponse, executionsResponse] = await Promise.all([
      fetch(`/api/printers/${printerId}/calibration/runs`),
      fetch(`/api/printers/${printerId}/calibration/summary`),
      fetch(`/api/printers/${printerId}/calibration/sequence`),
      fetch(`/api/printers/${printerId}/calibration/executions`),
    ]);
    if (runsResponse.ok) {
      const payload = (await runsResponse.json()) as { runs: CalibrationRunRecord[] };
      setCalibrationRuns(payload.runs);
    }
    if (summaryResponse.ok) {
      setCalibrationSummary((await summaryResponse.json()) as CalibrationSummary);
    }
    if (sequenceResponse.ok) {
      setCalibrationSequence((await sequenceResponse.json()) as CalibrationSequencePlan);
    }
    if (executionsResponse.ok) {
      const payload = (await executionsResponse.json()) as { executions: CalibrationExecutionRecord[] };
      setCalibrationExecutions(payload.executions);
    }
  }

  async function createCalibrationRun(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/calibration/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          test_key: calibrationTestKey,
          result_status: calibrationResultStatus,
          material: calibrationMaterial,
          plate_name: calibrationPlateName,
          nozzle: calibrationNozzle,
          observed_value: calibrationObservedValue,
          notes: calibrationNotes,
          gcode_reviewed: calibrationGcodeReviewed,
          photo_reference: calibrationPhotoReference || null,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationObservedValue("");
      setCalibrationNotes("");
      setCalibrationGcodeReviewed(false);
      setCalibrationPhotoReference("");
      setCalibrationResultTestKey(null);
      setCalibrationResultFormOpen(false);
      setCalibrationActivityCleared(false);
      await loadCalibrationRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadCalibrationPreflight() {
    if (!selectedPrinterId || !calibrationTestKey) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/printers/${selectedPrinterId}/calibration/tests/${encodeURIComponent(calibrationTestKey)}/preflight`,
      );
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationPreflight((await response.json()) as CalibrationPreflight);
      setCalibrationExecutionResult(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function openCalibrationExecute(test: CalibrationTestRecord) {
    setCalibrationTestKey(test.test_key);
    setCalibrationExecuteTestKey(test.test_key);
    setCalibrationExecutionResult(null);
    setCalibrationPreflight(null);
    setCalibrationGcodeReviewed(false);
    setCalibrationOperatorPresent(false);
    setCalibrationExecutionConfirmation("");
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/printers/${selectedPrinterId}/calibration/tests/${encodeURIComponent(test.test_key)}/preflight`,
      );
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationPreflight((await response.json()) as CalibrationPreflight);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function openCalibrationResult(
    test: CalibrationTestRecord,
    showForm = false,
    resultStatus: CalibrationRunRecord["result_status"] = "passed",
  ) {
    const formConfig = getCalibrationResultFormConfig(test);
    setCalibrationTestKey(test.test_key);
    setCalibrationResultTestKey(test.test_key);
    setCalibrationResultFormOpen(showForm);
    setCalibrationResultStatus(resultStatus);
    setCalibrationObservedValue("");
    setCalibrationNotes("");
    setCalibrationPhotoReference("");
    setCalibrationGcodeReviewed(test.gcode.length === 0);
    if (!formConfig.showMaterial) {
      setCalibrationMaterial("");
    } else if (!calibrationMaterial.trim()) {
      setCalibrationMaterial("PLA");
    }
    if (!formConfig.showPlate) {
      setCalibrationPlateName("");
    } else if (!calibrationPlateName.trim()) {
      setCalibrationPlateName("Texturizada");
    }
    if (!formConfig.showNozzle) {
      setCalibrationNozzle("");
    } else if (!calibrationNozzle.trim()) {
      setCalibrationNozzle("T0");
    }
  }

  async function executeCalibrationGcode(confirmationOverride?: string) {
    if (!selectedPrinterId || !calibrationTestKey) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/calibration/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          test_key: calibrationTestKey,
          confirmation: confirmationOverride ?? calibrationExecutionConfirmation,
          operator_present: calibrationOperatorPresent,
          gcode_reviewed: calibrationGcodeReviewed,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = (await response.json()) as CalibrationExecutionRecord;
      setCalibrationExecutionResult(payload);
      setCalibrationActivityCleared(false);
      await loadCalibrationRuns(selectedPrinterId);
      if (payload.status === "executed") {
        setCalibrationOperatorPresent(false);
        setCalibrationGcodeReviewed(false);
        setCalibrationExecutionConfirmation("");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createFirmwareBoard(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/firmware/boards`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: firmwareBoardName,
          preset_id: firmwareBoardPresetId,
          can_uuid: firmwareBoardCanUuid || null,
          can_interface: firmwareBoardCanInterface,
          config_file: firmwareBoardConfigFile || null,
          notes: firmwareBoardNotes,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareBoardNotes("");
      await loadFirmwareBoards(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createFirmwareBuildDryRun(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/firmware/boards/${boardId}/build-runs/dry-run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          klipper_path: firmwareKlipperPath,
          output_root: firmwareOutputRoot,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareBuildRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function validateFirmwareBuildPreflight(boardId: number) {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/firmware/boards/${boardId}/build-runs/preflight`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          klipper_path: firmwareKlipperPath,
          output_root: firmwareOutputRoot,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareBuildPreflight((await response.json()) as FirmwareBuildPreflight);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function executeFirmwareBuildLocal(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/firmware/boards/${boardId}/build-runs/execute-local`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          klipper_path: firmwareKlipperPath,
          output_root: firmwareOutputRoot,
          confirmation: firmwareBuildConfirmation,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareBuildRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createFirmwareFlashDryRun(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const latestBuildRun = firmwareBuildRuns.find((run) => run.board_id === boardId);
      const response = await fetch(`/api/firmware/boards/${boardId}/flash-runs/dry-run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          build_run_id: latestBuildRun?.id ?? null,
          binary_path: firmwareFlashBinaryPath || null,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareFlashRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function validateFirmwareFlashPreflight(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const latestBuildRun = firmwareBuildRuns.find((run) => run.board_id === boardId);
      const response = await fetch(`/api/firmware/boards/${boardId}/flash-runs/preflight`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          build_run_id: latestBuildRun?.id ?? null,
          binary_path: firmwareFlashBinaryPath || null,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareFlashPreflight((await response.json()) as FirmwareFlashPreflight);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function validateFirmwareFlashGate(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const latestBuildRun = firmwareBuildRuns.find((run) => run.board_id === boardId);
      const response = await fetch(`/api/firmware/boards/${boardId}/flash-runs/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          build_run_id: latestBuildRun?.id ?? null,
          binary_path: firmwareFlashBinaryPath || null,
          confirmation: firmwareFlashConfirmation,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareFlashRuns(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function loadFirmwareRecoveryPlan(boardId: number) {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/firmware/boards/${boardId}/recovery-plan`);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareRecoveryPlan((await response.json()) as FirmwareRecoveryPlan);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createCanRecord(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/can/records`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          interface_name: canInterfaceName,
          rx_error: canRxError,
          tx_error: canTxError,
          tx_retries: canTxRetries,
          bus_state: canBusState,
          bitrate: canBitrate,
          notes: canNotes,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCanNotes("");
      setCanRawOutput("");
      await loadCanRecords(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function parseCanRawOutput() {
    if (!selectedPrinterId || !canRawOutput.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/can/parse`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ interface_name: canInterfaceName, output: canRawOutput }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const parsed = (await response.json()) as {
        interface_name: string;
        rx_error: number;
        tx_error: number;
        tx_retries: number;
        bus_state?: string | null;
        bitrate?: number | null;
        notes: string;
      };
      setCanInterfaceName(parsed.interface_name);
      setCanRxError(parsed.rx_error);
      setCanTxError(parsed.tx_error);
      setCanTxRetries(parsed.tx_retries);
      setCanBusState(parsed.bus_state ?? "");
      setCanBitrate(parsed.bitrate ?? 1000000);
      setCanNotes(parsed.notes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function compareLatestCanRecords() {
    if (!selectedPrinterId || canRecords.length < 2) {
      return;
    }
    const pair = findLatestComparableCanRecords(canRecords);
    if (!pair) {
      setError("Não há duas leituras da mesma interface CAN para comparar.");
      return;
    }
    const { after, before } = pair;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        before_record_id: String(before.id),
        after_record_id: String(after.id),
      });
      const response = await fetch(`/api/printers/${selectedPrinterId}/can/compare?${params.toString()}`);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCanComparison((await response.json()) as CanBusRecordComparison);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function findLatestComparableCanRecords(records: CanBusRecord[]) {
    for (let afterIndex = 0; afterIndex < records.length; afterIndex += 1) {
      const after = records[afterIndex];
      const before = records.slice(afterIndex + 1).find((record) => record.interface_name === after.interface_name);
      if (before) {
        return { after, before };
      }
    }
    return null;
  }

  async function createZOffsetRecord(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    const parsedOffset = Number(zOffsetValue);
    if (!zOffsetPlateName.trim() || !zOffsetMaterial.trim() || !zOffsetNozzle.trim() || !Number.isFinite(parsedOffset)) {
      setError("Preencha chapa, material, toolhead e um Z-offset válido antes de registrar.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/z-offsets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plate_name: zOffsetPlateName.trim(),
          material: zOffsetMaterial.trim(),
          nozzle: zOffsetNozzle.trim(),
          offset_value: parsedOffset,
          notes: zOffsetNotes,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setZOffsetNotes("");
      setZOffsetFormOpen(false);
      setZOffsetWizardPlan(null);
      setZOffsetWizardChecks({});
      await loadZOffsets(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function evaluateZOffsetWizard() {
    if (!selectedPrinterId) {
      return;
    }
    const parsedOffset = Number(zOffsetValue);
    if (!zOffsetPlateName.trim() || !zOffsetMaterial.trim() || !zOffsetNozzle.trim() || !Number.isFinite(parsedOffset)) {
      setError("Preencha chapa, material, toolhead e um Z-offset válido antes de avaliar.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const query = new URLSearchParams({
        plate_name: zOffsetPlateName.trim(),
        material: zOffsetMaterial.trim(),
        nozzle: zOffsetNozzle.trim(),
        proposed_offset_value: String(parsedOffset),
      });
      const response = await fetch(`/api/printers/${selectedPrinterId}/z-offsets/wizard-plan?${query.toString()}`);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const plan = (await response.json()) as ZOffsetWizardPlan;
      setZOffsetWizardPlan(plan);
      setZOffsetWizardChecks(
        Object.fromEntries(plan.steps.filter((step) => step.must_confirm).map((step) => [step.key, false])),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  function toggleWizardCheck(key: string) {
    setZOffsetWizardChecks((current) => ({ ...current, [key]: !current[key] }));
  }

  function openMaintenanceDoneModal(task: MaintenanceTaskRecord) {
    setMaintenanceDoneTask(task);
    setMaintenanceDoneNotes("");
    setMaintenanceDoneIntervalKind(task.interval_kind);
    setMaintenanceDoneIntervalValue(task.is_active ? formatMaintenanceIntervalValue(task) : "");
    setMaintenanceDoneDisableReminder(!task.is_active);
  }

  function openMaintenanceFreeModal() {
    setMaintenanceEventType("");
    setMaintenanceComponent("");
    setMaintenanceTitle("");
    setMaintenanceNotes("");
    setMaintenanceFreeReminderEnabled(false);
    setMaintenanceFreeIntervalKind("days");
    setMaintenanceFreeIntervalValue("");
    setMaintenanceFreeModalOpen(true);
  }

  async function completeMaintenanceTask(
    taskId: number,
    notes = "Concluído pelo painel Printora.",
    nextIntervalKind?: "days" | "print_hours" | null,
    nextIntervalValue?: number | null,
    disableReminder = false,
  ): Promise<boolean> {
    if (!selectedPrinterId) {
      return false;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/maintenance/tasks/${taskId}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          notes,
          next_interval_kind: nextIntervalKind ?? null,
          next_interval_value: nextIntervalValue ?? null,
          next_interval_days: nextIntervalKind === "days" ? nextIntervalValue ?? null : null,
          disable_reminder: disableReminder,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
      return false;
    } finally {
      setLoading(false);
    }
  }

  async function submitMaintenanceDone(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!maintenanceDoneTask) {
      return;
    }
    const interval = maintenanceDoneDisableReminder || !maintenanceDoneIntervalValue.trim()
      ? null
      : Number(maintenanceDoneIntervalValue);
    if (!maintenanceDoneDisableReminder && maintenanceDoneIntervalKind === "print_hours" && !maintenancePrintHours?.available) {
      setError("Horas de impressão indisponíveis. Ligue a impressora para usar lembrete por horas.");
      return;
    }
    const completed = await completeMaintenanceTask(
      maintenanceDoneTask.id,
      maintenanceDoneNotes.trim() || "Manutenção realizada.",
      maintenanceDoneDisableReminder || interval === null ? null : maintenanceDoneIntervalKind,
      interval,
      maintenanceDoneDisableReminder || !maintenanceDoneIntervalValue.trim(),
    );
    if (!completed) {
      return;
    }
    setMaintenanceDoneTask(null);
    setMaintenanceDoneNotes("");
    setMaintenanceDoneIntervalKind("days");
    setMaintenanceDoneIntervalValue("");
    setMaintenanceDoneDisableReminder(false);
  }

  async function deleteLatestMaintenanceTaskEvent(taskId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/maintenance/tasks/${taskId}/latest-event`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createDefaultMaintenanceTasks() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/maintenance/tasks/defaults`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function submitMaintenanceFreeEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId || !maintenanceEventType || !maintenanceComponent.trim() || !maintenanceTitle.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const performedAt = new Date().toISOString();
      const response = await fetch(`/api/printers/${selectedPrinterId}/maintenance/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: maintenanceEventType,
          component: maintenanceComponent.trim(),
          title: maintenanceTitle.trim(),
          notes: maintenanceNotes,
          performed_at: performedAt,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const reminderValue = maintenanceFreeReminderEnabled && maintenanceFreeIntervalValue.trim()
        ? Number(maintenanceFreeIntervalValue)
        : null;
      if (maintenanceFreeReminderEnabled && maintenanceFreeIntervalKind === "print_hours" && !maintenancePrintHours?.available) {
        throw new Error("Horas de impressão indisponíveis. Ligue a impressora para usar lembrete por horas.");
      }
      if (reminderValue) {
        const taskResponse = await fetch(`/api/printers/${selectedPrinterId}/maintenance/tasks`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: maintenanceTitle,
            component: maintenanceComponent.trim(),
            interval_days: maintenanceFreeIntervalKind === "days" ? reminderValue : 30,
            interval_kind: maintenanceFreeIntervalKind,
            interval_value: reminderValue,
            last_done_at: performedAt,
          }),
        });
        if (!taskResponse.ok) {
          throw new Error(await taskResponse.text());
        }
      }
      setMaintenanceEventType("");
      setMaintenanceComponent("");
      setMaintenanceTitle("");
      setMaintenanceNotes("");
      setMaintenanceFreeReminderEnabled(false);
      setMaintenanceFreeIntervalKind("days");
      setMaintenanceFreeIntervalValue("");
      setMaintenanceFreeModalOpen(false);
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function deleteMaintenanceEvent(eventId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/maintenance/events/${eventId}`, {
        method: "DELETE",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createBackupPolicy(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/backup/policies`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: backupName,
          source_path: backupSourcePath,
          destination_path: backupDestinationPath,
          dry_run_only: backupDryRunOnly,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function executeLocalBackup(policyId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/backup/policies/${policyId}/execute-local`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createBackupDryRun(policyId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/backup/policies/${policyId}/dry-run`, {
        method: "POST",
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function compareBackupArchives() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/backup/archives/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_archive_path: backupCompareBasePath,
          target_archive_path: backupCompareTargetPath,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setBackupCompareResult((await response.json()) as BackupArchiveCompareResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createBackupRestorePlan() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/backup/restore-plan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          archive_path: backupRestoreArchivePath,
          restore_root: backupRestoreRoot,
          files: backupRestoreFiles.split("\n").map((item) => item.trim()).filter(Boolean),
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setBackupRestorePlan((await response.json()) as BackupRestorePlanResponse);
      setBackupRestoreGate(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function validateBackupRestoreGate() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/backup/restore-gate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          archive_path: backupRestoreArchivePath,
          restore_root: backupRestoreRoot,
          files: backupRestoreFiles.split("\n").map((item) => item.trim()).filter(Boolean),
          confirmation: backupRestoreConfirmation,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setBackupRestoreGate((await response.json()) as BackupRestoreGateResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function compareSnapshots() {
    if (!selectedPrinterId || !fromSnapshotId || !toSnapshotId || fromSnapshotId === toSnapshotId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/printers/${selectedPrinterId}/snapshots/diff?from_id=${fromSnapshotId}&to_id=${toSnapshotId}`,
      );
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setSnapshotDiff((await response.json()) as SnapshotDiff);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  React.useEffect(() => {
    void loadStatus();
  }, []);

  React.useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem("printora-theme", theme);
  }, [theme]);

  React.useEffect(() => {
    if (!selectedPrinterId || !["calibration", "tests"].includes(activeSection)) {
      return;
    }
    void loadCalibrationTests(selectedPrinterId);
    void loadCalibrationRuns(selectedPrinterId);
    if (activeSection === "calibration") {
      void loadOperationStatus(selectedPrinterId);
      void loadZOffsets(selectedPrinterId);
    }
  }, [activeSection, selectedPrinterId]);

  React.useEffect(() => () => closeUpdateSocket(), []);

  const activeSectionMeta = appSections.find((section) => section.key === activeSection) ?? appSections[0];
  const selectedPrinter = printers.find((printer) => printer.id === selectedPrinterId);
  const selectedCalibrationTest = calibrationTests.find((test) => test.test_key === calibrationTestKey) ?? calibrationTests[0];
  const calibrationHelpTest = calibrationTests.find((test) => test.test_key === calibrationHelpTestKey);
  const calibrationExecuteTest = calibrationTests.find((test) => test.test_key === calibrationExecuteTestKey);
  const calibrationResultTest = calibrationTests.find((test) => test.test_key === calibrationResultTestKey);
  const calibrationResultFormConfig = calibrationResultTest
    ? getCalibrationResultFormConfig(calibrationResultTest)
    : null;
  const calibrationResultRuns = calibrationResultTest
    ? calibrationRuns.filter((run) => run.test_key === calibrationResultTest.test_key)
    : [];
  const calibrationResultExecutions = calibrationResultTest
    ? calibrationExecutions.filter((execution) => execution.test_key === calibrationResultTest.test_key)
    : [];
  const calibrationVisibleGcodeCount = calibrationTests.filter((test) => test.gcode.length > 0).length;
  const calibrationBlockedGcodeCount = calibrationHiddenTests.length;
  const calibrationRecommended = calibrationSummary?.recommended_next_tests.slice(0, 5) ?? [];
  const hiddenCalibrationKeys = new Set(calibrationHiddenTests.map((test) => test.test_key));
  const calibrationSequencePreview = (calibrationSequence?.steps ?? []).filter((step) => !hiddenCalibrationKeys.has(step.test_key));
  const visibleCalibrationCompletedSteps = calibrationSequencePreview.filter((step) => step.status === "completed" || step.status === "skipped").length;
  const visibleCalibrationRecommendations = calibrationRecommended.filter((test) => !hiddenCalibrationKeys.has(test.test_key));
  const visibleCalibrationTests = calibrationTests.filter((test) => {
    if (testFilter === "executable") {
      return test.gcode.length > 0;
    }
    if (testFilter === "manual") {
      return test.gcode.length === 0;
    }
    return testFilter !== "blocked";
  });
  const visibleHiddenCalibrationTests = testFilter === "all" || testFilter === "blocked" ? calibrationHiddenTests : [];
  const visibleMaintenanceTasks = maintenanceTasks.filter((task) => {
    if (maintenanceFilter === "all") {
      return true;
    }
    return task.due_status === maintenanceFilter;
  });
  const nextMaintenanceTask = maintenanceSummary?.next_due_task;
  const maintenancePrintHoursAvailable =
    maintenancePrintHours?.available && typeof maintenancePrintHours.total_print_hours === "number";
  const maintenanceHoursDisabledMessage = "Horas de impressão indisponíveis. Ligue a impressora para habilitar.";
  const visibleFirmwareBoards = firmwareBoards.filter((board) => {
    if (firmwareFilter === "can") {
      return board.connection_type === "can" || board.connection_type === "usb_can_bridge";
    }
    if (firmwareFilter === "usb") {
      return board.connection_type === "usb";
    }
    return true;
  });
  const hotendTemperature = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("extruder"));
  const bedTemperature = operationStatus?.temperatures.find((item) => item.name.toLowerCase().includes("bed"));
  const recentCalibrationActivityCount =
    (calibrationExecutionResult ? 1 : 0) + calibrationExecutions.slice(0, 4).length + calibrationRuns.slice(0, 4).length;
  const ActiveIcon = activeSectionMeta.icon;
  const ThemeIcon = theme === "dark" ? Sun : Moon;
  const alertCenterItems = buildAlertCenterItems({ health, updateStatus, checklist, audit });
  const alertCount = alertCenterItems.length;
  const latestSnapshot = snapshots[0];
  const moonrakerOnline = health?.connected ?? status?.connected ?? false;
  const selectedPrinterOnline = Boolean(selectedPrinterId && moonrakerOnline);
  const visibleNavGroups = React.useMemo(
    () =>
      navGroups
        .map((group) => ({
          ...group,
          sections: group.sections.filter((sectionKey) => {
            if (onlinePrinterSections.has(sectionKey)) {
              return selectedPrinterOnline;
            }
            if (selectedPrinterLocalSections.has(sectionKey)) {
              return Boolean(selectedPrinterId);
            }
            return true;
          }),
        }))
        .filter((group) => group.sections.length > 0),
    [selectedPrinterId, selectedPrinterOnline],
  );
  const operationState = operationStatus?.miscellaneous.print_state ?? status?.printer?.state ?? health?.metrics.klipper_state ?? "-";
  const riskClass = overviewRiskClass(health?.decision);
  const riskLabel = formatDecision(health?.decision);
  const lastReadingLabel = latestSnapshot
    ? `Snapshot #${latestSnapshot.id} · ${latestSnapshot.created_at}`
    : health?.data_state
      ? formatChecklistDataState(health.data_state)
      : "Sem leitura";
  const topbarAlertTone = alertCenterItems.some((item) => item.severity === "blocker")
    ? "danger"
    : alertCenterItems.some((item) => item.severity === "warning")
      ? "warning"
      : "ok";
  const topbarPrimaryAction = (() => {
    if (activeSection === "printers") {
      return {
        icon: Plus,
        label: "Adicionar",
        disabled: loading,
        run: openCreatePrinterModal,
      };
    }
    if (activeSection === "reports") {
      return {
        icon: Camera,
        label: "Snapshot",
        disabled: !selectedPrinterId || loading,
        run: captureSnapshot,
      };
    }
    if (activeSection === "updates") {
      return {
        icon: RefreshCw,
        label: "Reanalisar",
        disabled: !selectedPrinterId || loading || Boolean(updateStatus?.busy),
        run: () => refreshUpdateStatus(),
      };
    }
    if (activeSection === "settings") {
      return {
        icon: Settings,
        label: selectedPrinter ? "Editar" : "Adicionar",
        disabled: loading,
        run: () => (selectedPrinter ? openEditPrinterModal(selectedPrinter) : openCreatePrinterModal()),
      };
    }
    return {
      icon: RefreshCw,
      label: loading ? "Atualizando" : "Atualizar",
      disabled: loading || (!selectedPrinterId && activeSection !== "overview"),
      run: () => (selectedPrinterId ? loadSelectedPrinterStatus() : loadStatus()),
    };
  })();
  const TopbarPrimaryIcon = topbarPrimaryAction.icon;

  React.useEffect(() => {
    if (onlinePrinterSections.has(activeSection) && !selectedPrinterOnline) {
      setActiveSection("overview");
      return;
    }
    if (selectedPrinterLocalSections.has(activeSection) && !selectedPrinterId) {
      setActiveSection("overview");
    }
  }, [activeSection, selectedPrinterId, selectedPrinterOnline]);

  return (
    <main className="app-shell">
      <aside className={`sidebar ${mobileNavOpen ? "open" : ""}`} aria-label="Navegação principal">
        <div className="brand">
          <div className="brand-mark">
            <img src="/brand/printora-icon-app-color.png" alt="" />
          </div>
          <div>
            <strong>Printora</strong>
            <span>Klipper Ops</span>
          </div>
          <button type="button" className="icon-button sidebar-close" onClick={() => setMobileNavOpen(false)} aria-label="Fechar menu">
            <X size={18} />
          </button>
        </div>
        <nav className="sidebar-nav">
          {visibleNavGroups.map((group) => (
            <div key={group.title} className="nav-group">
              <span className="nav-group-title">{group.title}</span>
              {group.sections.map((sectionKey) => {
                const section = appSections.find((candidate) => candidate.key === sectionKey);
                if (!section) {
                  return null;
                }
                const Icon = section.icon;
                return (
                  <button
                    key={section.key}
                    type="button"
                    className={`nav-button ${activeSection === section.key ? "active" : ""}`}
                    onClick={() => {
                      setActiveSection(section.key);
                      setMobileNavOpen(false);
                    }}
                  >
                    <span className="nav-icon">
                      <Icon size={17} strokeWidth={2.2} />
                    </span>
                    <span>{section.label}</span>
                  </button>
                );
              })}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span>Impressora ativa</span>
          <strong>{selectedPrinter?.name ?? "não selecionada"}</strong>
          <small>{selectedPrinter?.moonraker_url ?? "Cadastre ou selecione uma impressora."}</small>
        </div>
      </aside>
      {mobileNavOpen ? <button type="button" className="sidebar-backdrop" onClick={() => setMobileNavOpen(false)} aria-label="Fechar menu" /> : null}

      <div className={`workspace section-${activeSection}`}>
        <header className="topbar">
          <div className="topbar-title">
            <button type="button" className="icon-button mobile-menu-button" onClick={() => setMobileNavOpen(true)} aria-label="Abrir menu">
              <Menu size={18} />
            </button>
            <span className="section-icon">
              <ActiveIcon size={18} strokeWidth={2.2} />
            </span>
            <div>
              <h1>{activeSectionMeta.label}</h1>
            </div>
          </div>
          <div className="topbar-actions">
            <label className="topbar-printer context-select" aria-label="Impressora ativa">
              <select
                value={selectedPrinterId ?? ""}
                onChange={(event) => selectPrinter(Number(event.target.value))}
              >
                <option value="" disabled>
                  Selecione uma impressora
                </option>
                {printers.map((printer) => (
                  <option key={printer.id} value={printer.id}>
                    {printer.name}
                  </option>
                ))}
              </select>
            </label>
            <button
              type="button"
              className={`icon-button topbar-alert ${topbarAlertTone}`}
              title="Alertas"
              aria-label={alertCount > 0 ? `${alertCount} alerta(s)` : "Sem alertas"}
              onClick={() => setAlertCenterOpen(true)}
            >
              <Bell size={16} />
              {alertCount > 0 ? <strong>{alertCount}</strong> : null}
            </button>
            <button
              type="button"
              className="icon-button"
              title={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
              aria-label={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
              onClick={() => setTheme((currentTheme) => (currentTheme === "dark" ? "light" : "dark"))}
            >
              <ThemeIcon size={18} />
            </button>
            <button
              type="button"
              className="icon-button topbar-primary"
              title={topbarPrimaryAction.label}
              aria-label={topbarPrimaryAction.label}
              onClick={() => void topbarPrimaryAction.run()}
              disabled={topbarPrimaryAction.disabled}
            >
              <TopbarPrimaryIcon size={16} />
            </button>
          </div>
        </header>

        <section className="page-helper">
          <strong>{activeSectionMeta.purpose}</strong>
          <span>
            {activeSection === "settings"
              ? "Configuração global do Printora"
              : selectedPrinter
                ? `Contexto atual: ${selectedPrinter.name}`
                : "Selecione uma impressora para carregar os dados por contexto."}
          </span>
        </section>
        <button type="button" className="primary-button mobile-section-action" onClick={() => void topbarPrimaryAction.run()} disabled={topbarPrimaryAction.disabled}>
          <TopbarPrimaryIcon size={16} />
          {topbarPrimaryAction.label}
        </button>

        {error ? <section className="alert danger">{error}</section> : null}

        {alertCenterOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Central de alertas">
            <div className="modal-card alert-center-card">
              <div className="modal-header">
                <div>
                  <h2>
                    <Bell size={20} />
                    Central de alertas
                  </h2>
                  <p>{selectedPrinter?.name ?? "Impressora não selecionada"} · riscos, updates e avisos consolidados.</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setAlertCenterOpen(false)}>
                  <X size={16} />
                  Fechar
                </button>
              </div>
              <div className="overview-strip">
                <Badge icon={AlertTriangle} label="Bloqueios" value={alertCenterItems.filter((item) => item.severity === "blocker").length} />
                <Badge icon={AlertTriangle} label="Alertas" value={alertCenterItems.filter((item) => item.severity === "warning").length} />
                <Badge icon={RefreshCw} label="Updates" value={countPendingUpdates(updateStatus)} />
                <Badge icon={Bell} label="Total" value={alertCenterItems.length} />
              </div>
              <div className="alert-center-list">
                {alertCenterItems.length === 0 ? (
                  <div className="empty-state">
                    <CheckCircle2 size={22} />
                    <strong>Nenhum alerta ativo</strong>
                    <p className="muted">Não há bloqueios, riscos ou updates pendentes nos dados carregados da impressora selecionada.</p>
                  </div>
                ) : null}
                {alertCenterItems.map((item) => (
                  <div key={item.id} className={`alert-center-row ${item.severity}`}>
                    <div className="alert-center-icon">
                      {React.createElement(alertCenterIcon(item.severity), { size: 17 })}
                    </div>
                    <div>
                      <strong>{item.title}</strong>
                      <span>{item.source}</span>
                      <p>{item.detail}</p>
                      <small>{item.action}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : null}

        {printerModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Cadastrar impressora">
            <div className="modal-card">
              <div className="modal-header">
                <div>
                  <h2>{printerModalMode === "edit" ? "Editar impressora" : "Cadastrar impressora"}</h2>
                  <p>Configure Moonraker e, se quiser auditoria completa, o acesso SSH do host.</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setPrinterModalOpen(false)}>
                  Fechar
                </button>
              </div>
              <div className="modal-actions">
                {printerModalMode === "create" ? (
                  <button type="button" className="secondary-button" onClick={() => void discoverPrinters()} disabled={loading}>
                    <Search size={16} />
                    Buscar na rede
                  </button>
                ) : null}
                <button type="button" className="secondary-button" onClick={() => void testPrinterConnections()} disabled={loading}>
                  <Radio size={16} />
                  Testar conexões
                </button>
                <span>
                  {printerModalMode === "create"
                    ? "Buscar usa HTTP GET em `/server/info`, sem G-code e sem cadastro automático."
                    : "Teste seguro: valida Moonraker e porta SSH sem enviar G-code."}
                </span>
              </div>
              {printerModalMode === "create" && discovery ? (
                <div className="discovery-box">
                  <div className="discovery-summary">
                    <strong>
                      {discovery.candidates.length} Moonraker encontrado(s) em {discovery.cidr}
                    </strong>
                    <span>
                      {discovery.scanned_hosts} hosts verificados · modo {discovery.safe_mode}
                    </span>
                  </div>
                  {discovery.warnings.map((warning) => (
                    <small key={warning} className="muted">
                      {warning}
                    </small>
                  ))}
                  <div className="discovery-list">
                    {discovery.candidates.length === 0 ? <p className="muted">Nenhuma impressora encontrada na rede atual.</p> : null}
                    {discovery.candidates.map((candidate) => (
                      <div key={candidate.moonraker_url} className="discovery-row">
                        <div>
                          <strong>{candidate.name}</strong>
                          <span>{candidate.moonraker_url}</span>
                          <small>
                            Klippy: {candidate.klippy_state ?? "-"} · Moonraker: {candidate.moonraker_version ?? "-"}
                          </small>
                        </div>
                        {candidate.already_registered ? (
                          <span className="registered-badge">já cadastrada</span>
                        ) : (
                          <button type="button" onClick={() => useDiscoveredPrinter(candidate)} disabled={loading}>
                            Usar dados
                          </button>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
              {printerConnectionTest ? (
                <div className="connection-test-box">
                  <ConnectionTestRow label="Moonraker" result={printerConnectionTest.moonraker} />
                  <ConnectionTestRow label="SSH" result={printerConnectionTest.ssh} emptyDetail="Preencha host SSH para testar a porta." />
                </div>
              ) : null}
              <form className="printer-access-form" onSubmit={(event) => void createPrinter(event)}>
                <section className="form-section">
                  <div className="form-section-heading">
                    <strong>Conexão Moonraker</strong>
                    <span>Usada para status, snapshots e leitura segura via HTTP.</span>
                  </div>
                  <div className="form-grid two-columns">
                    <label className="form-field">
                      <span>Nome</span>
                      <input
                        aria-label="Nome da impressora"
                        value={newPrinterName}
                        onChange={(event) => setNewPrinterName(event.target.value)}
                        placeholder="Voron 2.4"
                      />
                    </label>
                    <label className="form-field">
                      <span>URL Moonraker</span>
                      <input
                        aria-label="URL Moonraker"
                        value={newPrinterUrl}
                        onChange={(event) => setNewPrinterUrl(event.target.value)}
                        placeholder="http://voron.local:7125"
                      />
                    </label>
                  </div>
                </section>

                <section className="form-section">
                  <div className="form-section-heading">
                    <strong>Acesso SSH</strong>
                    <span>Necessário para auditoria profunda, CAN, systemd, backups locais e firmware.</span>
                  </div>
                  <div className="form-grid ssh-grid">
                    <label className="form-field">
                      <span>Host SSH</span>
                      <input
                        aria-label="Host SSH"
                        value={newPrinterSshHost}
                        onChange={(event) => setNewPrinterSshHost(event.target.value)}
                        placeholder="voron.local"
                      />
                    </label>
                    <label className="form-field compact-field">
                      <span>Porta</span>
                      <input
                        aria-label="Porta SSH"
                        type="number"
                        min="1"
                        max="65535"
                        value={newPrinterSshPort}
                        onChange={(event) => setNewPrinterSshPort(Number(event.target.value))}
                        placeholder="22"
                      />
                    </label>
                    <label className="form-field">
                      <span>Usuário</span>
                      <input
                        aria-label="Usuário SSH"
                        value={newPrinterSshUser}
                        onChange={(event) => setNewPrinterSshUser(event.target.value)}
                        placeholder="pi"
                      />
                    </label>
                    <label className="form-field">
                      <span>{printerModalMode === "edit" ? "Nova senha opcional" : "Senha"}</span>
                      <input
                        aria-label="Senha SSH"
                        type="password"
                        value={newPrinterSshCredential}
                        onChange={(event) => setNewPrinterSshCredential(event.target.value)}
                        placeholder={printerModalMode === "edit" ? "Deixe vazio para manter a atual" : "Senha SSH"}
                      />
                    </label>
                  </div>
                  <small className="form-note">
                    O valor sensível não é retornado pela API. Em edição, deixe a senha vazia para manter a credencial atual.
                  </small>
                </section>

                <div className="modal-footer">
                  <button type="button" className="ghost-button" onClick={() => setPrinterModalOpen(false)}>
                    Cancelar
                  </button>
                  <button type="submit" className="primary-button" disabled={loading || (!maintenanceDoneDisableReminder && maintenanceDoneIntervalKind === "print_hours" && !maintenancePrintHoursAvailable)}>
                    <Plus size={16} />
                    {printerModalMode === "edit" ? "Salvar impressora" : "Cadastrar impressora"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}

        {selfUpdateModalOpen && selfUpdatePlan ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Update do Printora">
            <div className="modal-card self-update-modal-card">
              <div className="modal-header">
                <div>
                  <h2>
                    <ShieldCheck size={20} />
                    Update do Printora
                  </h2>
                  <p>
                    {systemReleases?.installed_version ?? "-"} → {selfUpdatePlan.run.target_tag} ·{" "}
                    {formatSelfUpdateEnvironment(selfUpdatePlan.run.environment)}
                  </p>
                </div>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => setSelfUpdateModalOpen(false)}
                  disabled={selfUpdateApplying || selfUpdateRollingBack}
                >
                  <X size={16} />
                  Fechar
                </button>
              </div>
              <div className="self-update-summary">
                <Metric label="Versão instalada" value={systemReleases?.installed_version ?? "-"} />
                <Metric label="Versão alvo" value={selfUpdatePlan.run.target_tag} />
                <Metric label="Ambiente" value={formatSelfUpdateEnvironment(selfUpdatePlan.run.environment)} />
                <Metric label="Status" value={formatSelfUpdateStatus(selfUpdatePlan.run.status)} />
              </div>
              {selfUpdatePlan.update_supported ? (
                <div className="action-result warning">
                  <strong>Atenção</strong>
                  <span>O Printora pode reiniciar durante o update. Se a conexão cair, aguarde e recarregue a página.</span>
                </div>
              ) : (
                <div className="action-result warning">
                  <strong>Ambiente sem apply automático</strong>
                  <span>Este ambiente ainda não tem aplicação real de update habilitada pelo backend.</span>
                </div>
              )}
              {selfUpdateConnectionLost ? (
                <div className="action-result warning">
                  <strong>O Printora pode estar reiniciando</strong>
                  <span>Aguarde e recarregue.</span>
                </div>
              ) : null}
              {selfUpdateMessage ? (
                <div className="action-result">
                  <strong>Status</strong>
                  <span>{selfUpdateMessage}</span>
                </div>
              ) : null}
              <div className="self-update-backups">
                <strong>Backups previstos</strong>
                <span>Banco: {selfUpdatePlan.run.backup_db_path ?? "~/.local/share/printora/backups/printora.db.before-update-&lt;timestamp&gt;"}</span>
                <span>Projeto anterior: {selfUpdatePlan.run.previous_project_path ?? "~/Printora.previous-update-&lt;timestamp&gt;"}</span>
              </div>
              <div className="update-log-list">
                {selfUpdatePlan.run.steps.map((step) => (
                  <div key={step.id} className={`update-log-row ${selfUpdateStepClass(step.status)}`}>
                    <time>{formatSelfUpdateStepStatus(step.status)}</time>
                    <span>
                      {step.title}
                      {step.log_excerpt ? ` · ${step.log_excerpt}` : ""}
                    </span>
                  </div>
                ))}
              </div>
              {selfUpdatePlan.update_supported && selfUpdatePlan.run.status === "planned" ? (
                <div className="self-update-confirm">
                  <label>
                    Confirmação
                    <input
                      value={selfUpdateConfirmation}
                      onChange={(event) => setSelfUpdateConfirmation(event.target.value)}
                      placeholder="ATUALIZAR PRINTORA"
                    />
                  </label>
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => void applySelfUpdate()}
                    disabled={selfUpdateApplying || selfUpdateConfirmation !== "ATUALIZAR PRINTORA"}
                  >
                    <ShieldAlert size={16} />
                    Aplicar update
                  </button>
                </div>
              ) : null}
              {canRollbackSelfUpdateRun(selfUpdatePlan.run) ? (
                <div className="self-update-confirm">
                  <label>
                    Confirmação de rollback
                    <input
                      value={selfUpdateRollbackConfirmation}
                      onChange={(event) => setSelfUpdateRollbackConfirmation(event.target.value)}
                      placeholder="ROLLBACK PRINTORA"
                    />
                  </label>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => void rollbackSelfUpdate(selfUpdatePlan.run.id)}
                    disabled={selfUpdateRollingBack || selfUpdateRollbackConfirmation !== "ROLLBACK PRINTORA"}
                  >
                    <Undo2 size={16} />
                    Aplicar rollback
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        ) : null}

        {updateDialog?.open ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Atualizar componente">
            <div className="modal-card update-modal-card">
              <div className="modal-header">
                <div>
                  <h2>
                    <RefreshCw size={20} />
                    Atualizar {updateDialog.label}
                  </h2>
                  <p>
                    {selectedPrinter?.name ?? "Impressora"} · {selectedPrinter?.moonraker_url ?? "Moonraker não selecionado"}
                  </p>
                </div>
                <button
                  type="button"
                  className="ghost-button"
                  onClick={() => {
                    closeUpdateSocket();
                    setUpdateDialog(null);
                  }}
                  disabled={updateDialog.phase === "running"}
                >
                  <X size={16} />
                  Fechar
                </button>
              </div>

              {updateDialog.phase === "confirm" ? (
                <div className="update-confirm-box">
                  <div className="finding monitorar">
                    <div>
                      <strong>Confirmação necessária</strong>
                      <span>operação mutável</span>
                    </div>
                    <p>O Moonraker pode reiniciar serviços durante o update. Não execute se houver impressão em andamento.</p>
                    <small>O Printora vai abrir o log ao vivo do Moonraker e atualizar o status ao final.</small>
                  </div>
                  <div className="modal-footer">
                    <button type="button" className="ghost-button" onClick={() => setUpdateDialog(null)}>
                      Cancelar
                    </button>
                    <button type="button" className="primary-button" onClick={() => void runUpdate(updateDialog.target)} disabled={loading}>
                      <RefreshCw size={16} />
                      Iniciar update
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className={`update-progress-status ${updateDialog.phase}`}>
                    {React.createElement(updatePhaseIcon(updateDialog.phase), { size: 18 })}
                    <strong>{formatUpdatePhase(updateDialog.phase)}</strong>
                  </div>
                  <div className="update-log-list" aria-live="polite">
                    {updateLogs.length === 0 ? <p className="muted">Aguardando mensagens do Moonraker...</p> : null}
                    {updateLogs.map((log) => (
                      <div key={log.id} className={`update-log-row ${log.level}`}>
                        <time>{log.time}</time>
                        <span>{log.message}</span>
                      </div>
                    ))}
                  </div>
                  <div className="modal-footer">
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => {
                        if (selectedPrinterId) {
                          void loadUpdateStatus(selectedPrinterId);
                        }
                      }}
                      disabled={!selectedPrinterId || loading}
                    >
                      <RefreshCw size={16} />
                      Recarregar status
                    </button>
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => {
                        closeUpdateSocket();
                        setUpdateDialog(null);
                      }}
                      disabled={updateDialog.phase === "running"}
                    >
                      <X size={16} />
                      Fechar
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        ) : null}

        {maintenanceDoneTask ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Registrar ${maintenanceDoneTask.name}`}>
            <div className="modal-card maintenance-modal-card">
              <div className="modal-header">
                <div>
                  <h2>{maintenanceDoneTask.name}</h2>
                  <p>{selectedPrinter?.name ?? "Impressora"} · {formatLocalDateTime(new Date())}</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setMaintenanceDoneTask(null)}>
                  <X size={16} />
                  Fechar
                </button>
              </div>
              <form className="maintenance-modal-form" onSubmit={(event) => void submitMaintenanceDone(event)}>
                <div className="maintenance-selected-printer">
                  <span>Impressora selecionada</span>
                  <strong>{selectedPrinter?.name ?? "Impressora"}</strong>
                  <small>{selectedPrinter?.moonraker_url ?? "-"}</small>
                </div>
                <div className="maintenance-modal-summary">
                  <Metric label="Componente" value={maintenanceDoneTask.component} />
                  <Metric label="Última" value={formatOptionalLocalDateTime(maintenanceDoneTask.last_done_at)} />
                  <Metric label="Lembrete atual" value={maintenanceDoneTask.is_active ? formatMaintenanceInterval(maintenanceDoneTask) : "sem lembrete"} />
                </div>
                {maintenancePrintHoursAvailable ? (
                  <div className="maintenance-print-hours-banner">
                    <Timer size={16} />
                    <span>Horas atuais de impressão</span>
                    <strong>{formatHours(maintenancePrintHours.total_print_hours ?? 0)}</strong>
                  </div>
                ) : (
                  <p className="maintenance-modal-hint">{maintenanceHoursDisabledMessage}</p>
                )}
                <label className="form-field">
                  <span>Observação</span>
                  <textarea
                    value={maintenanceDoneNotes}
                    onChange={(event) => setMaintenanceDoneNotes(event.target.value)}
                    placeholder="O que foi feito, peça trocada, condição encontrada..."
                  />
                </label>
                <p className="maintenance-modal-hint">
                  Com o prazo preenchido, o Printora volta a avisar quando vencer. Se deixar vazio, esta rotina fica registrada e não gera novo lembrete.
                </p>
                <div className="form-grid two-columns">
                  <label className="form-field">
                    <span>Lembrar por</span>
                    <select
                      value={maintenanceDoneIntervalKind}
                      onChange={(event) => {
                        const value = event.target.value as "days" | "print_hours";
                        if (value === "print_hours" && !maintenancePrintHoursAvailable) {
                          return;
                        }
                        setMaintenanceDoneIntervalKind(value);
                        setMaintenanceDoneDisableReminder(false);
                      }}
                      disabled={maintenanceDoneDisableReminder}
                    >
                      <option value="days">Dias</option>
                      <option value="print_hours" disabled={!maintenancePrintHoursAvailable}>Horas de impressão</option>
                    </select>
                  </label>
                  <label className="form-field">
                    <span>Valor</span>
                    <input
                      type="number"
                      min="1"
                      max={maintenanceDoneIntervalKind === "days" ? "3650" : "100000"}
                      step={maintenanceDoneIntervalKind === "days" ? "1" : "0.1"}
                      value={maintenanceDoneIntervalValue}
                      onChange={(event) => {
                        setMaintenanceDoneIntervalValue(event.target.value);
                        setMaintenanceDoneDisableReminder(false);
                      }}
                      placeholder="Vazio para nunca lembrar"
                      disabled={maintenanceDoneDisableReminder}
                    />
                  </label>
                </div>
                <div className="form-grid two-columns">
                  <label className="inline-check maintenance-no-reminder">
                    <input
                      type="checkbox"
                      checked={maintenanceDoneDisableReminder || !maintenanceDoneIntervalValue.trim()}
                      onChange={(event) => {
                        setMaintenanceDoneDisableReminder(event.target.checked);
                        if (event.target.checked) {
                          setMaintenanceDoneIntervalValue("");
                        }
                      }}
                    />
                    Não lembrar de novo
                  </label>
                </div>
                <div className="modal-footer">
                  <button type="button" className="ghost-button" onClick={() => setMaintenanceDoneTask(null)}>
                    <X size={16} />
                    Cancelar
                  </button>
                  <button type="submit" className="primary-button" disabled={loading}>
                    <CheckCircle2 size={16} />
                    Confirmar manutenção
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}

        {maintenanceFreeModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Registro livre de manutenção">
            <div className="modal-card maintenance-modal-card">
              <div className="modal-header">
                <div>
                  <h2>Registro livre</h2>
                  <p>{selectedPrinter?.name ?? "Impressora"} · {formatLocalDateTime(new Date())}</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setMaintenanceFreeModalOpen(false)}>
                  <X size={16} />
                  Fechar
                </button>
              </div>
              <form className="maintenance-modal-form" onSubmit={(event) => void submitMaintenanceFreeEvent(event)}>
                <div className="maintenance-selected-printer">
                  <span>Impressora selecionada</span>
                  <strong>{selectedPrinter?.name ?? "Impressora"}</strong>
                  <small>{selectedPrinter?.moonraker_url ?? "-"}</small>
                </div>
                <div className="form-grid two-columns">
                  <label className="form-field">
                    <span>Tipo</span>
                    <select
                      value={maintenanceEventType}
                      onChange={(event) => setMaintenanceEventType(event.target.value as MaintenanceEventRecord["event_type"])}
                      required
                    >
                      <option value="" disabled>
                        Selecione o tipo
                      </option>
                      <option value="maintenance">manutenção</option>
                      <option value="failure">falha</option>
                      <option value="adjustment">ajuste</option>
                      <option value="note">nota</option>
                    </select>
                  </label>
                  <label className="form-field">
                    <span>Componente</span>
                    <input value={maintenanceComponent} onChange={(event) => setMaintenanceComponent(event.target.value)} required />
                  </label>
                </div>
                <label className="form-field">
                  <span>Título</span>
                  <input value={maintenanceTitle} onChange={(event) => setMaintenanceTitle(event.target.value)} required />
                </label>
                <label className="form-field">
                  <span>Notas</span>
                  <textarea value={maintenanceNotes} onChange={(event) => setMaintenanceNotes(event.target.value)} />
                </label>
                <label className="inline-check maintenance-no-reminder">
                  <input
                    type="checkbox"
                    checked={maintenanceFreeReminderEnabled}
                    onChange={(event) => {
                      setMaintenanceFreeReminderEnabled(event.target.checked);
                      if (!event.target.checked) {
                        setMaintenanceFreeIntervalValue("");
                      }
                    }}
                  />
                  Criar lembrete recorrente
                </label>
                {maintenanceFreeReminderEnabled ? (
                  <div className="form-grid two-columns">
                    <label className="form-field">
                      <span>Lembrar por</span>
                      <select
                        value={maintenanceFreeIntervalKind}
                        onChange={(event) => {
                          const value = event.target.value as "days" | "print_hours";
                          if (value === "print_hours" && !maintenancePrintHoursAvailable) {
                            return;
                          }
                          setMaintenanceFreeIntervalKind(value);
                        }}
                      >
                        <option value="days">Dias</option>
                        <option value="print_hours" disabled={!maintenancePrintHoursAvailable}>Horas de impressão</option>
                      </select>
                    </label>
                    <label className="form-field">
                      <span>Valor</span>
                      <input
                        type="number"
                        min="1"
                        max={maintenanceFreeIntervalKind === "days" ? "3650" : "100000"}
                        step={maintenanceFreeIntervalKind === "days" ? "1" : "0.1"}
                        value={maintenanceFreeIntervalValue}
                        onChange={(event) => setMaintenanceFreeIntervalValue(event.target.value)}
                        required={maintenanceFreeReminderEnabled}
                      />
                    </label>
                  </div>
                ) : null}
                <p className="maintenance-modal-hint">
                  {maintenancePrintHoursAvailable
                    ? `Horas atuais de impressão: ${formatHours(maintenancePrintHours.total_print_hours ?? 0)}.`
                    : `Sem lembrete recorrente, o registro fica apenas no histórico. ${maintenanceHoursDisabledMessage}`}
                </p>
                <div className="modal-footer">
                  <button type="button" className="ghost-button" onClick={() => setMaintenanceFreeModalOpen(false)}>
                    <X size={16} />
                    Cancelar
                  </button>
                  <button type="submit" className="primary-button" disabled={loading || !maintenanceEventType || !maintenanceComponent.trim() || !maintenanceTitle.trim() || (maintenanceFreeReminderEnabled && maintenanceFreeIntervalKind === "print_hours" && !maintenancePrintHoursAvailable)}>
                    <CheckCircle2 size={16} />
                    Salvar registro
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}

        <section className="grid">
        <article className="panel wide panel-section panel-overview">
          <div className="overview-hero">
            <div className="overview-status-card">
              <span className={`status-pill ${moonrakerOnline ? "online" : "offline"}`}>
                <span />
                Moonraker {moonrakerOnline ? "online" : "offline"}
              </span>
              <h2>{selectedPrinter?.name ?? "Nenhuma impressora selecionada"}</h2>
              <p>{selectedPrinter?.moonraker_url ?? "Cadastre uma impressora para carregar status, snapshots e health check."}</p>
              <div className="overview-status-grid">
                <Metric label="Estado" value={formatUnknown(operationState)} />
                <Metric label="Última leitura" value={lastReadingLabel} />
                <Metric label="Origem" value={health?.data_state ? formatChecklistDataState(health.data_state) : "-"} />
                <Metric label="Updates" value={String(countPendingUpdates(updateStatus))} />
              </div>
            </div>
            <div className={`overview-risk-card ${riskClass}`}>
              <span>Risco atual</span>
              <strong>{riskLabel}</strong>
              <p>{health?.summary ?? "Sem health check carregado para a impressora ativa."}</p>
              <div className="overview-risk-counts">
                <span>{health?.counts.blocker ?? 0} bloqueio(s)</span>
                <span>{health?.counts.warning ?? 0} alerta(s)</span>
                <span>{snapshots.length} snapshot(s)</span>
              </div>
            </div>
          </div>
          <div className="overview-quick-actions" aria-label="Ações rápidas">
            <button type="button" className="primary-button" onClick={openCreatePrinterModal}>
              <Plus size={15} />
              Adicionar impressora
            </button>
            <button type="button" className="secondary-button" onClick={() => void captureSnapshot()} disabled={!selectedPrinterId || loading}>
              <Database size={15} />
              Capturar snapshot
            </button>
            <button type="button" className="secondary-button" onClick={() => selectedPrinterId ? void loadPrinterHealth(selectedPrinterId) : undefined} disabled={!selectedPrinterId || loading}>
              <ShieldCheck size={15} />
              Health check
            </button>
            <button type="button" className="secondary-button" onClick={() => void loadSelectedPrinterStatus()} disabled={!selectedPrinterId || loading}>
              <RefreshCw size={15} />
              Atualizar status
            </button>
          </div>
        </article>

        <article className="panel wide panel-section panel-printers">
          <div className="panel-heading">
            <div>
              <h2>Dashboard de impressoras</h2>
              <p className="muted">Visão rápida das impressoras cadastradas e do contexto ativo do sistema.</p>
            </div>
            <button type="button" className="primary-button" onClick={openCreatePrinterModal}>
              <Plus size={16} />
              Adicionar impressora
            </button>
          </div>
          <div className="overview-strip">
            <Badge icon={Server} label="Impressoras" value={printers.length} />
            <Badge icon={Printer} label="Ativa" value={selectedPrinter?.name ?? "-"} />
            <Badge icon={Gauge} label="Decisão" value={formatDecision(health?.decision)} />
            <Badge icon={Database} label="Snapshots" value={snapshots.length} />
          </div>
          <div className="printer-dashboard">
            {printers.length === 0 ? <p className="muted">Nenhuma impressora cadastrada.</p> : null}
            {printers.map((printer) => (
              <div key={printer.id} className={`printer-card ${printer.id === selectedPrinterId ? "active" : ""}`}>
                <div className="printer-card-header">
                  <div>
                    <strong>{printer.name}</strong>
                    <span>{printer.moonraker_url}</span>
                  </div>
                  <span className={printer.id === selectedPrinterId ? "status-pill active" : "status-pill"}>
                    {printer.id === selectedPrinterId ? "ativa" : "cadastrada"}
                  </span>
                </div>
                <div className="printer-card-grid">
                  <Metric label="Host audit" value={printer.host_audit_mode} />
                  <Metric label="SSH" value={formatSshStatus(printer)} />
                  <Metric label="Klipper" value={printer.id === selectedPrinterId ? health?.metrics.klipper_state ? String(health.metrics.klipper_state) : "-" : "-"} />
                  <Metric label="Moonraker" value={printer.id === selectedPrinterId ? health?.metrics.moonraker_version ? String(health.metrics.moonraker_version) : "-" : "-"} />
                </div>
                <div className="printer-card-actions">
                  <button type="button" className="secondary-button" onClick={() => openEditPrinterModal(printer)} disabled={loading}>
                    <Settings size={15} />
                    Editar
                  </button>
                  <button type="button" className="secondary-button" onClick={() => selectPrinter(printer.id)} disabled={loading || printer.id === selectedPrinterId}>
                    <CheckCircle2 size={15} />
                    Selecionar
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void loadSelectedPrinterStatus()} disabled={!selectedPrinterId || printer.id !== selectedPrinterId || loading}>
                    <Radio size={15} />
                    Ler status
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void captureSnapshot()} disabled={!selectedPrinterId || printer.id !== selectedPrinterId || loading}>
                    <Camera size={15} />
                    Snapshot
                  </button>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-operation">
          <div className="panel-heading">
            <div>
              <h2>Operação read-only</h2>
              <p className="muted">{operationStatus?.summary ?? "Aguardando dados da impressora selecionada."}</p>
            </div>
            <button type="button" className="secondary-button" onClick={() => selectedPrinterId && void loadOperationStatus(selectedPrinterId)} disabled={!selectedPrinterId || loading}>
              <RefreshCw size={15} />
              Recarregar
            </button>
            <button type="button" className="secondary-button" onClick={() => void loadOfflineOperationFixture()} disabled={loading}>
              <Database size={15} />
              Exemplo offline
            </button>
          </div>
          <div className="overview-strip dense-toolbar">
            <Badge icon={Printer} label="Impressora" value={selectedPrinter?.name ?? "-"} />
            <Badge icon={Radio} label="Moonraker" value={operationStatus?.connected ? "online" : "offline"} />
            <Badge icon={ShieldCheck} label="Modo" value={operationStatus?.safe_mode ?? "read_only"} />
            <Badge icon={Database} label="Dados" value={formatOperationDataState(operationStatus?.data_state)} />
            <Badge icon={Gauge} label="Comandos" value={operationStatus?.can_send_commands ? "habilitados" : "bloqueados"} />
          </div>
          {operationStatus?.data_state === "offline" ? (
            <div className="operation-state offline">
              <AlertTriangle size={17} />
              <div>
                <strong>Sem leitura ao vivo</strong>
                <span>{operationStatus.error ?? "A impressora pode estar desligada ou fora da rede."}</span>
              </div>
            </div>
          ) : null}
          {operationStatus?.data_state === "fixture" ? (
            <div className="operation-state fixture">
              <Database size={17} />
              <div>
                <strong>Fixture local</strong>
                <span>Dados simulados para validar layout com a impressora desligada. Nenhum endpoint da impressora foi chamado.</span>
              </div>
            </div>
          ) : null}
          {operationStatus?.data_state === "last_snapshot" ? (
            <div className="operation-state last-snapshot">
              <Database size={17} />
              <div>
                <strong>Último estado conhecido</strong>
                <span>
                  Snapshot #{operationStatus.last_snapshot?.id ?? "-"} de {operationStatus.last_snapshot?.created_at ?? "-"}.
                  A impressora não foi consultada ao exibir estes dados.
                </span>
              </div>
            </div>
          ) : null}
          <div className="operation-grid">
            <section className="operation-panel">
              <h3>System Loads</h3>
              <div className="section-summary">
                {operationStatus?.system_loads.map((metric) => (
                  <Metric key={metric.label} label={metric.label} value={formatOperationValue(metric.value, metric.unit)} />
                ))}
              </div>
            </section>

            <section className="operation-panel">
              <h3>Temperaturas</h3>
              <div className="temperature-list">
                <div className="list-table-header temperature-row">
                  <strong>Sensor</strong>
                  <span>Leitura</span>
                  <small>Potência</small>
                </div>
                {operationStatus?.temperatures.length === 0 ? <p className="muted">Nenhum heater ou sensor retornado pelo Moonraker.</p> : null}
                {operationStatus?.temperatures.map((item) => (
                  <div key={item.name} className="temperature-row">
                    <strong>{item.name}</strong>
                    <span>
                      {formatTemperature(item.temperature)} / alvo {formatTemperature(item.target)}
                    </span>
                    <small>Potência: {formatPercent(item.power)}</small>
                  </div>
                ))}
              </div>
            </section>

            <details className="operation-panel wide-operation-panel collapsible-panel">
              <summary>Histórico de temperaturas</summary>
              <div className="temperature-history">
                {buildTemperatureSeries(operationStatus?.temperature_history ?? []).length === 0 ? (
                  <p className="muted">Nenhum snapshot com temperatura disponível para histórico.</p>
                ) : null}
                {buildTemperatureSeries(operationStatus?.temperature_history ?? []).map((series) => (
                  <div key={series.name} className="temperature-history-row">
                    <div className="temperature-history-label">
                      <strong>{series.name}</strong>
                      <span>
                        {formatTemperature(series.min)} - {formatTemperature(series.max)}
                      </span>
                    </div>
                    <div className="temperature-sparkline" aria-label={`Histórico ${series.name}`}>
                      {series.points.map((point) => (
                        <span
                          key={`${series.name}-${point.snapshotId}-${point.createdAt}`}
                          style={{ height: `${temperatureBarHeight(point.temperature, series.min, series.max)}%` }}
                          title={`${point.createdAt}: ${formatTemperature(point.temperature)}`}
                        />
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </details>

            <section className="operation-panel">
              <h3>Toolhead</h3>
              <div className="section-summary">
                <Metric label="Posição" value={formatPosition(operationStatus?.toolhead.position)} />
                <Metric label="Home" value={formatUnknown(operationStatus?.toolhead.homed_axes ?? "-")} />
                <Metric label="Velocidade máx." value={formatOperationValue(operationStatus?.toolhead.max_velocity, "mm/s")} />
                <Metric label="Aceleração máx." value={formatOperationValue(operationStatus?.toolhead.max_accel, "mm/s²")} />
                <Metric label="Speed factor" value={formatPercent(operationStatus?.toolhead.speed_factor)} />
              </div>
            </section>

            <section className="operation-panel">
              <h3>Extruder</h3>
              <div className="section-summary">
                <Metric label="Pressure advance" value={formatUnknown(operationStatus?.extruder.pressure_advance ?? "-")} />
                <Metric label="Smooth time" value={formatOperationValue(operationStatus?.extruder.smooth_time, "s")} />
                <Metric label="Extrusion factor" value={formatPercent(operationStatus?.extruder.extrusion_factor)} />
                <Metric label="Filamento usado" value={formatOperationValue(operationStatus?.extruder.filament_used, "mm")} />
              </div>
            </section>

            <section className="operation-panel wide-operation-panel">
              <h3>Miscellaneous</h3>
              <div className="section-summary">
                <Metric label="Print state" value={operationStatus?.miscellaneous.print_state ?? "-"} />
                <Metric label="Arquivo" value={operationStatus?.miscellaneous.filename || "-"} />
                <Metric label="Progresso" value={formatPercent(operationStatus?.miscellaneous.progress)} />
                <Metric label="Mensagem" value={operationStatus?.miscellaneous.message || "-"} />
              </div>
              <div className="fan-list">
                {operationStatus?.miscellaneous.fans?.length === 0 ? <p className="muted">Nenhum fan retornado pelo Moonraker.</p> : null}
                {operationStatus?.miscellaneous.fans?.map((fan) => (
                  <div key={fan.name} className="fan-row">
                    <strong>{fan.name}</strong>
                    <span>{formatPercent(fan.speed)}</span>
                    <small>RPM: {formatUnknown(fan.rpm ?? "-")}</small>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </article>

        <article className={`panel wide health ${healthPanelClass(health?.decision)} panel-section panel-monitoring`}>
          <div className="panel-heading">
            <h2>Health Check</h2>
            <strong>{health?.summary ?? "Aguardando dados"}</strong>
          </div>
          {health ? (
            <div className="checklist-meta">
              <span>{formatChecklistDataState(health.data_state)}</span>
              <span>{health.source}</span>
            </div>
          ) : null}
          <div className="health-metrics">
            <Badge icon={Gauge} label="Decisão" value={formatDecision(health?.decision)} />
            <Badge icon={ShieldCheck} label="Bloqueios" value={health?.counts.blocker ?? 0} />
            <Badge icon={AlertTriangle} label="Alertas" value={health?.counts.warning ?? 0} />
            <Badge icon={Database} label="Snapshots" value={formatUnknown(health?.metrics.snapshot_count ?? "-")} />
          </div>
          <div className="section-summary">
            {health?.metrics
              ? Object.entries(health.metrics).map(([key, value]) => (
                  <Metric key={key} label={formatMetricLabel(key)} value={formatUnknown(value)} />
                ))
              : null}
          </div>
          <div className="findings">
            {health?.items.map((item) => (
              <div key={item.key} className={`finding ${healthFindingClass(item.severity)}`}>
                <div>
                  <strong>{item.title}</strong>
                  <span>{formatHealthSeverity(item.severity)}</span>
                </div>
                <p>{item.detail}</p>
                <small>{item.action}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-updates">
          <div className="panel-heading">
            <div>
              <h2>Atualizações</h2>
              <p className="muted">Componentes do Update Manager para {selectedPrinter?.name ?? "a impressora selecionada"}.</p>
            </div>
            <div className="panel-actions">
              <button
                type="button"
                className="secondary-button"
                onClick={() => void refreshUpdateStatus()}
                disabled={!selectedPrinterId || loading || updateStatus?.busy}
              >
                <RefreshCw size={15} />
                Reanalisar
              </button>
              <button
                type="button"
                className="primary-button"
                onClick={() => openUpdateDialog("all")}
                disabled={!selectedPrinterId || loading || updateStatus?.busy}
              >
                <RefreshCw size={15} />
                Atualizar tudo
              </button>
            </div>
          </div>
          <div className="overview-strip">
            <Badge icon={RefreshCw} label="Pendentes" value={updateStatus?.counts.update_available ?? 0} />
            <Badge icon={AlertTriangle} label="Alertas" value={updateStatus?.counts.warning ?? 0} />
            <Badge icon={CheckCircle2} label="Atualizados" value={updateStatus?.counts.up_to_date ?? 0} />
            <Badge icon={Gauge} label="Estado" value={updateStatus?.busy ? "ocupado" : updateStatus?.summary ?? "-"} />
          </div>
          {updateActionResult ? (
            <div className="action-result">
              <strong>{updateActionResult.message}</strong>
              <span>Alvo: {updateActionResult.target}</span>
            </div>
          ) : null}
          <div className="update-list">
            {updateStatus?.components.length === 0 ? <p className="muted">Nenhum componente retornado pelo Update Manager.</p> : null}
            {updateStatus?.components.map((component) => (
              <div key={component.name} className={`update-row ${component.status}`}>
                <div className="update-main">
                  <div className="update-component-copy">
                    <strong className="update-title">
                      {React.createElement(updateStatusIcon(component.status), { size: 16 })}
                      {component.title}
                    </strong>
                    <span>
                      {component.current_version ?? "-"} {component.remote_version ? `→ ${component.remote_version}` : ""}
                    </span>
                    <small>
                      {component.configured_type} · behind {component.commits_behind_count} · packages {component.package_count}
                    </small>
                  </div>
                  <span className={`status-pill ${component.status}`}>{formatUpdateStatus(component.status)}</span>
                </div>
                {component.warnings.length || component.anomalies.length ? (
                  <small className="update-warning">
                    {[...component.warnings, ...component.anomalies].join(" · ")}
                  </small>
                ) : null}
                <div className="update-actions">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => void refreshUpdateStatus(component.name)}
                    disabled={!selectedPrinterId || loading || updateStatus.busy}
                  >
                    <RefreshCw size={15} />
                    Reanalisar
                  </button>
                  {component.can_update ? (
                    <button
                      type="button"
                      className="primary-button"
                      onClick={() => openUpdateDialog(component.name)}
                      disabled={!selectedPrinterId || loading || updateStatus.busy}
                    >
                      <RefreshCw size={15} />
                      Atualizar
                    </button>
                  ) : (
                    <button type="button" className="secondary-button" disabled>
                      <CheckCircle2 size={15} />
                      Atualizado
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-monitoring">
          <div className="panel-heading">
            <h2>Monitor CAN</h2>
            <strong>{formatCanAlert(canSummary?.overall_alert ?? canRecords[0]?.alert_level ?? "ok")}</strong>
          </div>
          <div className="can-summary">
            <Badge label="Modo" value={canSummary?.safe_mode ?? "manual_read_only"} />
            <Badge label="Dados" value={canSummary?.data_state === "manual_records" ? "registros manuais" : "sem registros"} />
            <Badge label="OK" value={canSummary?.counts.ok ?? 0} />
            <Badge label="Monitorar" value={canSummary?.counts.monitorar ?? 0} />
            <Badge label="Problemas" value={canSummary?.counts.problema ?? 0} />
          </div>
          <div className="panel-actions">
            <button type="button" className="secondary-button" onClick={() => void compareLatestCanRecords()} disabled={!selectedPrinterId || loading || canRecords.length < 2}>
              Comparar últimas leituras
            </button>
          </div>
          {canSummary?.data_state === "no_data" ? (
            <p className="muted">Nenhuma leitura CAN local registrada. Cole a saída de ip link ou preencha os contadores manualmente.</p>
          ) : null}
          {canComparison ? (
            <div className={`can-row ${canComparison.alert_level}`}>
              <strong>Comparação #{canComparison.before_record_id} → #{canComparison.after_record_id}</strong>
              <span>
                {canComparison.interface_name} · rx={canComparison.delta_rx_error} · tx={canComparison.delta_tx_error} · retries={canComparison.delta_tx_retries}
              </span>
              <small>{canComparison.diagnosis}</small>
              <small>{canComparison.recommended_actions.join(" · ")}</small>
            </div>
          ) : null}
          <div className="can-parser">
            <textarea
              aria-label="Saída bruta ip link CAN"
              value={canRawOutput}
              onChange={(event) => setCanRawOutput(event.target.value)}
              placeholder="Cole aqui a saída de ip -details -statistics link show can0 para preencher os campos."
            />
            <button type="button" className="secondary-button" onClick={() => void parseCanRawOutput()} disabled={!selectedPrinterId || loading || !canRawOutput.trim()}>
              Extrair leitura
            </button>
          </div>
          <form className="can-form" onSubmit={(event) => void createCanRecord(event)}>
            <input
              aria-label="Interface CAN"
              value={canInterfaceName}
              onChange={(event) => setCanInterfaceName(event.target.value)}
              placeholder="can0"
            />
            <input
              aria-label="RX error"
              type="number"
              min="0"
              value={canRxError}
              onChange={(event) => setCanRxError(Number(event.target.value))}
            />
            <input
              aria-label="TX error"
              type="number"
              min="0"
              value={canTxError}
              onChange={(event) => setCanTxError(Number(event.target.value))}
            />
            <input
              aria-label="TX retries"
              type="number"
              min="0"
              value={canTxRetries}
              onChange={(event) => setCanTxRetries(Number(event.target.value))}
            />
            <input
              aria-label="Estado do barramento"
              value={canBusState}
              onChange={(event) => setCanBusState(event.target.value)}
              placeholder="ERROR-ACTIVE"
            />
            <input
              aria-label="Bitrate CAN"
              type="number"
              min="1"
              value={canBitrate}
              onChange={(event) => setCanBitrate(Number(event.target.value))}
            />
            <textarea
              aria-label="Notas CAN"
              value={canNotes}
              onChange={(event) => setCanNotes(event.target.value)}
              placeholder="Ex.: leitura manual de ip -details -statistics link show can0"
            />
            <button type="submit" disabled={!selectedPrinterId || loading}>
              Registrar
            </button>
          </form>
          <div className="can-list">
            {canRecords.length === 0 ? <p className="muted">Nenhuma leitura CAN registrada.</p> : null}
            {canRecords.map((record) => (
              <div key={record.id} className={`can-row ${record.alert_level}`}>
                <strong>{formatCanAlert(record.alert_level)}</strong>
                <span>
                  {record.interface_name} · rx={record.rx_error} · tx={record.tx_error} · retries={record.tx_retries} ·{" "}
                  {record.recorded_at}
                </span>
                <small>
                  Delta rx={formatOptionalInt(record.delta_rx_error)} · tx={formatOptionalInt(record.delta_tx_error)} ·
                  retries={formatOptionalInt(record.delta_tx_retries)}
                </small>
                <small>
                  Estado: {record.bus_state ?? "-"} · bitrate: {record.bitrate ?? "-"}
                </small>
                <small>{record.diagnosis}</small>
                {record.recommended_actions.length ? <small>{record.recommended_actions.join(" · ")}</small> : null}
                {record.notes ? <small>{record.notes}</small> : null}
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-firmware">
          <div className="panel-heading">
            <h2>Mods e plugins</h2>
            <strong>{pluginAudit?.summary ?? "Sem snapshot analisado"}</strong>
          </div>
          <div className="plugin-actions">
            <button type="button" onClick={() => selectedPrinterId && void loadPluginAudit(selectedPrinterId)} disabled={!selectedPrinterId || loading}>
              Reanalisar
            </button>
            <span>Leitura baseada no último snapshot Moonraker/Update Manager. Não remove nem altera nada.</span>
          </div>
          <div className="plugin-summary">
            <Badge label="Detectados" value={pluginAudit?.counts.detected ?? 0} />
            <Badge label="Risco" value={pluginAudit?.counts.risky ?? 0} />
            <Badge label="Investigar" value={pluginAudit?.counts.investigate ?? 0} />
            <Badge label="Desconhecidos" value={pluginAudit?.counts.unknown ?? 0} />
          </div>
          {pluginAudit?.unknown_update_manager_components.length ? (
            <div className="plugin-unknown">
              <strong>Componentes fora do catálogo</strong>
              <span>{pluginAudit.unknown_update_manager_components.join(" · ")}</span>
            </div>
          ) : null}
          <div className="plugin-list">
            {pluginAudit?.items.map((item) => (
              <div key={item.name} className={`plugin-row ${item.classification} ${item.detected ? "detected" : "missing"}`}>
                <div>
                  <strong>{item.title}</strong>
                  <span>
                    {item.detected ? "detectado" : "não detectado"} · {formatPluginClassification(item.classification)}
                  </span>
                  <small>
                    Versão: {item.version ?? "-"} · dirty: {formatBoolean(item.dirty)} · behind:{" "}
                    {formatOptionalInt(item.commits_behind)}
                  </small>
                  <small>Ação: {formatPluginAction(item.action)}</small>
                </div>
                <p>{item.risk}</p>
                <small>{item.recommendation}</small>
                <small>Evidência: {item.evidence.join(" · ")}</small>
                <small>Gate: {item.removal_gates.join(" · ")}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-firmware">
          <div className="panel-heading">
            <h2>Firmware Manager</h2>
            <strong>{firmwareBoards.length} placas cadastradas</strong>
          </div>
          <p className="muted">
            Cadastro local de MCUs, presets, build e flash planejados. Flash permanece somente em dry-run nesta etapa.
          </p>
          <div className="dense-toolbar firmware-filter-toolbar" aria-label="Filtros de firmware">
            <button type="button" className={firmwareFilter === "all" ? "active" : ""} onClick={() => setFirmwareFilter("all")}>
              Todas
            </button>
            <button type="button" className={firmwareFilter === "can" ? "active" : ""} onClick={() => setFirmwareFilter("can")}>
              CAN
            </button>
            <button type="button" className={firmwareFilter === "usb" ? "active" : ""} onClick={() => setFirmwareFilter("usb")}>
              USB
            </button>
            <span>{visibleFirmwareBoards.length} placa(s) visíveis</span>
          </div>
          <form className="firmware-board-form" onSubmit={(event) => void createFirmwareBoard(event)}>
            <input
              aria-label="Nome da placa"
              value={firmwareBoardName}
              onChange={(event) => setFirmwareBoardName(event.target.value)}
              placeholder="EBB T0"
            />
            <select
              aria-label="Preset da placa"
              value={firmwareBoardPresetId}
              onChange={(event) => {
                setFirmwareBoardPresetId(event.target.value);
                setFirmwareBoardConfigFile(`firmware/${event.target.value}.config`);
              }}
            >
              {boardPresets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {preset.vendor} · {preset.name}
                </option>
              ))}
            </select>
            <input
              aria-label="UUID CAN"
              value={firmwareBoardCanUuid}
              onChange={(event) => setFirmwareBoardCanUuid(event.target.value)}
              placeholder="UUID CAN"
            />
            <input
              aria-label="Interface CAN"
              value={firmwareBoardCanInterface}
              onChange={(event) => setFirmwareBoardCanInterface(event.target.value)}
              placeholder="can0"
            />
            <input
              aria-label="Arquivo .config"
              value={firmwareBoardConfigFile}
              onChange={(event) => setFirmwareBoardConfigFile(event.target.value)}
              placeholder="firmware/ebb_t0.config"
            />
            <textarea
              aria-label="Notas da placa"
              value={firmwareBoardNotes}
              onChange={(event) => setFirmwareBoardNotes(event.target.value)}
              placeholder="Ex.: toolhead CAN, Katapult já instalado"
            />
            <button type="submit" disabled={!selectedPrinterId || loading || boardPresets.length === 0}>
              Cadastrar placa
            </button>
          </form>
          <div className="firmware-board-list">
            <div className="list-table-header firmware-board-row">
              <strong>Placa</strong>
              <span>Conexão</span>
              <small>Ações</small>
            </div>
            {visibleFirmwareBoards.length === 0 ? <p className="muted">Nenhuma placa cadastrada para este filtro.</p> : null}
            {visibleFirmwareBoards.map((board) => (
              <div key={board.id} className="firmware-board-row">
                <div>
                  <strong>{board.name}</strong>
                  <span>
                    {board.preset_id} · {board.mcu} · {formatConnectionType(board.connection_type)}
                  </span>
                  <small>
                    flash futuro: {board.flash_method} · config: {board.config_file}
                  </small>
                </div>
                <div>
                  <span>CAN UUID: {board.can_uuid ?? "-"}</span>
                  <small>Interface: {board.can_interface}</small>
                </div>
                <div>
                  <small>{board.notes || "Sem notas."}</small>
                  <button type="button" onClick={() => void validateFirmwareBuildPreflight(board.id)} disabled={loading}>
                    Preflight build
                  </button>
                  <button type="button" onClick={() => void createFirmwareBuildDryRun(board.id)} disabled={loading}>
                    Dry-run build
                  </button>
                  <button type="button" onClick={() => void createFirmwareFlashDryRun(board.id)} disabled={loading}>
                    Dry-run flash
                  </button>
                  <button type="button" onClick={() => void validateFirmwareFlashPreflight(board.id)} disabled={loading}>
                    Preflight flash
                  </button>
                  <button type="button" onClick={() => void loadFirmwareRecoveryPlan(board.id)} disabled={loading}>
                    Plano recuperação
                  </button>
                  <button
                    type="button"
                    onClick={() => void validateFirmwareFlashGate(board.id)}
                    disabled={loading || firmwareFlashConfirmation !== "BLOCK_REAL_FLASH"}
                  >
                    Validar gate flash
                  </button>
                  <button
                    type="button"
                    onClick={() => void executeFirmwareBuildLocal(board.id)}
                    disabled={loading || firmwareBuildConfirmation !== "EXECUTE_LOCAL_BUILD_NO_FLASH"}
                  >
                    Executar build local
                  </button>
                </div>
              </div>
            ))}
          </div>
          {firmwareRecoveryPlan ? (
            <details className="firmware-run-row" open>
              <summary>
                Recuperação · {firmwareRecoveryPlan.board_name} · {firmwareRecoveryPlan.flash_method}
              </summary>
              <div className="firmware-run-detail">
                <small>
                  Modo: {firmwareRecoveryPlan.safe_mode} · bloqueado: {formatBoolean(firmwareRecoveryPlan.blocked)}
                </small>
                <strong>Pré-condições</strong>
                <ol>
                  {firmwareRecoveryPlan.prerequisites.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
                <strong>Recuperação</strong>
                <ol>
                  {firmwareRecoveryPlan.recovery_steps.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
                <strong>Validação</strong>
                <ol>
                  {firmwareRecoveryPlan.validation_steps.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
                <small>{firmwareRecoveryPlan.rollback_notes.join(" · ")}</small>
              </div>
            </details>
          ) : null}
          {firmwareBuildPreflight ? (
            <details className="firmware-run-row" open>
              <summary>
                Preflight build · {firmwareBuildPreflight.board_name} · bloqueado:{" "}
                {formatBoolean(firmwareBuildPreflight.blocked)}
              </summary>
              <div className="firmware-run-detail">
                <small>
                  Modo: {firmwareBuildPreflight.safe_mode} · execução liberada:{" "}
                  {formatBoolean(firmwareBuildPreflight.can_execute_build)}
                </small>
                <small>Klipper: {firmwareBuildPreflight.klipper_path}</small>
                <small>Config: {firmwareBuildPreflight.config_file}</small>
                <small>Output esperado: {firmwareBuildPreflight.expected_build_output}</small>
                <strong>Checks</strong>
                <ol>
                  {firmwareBuildPreflight.checks.map((item) => (
                    <li key={item.key}>
                      {item.label}: {item.status} · {item.detail}
                    </li>
                  ))}
                </ol>
                <strong>Preview</strong>
                <pre>{firmwareBuildPreflight.commands_preview.join("\n")}</pre>
                <small>{firmwareBuildPreflight.message}</small>
              </div>
            </details>
          ) : null}
          {firmwareFlashPreflight ? (
            <details className="firmware-run-row" open>
              <summary>
                Preflight flash · {firmwareFlashPreflight.board_name} · bloqueado:{" "}
                {formatBoolean(firmwareFlashPreflight.blocked)}
              </summary>
              <div className="firmware-run-detail">
                <small>
                  Modo: {firmwareFlashPreflight.safe_mode} · execução liberada:{" "}
                  {formatBoolean(firmwareFlashPreflight.can_execute_flash)}
                </small>
                <small>
                  Klipper: {firmwareFlashPreflight.klipper_state ?? "-"} · Klippy:{" "}
                  {firmwareFlashPreflight.klippy_state ?? "-"} · print: {firmwareFlashPreflight.print_state || "-"}
                </small>
                <small>
                  Método: {firmwareFlashPreflight.flash_method} · CAN: {firmwareFlashPreflight.can_uuid ?? "-"} ·{" "}
                  interface {firmwareFlashPreflight.can_interface}
                </small>
                <small>Binário: {firmwareFlashPreflight.binary_path}</small>
                <strong>Checks</strong>
                <ol>
                  {firmwareFlashPreflight.checks.map((item) => (
                    <li key={item.key}>
                      {item.label}: {item.status} · {item.detail}
                    </li>
                  ))}
                </ol>
                <strong>Preview bloqueado</strong>
                <pre>{firmwareFlashPreflight.commands_preview.join("\n")}</pre>
                <strong>Rollback futuro</strong>
                <ol>
                  {firmwareFlashPreflight.rollback_plan.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ol>
                <small>{firmwareFlashPreflight.message}</small>
              </div>
            </details>
          ) : null}
          <details className="collapsible-panel firmware-control-panel" open>
            <summary>Parâmetros de build e flash</summary>
          <div className="firmware-build-controls">
            <input
              aria-label="Caminho do Klipper"
              value={firmwareKlipperPath}
              onChange={(event) => setFirmwareKlipperPath(event.target.value)}
              placeholder="~/klipper"
            />
            <input
              aria-label="Diretório raiz dos builds"
              value={firmwareOutputRoot}
              onChange={(event) => setFirmwareOutputRoot(event.target.value)}
              placeholder="~/printer_data/firmware_builds"
            />
            <input
              aria-label="Confirmação do build local"
              value={firmwareBuildConfirmation}
              onChange={(event) => setFirmwareBuildConfirmation(event.target.value)}
              placeholder="EXECUTE_LOCAL_BUILD_NO_FLASH"
            />
            <input
              aria-label="Binário para dry-run de flash"
              value={firmwareFlashBinaryPath}
              onChange={(event) => setFirmwareFlashBinaryPath(event.target.value)}
              placeholder="binário opcional para dry-run de flash"
            />
            <input
              aria-label="Confirmação do gate de flash"
              value={firmwareFlashConfirmation}
              onChange={(event) => setFirmwareFlashConfirmation(event.target.value)}
              placeholder="BLOCK_REAL_FLASH"
            />
          </div>
          </details>
          <details className="collapsible-panel firmware-history-panel">
            <summary>Histórico de builds</summary>
          <div className="firmware-run-list">
            {firmwareBuildRuns.length === 0 ? <p className="muted">Nenhum dry-run de firmware registrado.</p> : null}
            {firmwareBuildRuns.map((run) => (
              <details key={run.id} className="firmware-run-row">
                <summary>
                  #{run.id} · placa #{run.board_id} · {run.status} · {run.created_at}
                </summary>
                <div className="firmware-run-detail">
                  <small>Output: {run.output_dir}</small>
                  <small>Backup .config: {run.config_backup_path}</small>
                  <small>Binário planejado: {run.binary_output_path}</small>
                  <strong>Checklist</strong>
                  <ol>
                    {run.checklist.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                  <strong>Comandos planejados</strong>
                  <pre>{run.commands.join("\n")}</pre>
                  <small>{run.message}</small>
                </div>
              </details>
            ))}
          </div>
          </details>
          <details className="collapsible-panel firmware-history-panel">
            <summary>Histórico de flash</summary>
          <div className="firmware-run-list">
            {firmwareFlashRuns.length === 0 ? <p className="muted">Nenhum dry-run de flash registrado.</p> : null}
            {firmwareFlashRuns.map((run) => (
              <details key={run.id} className="firmware-run-row">
                <summary>
                  Flash #{run.id} · placa #{run.board_id} · {run.status} · {run.created_at}
                </summary>
                <div className="firmware-run-detail">
                  <small>Método: {run.flash_method}</small>
                  <small>Binário: {run.binary_path}</small>
                  <small>
                    CAN: {run.can_uuid ?? "-"} · interface {run.can_interface}
                  </small>
                  <strong>Checklist</strong>
                  <ol>
                    {run.checklist.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                  <strong>Comandos planejados</strong>
                  <pre>{run.commands.join("\n")}</pre>
                  <small>{run.message}</small>
                </div>
              </details>
            ))}
          </div>
          </details>
          <details className="preset-details">
            <summary>Presets disponíveis ({boardPresets.length})</summary>
            <div className="preset-list">
              {boardPresets.map((preset) => (
                <div key={preset.id} className="preset-row">
                  <strong>{preset.name}</strong>
                  <span>
                    {preset.mcu} · {formatConnectionType(preset.connection_type)} · {preset.default_flash_method}
                  </span>
                  <small>
                    bootloader: {preset.bootloader_offset} · output: {preset.build_output} · pins:{" "}
                    {preset.canbus_pins ?? "-"}
                  </small>
                </div>
              ))}
            </div>
          </details>
        </article>

        <article className="panel wide panel-section panel-tests">
          <div className="panel-heading">
            <h2>Testes da impressora</h2>
            <strong>{selectedPrinter?.name ?? "Sem impressora"}</strong>
          </div>
          <div className="test-board-header dense-toolbar">
            <div>
              <strong>{calibrationSummary?.run_count ?? calibrationRuns.length}</strong>
              <span>resultados registrados</span>
            </div>
            <div>
              <strong>{calibrationExecutions.filter((item) => item.status === "executed").length}</strong>
              <span>execuções feitas</span>
            </div>
            <div>
              <strong>{calibrationTests.filter((test) => test.gcode.length > 0).length}</strong>
              <span>testes executáveis</span>
            </div>
            <div>
              <strong>{calibrationHiddenTests.length}</strong>
              <span>bloqueados pelo contexto</span>
            </div>
          </div>
          <div className="dense-toolbar filter-toolbar" aria-label="Filtros de testes">
            <button type="button" className={testFilter === "all" ? "active" : ""} onClick={() => setTestFilter("all")}>
              Todos
            </button>
            <button type="button" className={testFilter === "executable" ? "active" : ""} onClick={() => setTestFilter("executable")}>
              Executáveis
            </button>
            <button type="button" className={testFilter === "manual" ? "active" : ""} onClick={() => setTestFilter("manual")}>
              Manuais
            </button>
            <button type="button" className={testFilter === "blocked" ? "active" : ""} onClick={() => setTestFilter("blocked")}>
              Bloqueados
            </button>
          </div>
          <div className="test-card-grid">
            {visibleCalibrationTests.map((test) => {
              const lastRun = calibrationRuns.find((run) => run.test_key === test.test_key);
              const lastExecution = calibrationExecutions.find((execution) => execution.test_key === test.test_key);
              return (
                <article key={test.test_key} className={`test-card ${test.risk_level}`}>
                  <div className="test-card-title">
                    <div>
                      <strong>{test.title}</strong>
                      <span>{formatCalibrationCategory(test.category)}</span>
                    </div>
                    <button
                      type="button"
                      className="icon-button"
                      onClick={() => setCalibrationHelpTestKey(test.test_key)}
                      aria-label={`Ajuda de ${test.title}`}
                    >
                      <HelpCircle size={16} />
                    </button>
                  </div>
                  <p>{test.objective}</p>
                  <div className="test-card-meta">
                    <span>Risco: {formatRiskLevel(test.risk_level)}</span>
                    <span>{test.gcode.length ? "Com G-code" : "Manual"}</span>
                    <span>{lastRun ? `Último: ${formatCalibrationResult(lastRun.result_status)}` : "Sem resultado"}</span>
                  </div>
                  {lastExecution ? (
                    <small>
                      Última execução: {lastExecution.status} · {lastExecution.sent_commands.length} comando(s)
                    </small>
                  ) : null}
                  <div className="test-card-actions">
                    {test.gcode.length ? (
                      <button type="button" className="primary-button" onClick={() => void openCalibrationExecute(test)} disabled={!selectedPrinterId || loading}>
                        <Play size={15} />
                        Executar
                      </button>
                    ) : (
                      <button type="button" className="primary-button" onClick={() => openCalibrationResult(test, true)} disabled={!selectedPrinterId || loading}>
                        <CheckCircle2 size={15} />
                        Registrar
                      </button>
                    )}
                    <button type="button" className="secondary-button" onClick={() => openCalibrationResult(test)} disabled={!selectedPrinterId || loading}>
                      <History size={15} />
                      Histórico
                    </button>
                  </div>
                </article>
              );
            })}
            {visibleHiddenCalibrationTests.map((test) => (
              <article key={test.test_key} className="test-card high blocked">
                <div className="test-card-title">
                  <div>
                    <strong>{test.title}</strong>
                    <span>bloqueado</span>
                  </div>
                  <AlertTriangle size={16} />
                </div>
                <p>{test.reason}</p>
                <div className="test-card-meta">
                  <span>Sem execução neste contexto</span>
                  <span>Disponível quando a capacidade for confirmada</span>
                </div>
              </article>
            ))}
          </div>
        </article>

        <details className="panel wide panel-section test-history-panel collapsible-panel">
          <summary>Atividade recente</summary>
          <div className="panel-heading">
            <button
              type="button"
              className="secondary-button"
              onClick={() => {
                setCalibrationActivityCleared(true);
                setCalibrationExecutionResult(null);
              }}
              disabled={recentCalibrationActivityCount === 0}
            >
              Limpar visualização
            </button>
          </div>
          {calibrationActivityCleared ? <p className="muted">Atividade recente limpa nesta sessão.</p> : null}
          {!calibrationActivityCleared && calibrationExecutionResult ? (
            <div className={`test-history-row ${calibrationExecutionRowClass(calibrationExecutionResult.status)}`}>
              <strong>{formatCalibrationExecutionStatus(calibrationExecutionResult.status)}</strong>
              <span>{calibrationExecutionResult.message || "Sem mensagem."}</span>
              <small>{summarizeCalibrationExecutionFinalState(calibrationExecutionResult)}</small>
            </div>
          ) : null}
          {!calibrationActivityCleared &&
            calibrationExecutions.slice(0, 4).map((execution) => (
              <div key={execution.id} className={`test-history-row ${calibrationExecutionRowClass(execution.status)}`}>
                <strong>{formatCalibrationTestTitle(execution.test_key, calibrationTests)}</strong>
                <span>
                  {formatCalibrationExecutionStatus(execution.status)} · {execution.created_at}
                </span>
                <small>{summarizeCalibrationExecutionFinalState(execution)}</small>
              </div>
            ))}
          {!calibrationActivityCleared &&
            calibrationRuns.slice(0, 4).map((run) => (
              <div key={`run-${run.id}`} className={`test-history-row ${run.result_status}`}>
                <strong>{run.test_title}</strong>
                <span>
                  {formatCalibrationResult(run.result_status)} · {run.created_at}
                </span>
              </div>
            ))}
          {!calibrationActivityCleared && !calibrationExecutions.length && !calibrationRuns.length ? (
            <p className="muted">Nenhuma atividade registrada ainda.</p>
          ) : null}
        </details>

        {calibrationHelpTest ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Ajuda de ${calibrationHelpTest.title}`}>
            <div className="modal-card test-modal-card">
              <div className="modal-header">
                <div>
                  <h2>{calibrationHelpTest.title}</h2>
                  <p>{calibrationHelpTest.objective}</p>
                </div>
                <button type="button" className="icon-button" onClick={() => setCalibrationHelpTestKey(null)} aria-label="Fechar ajuda">
                  <X size={18} />
                </button>
              </div>
              <div className="test-help-grid">
                <section>
                  <strong>Antes de começar</strong>
                  <ol>
                    {calibrationHelpTest.prerequisites.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                </section>
                <section>
                  <strong>Sucesso esperado</strong>
                  <ol>
                    {calibrationHelpTest.success_criteria.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                </section>
              </div>
              {calibrationHelpTest.gcode.length ? <pre>{calibrationHelpTest.gcode.join("\n")}</pre> : null}
              <div className="modal-footer">
                <button type="button" className="secondary-button" onClick={() => setCalibrationHelpTestKey(null)}>
                  Fechar
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {calibrationExecuteTest ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Executar ${calibrationExecuteTest.title}`}>
            <div className="modal-card test-modal-card">
              <div className="modal-header">
                <div>
                  <h2>{calibrationExecuteTest.title}</h2>
                  <p>
                    {calibrationPreflight?.summary ?? "Preflight será validado antes do envio."}
                  </p>
                </div>
                <button type="button" className="icon-button" onClick={() => setCalibrationExecuteTestKey(null)} aria-label="Fechar execução">
                  <X size={18} />
                </button>
              </div>
              <div className={`test-preflight-status ${calibrationPreflight?.blocked ? "blocked" : "ready"}`}>
                <strong>{calibrationPreflight?.blocked ? "Bloqueado" : "Pronto para confirmação"}</strong>
                <span>
                  Klipper {calibrationPreflight?.klipper_state ?? "-"} · print {calibrationPreflight?.print_state || "-"}
                </span>
              </div>
              {calibrationPreflight?.block_reasons.length ? (
                <ul className="test-blockers">
                  {calibrationPreflight.block_reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              ) : null}
              <pre>{calibrationExecuteTest.gcode.join("\n")}</pre>
              <div className="test-confirm-grid">
                <label className="inline-check">
                  <input
                    type="checkbox"
                    checked={calibrationGcodeReviewed}
                    onChange={(event) => setCalibrationGcodeReviewed(event.target.checked)}
                  />
                  Revisei o G-code
                </label>
                <label className="inline-check">
                  <input
                    type="checkbox"
                    checked={calibrationOperatorPresent}
                    onChange={(event) => setCalibrationOperatorPresent(event.target.checked)}
                  />
                  Estou ao lado da impressora
                </label>
              </div>
              {calibrationExecutionResult ? (
                <div className={`test-history-row ${calibrationExecutionRowClass(calibrationExecutionResult.status)}`}>
                  <strong>{formatCalibrationExecutionStatus(calibrationExecutionResult.status)}</strong>
                  <span>{calibrationExecutionResult.message}</span>
                  <small>{summarizeCalibrationExecutionFinalState(calibrationExecutionResult)}</small>
                  <details>
                    <summary>Retorno registrado</summary>
                    <pre>{formatCalibrationExecutionResult(calibrationExecutionResult)}</pre>
                  </details>
                </div>
              ) : null}
              <div className="modal-footer">
                <button type="button" className="secondary-button" onClick={() => setCalibrationExecuteTestKey(null)}>
                  Cancelar
                </button>
                {calibrationExecutionResult?.status === "executed" ? (
                  <button
                    type="button"
                    className="primary-button"
                    onClick={() => {
                      setCalibrationExecuteTestKey(null);
                      openCalibrationResult(calibrationExecuteTest, true, "passed");
                      setCalibrationObservedValue(summarizeCalibrationExecutionFinalState(calibrationExecutionResult));
                      setCalibrationNotes(buildCalibrationExecutionNotes(calibrationExecutionResult));
                    }}
                  >
                    Registrar resultado
                  </button>
                ) : null}
                <button
                  type="button"
                  className="danger-button"
                  onClick={() => {
                    setCalibrationExecutionConfirmation("EXECUTE_CALIBRATION_GCODE");
                    void executeCalibrationGcode("EXECUTE_CALIBRATION_GCODE");
                  }}
                  disabled={!selectedPrinterId || loading || !calibrationGcodeReviewed || !calibrationOperatorPresent || !calibrationPreflight || calibrationPreflight.blocked}
                >
                  Executar agora
                </button>
              </div>
            </div>
          </div>
        ) : null}

        {calibrationResultTest ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Resultados de ${calibrationResultTest.title}`}>
            <div className="modal-card test-modal-card">
              <div className="modal-header">
                <div>
                  <h2>Resultados - {calibrationResultTest.title}</h2>
                  <p>Histórico deste teste na impressora selecionada.</p>
                </div>
                <button type="button" className="icon-button" onClick={() => setCalibrationResultTestKey(null)} aria-label="Fechar resultado">
                  <X size={18} />
                </button>
              </div>
              <div className="test-result-history">
                {calibrationResultExecutions.map((execution) => (
                  <div key={`execution-${execution.id}`} className={`test-history-row ${calibrationExecutionRowClass(execution.status)}`}>
                    <strong>{formatCalibrationExecutionStatus(execution.status)}</strong>
                    <span>
                      {execution.created_at} · {execution.sent_commands.length} comando(s)
                    </span>
                    {execution.message ? <small>{execution.message}</small> : null}
                    <small>{summarizeCalibrationExecutionFinalState(execution)}</small>
                  </div>
                ))}
                {calibrationResultRuns.map((run) => (
                  <div key={`run-${run.id}`} className={`test-history-row ${run.result_status}`}>
                    <strong>{formatCalibrationResult(run.result_status)}</strong>
                    <span>
                      {run.created_at} · {run.material || "-"} · {run.plate_name || "-"} · {run.nozzle || "-"}
                    </span>
                    {run.observed_value ? <small>Valor: {run.observed_value}</small> : null}
                    {run.notes ? <small>{run.notes}</small> : null}
                  </div>
                ))}
                {!calibrationResultExecutions.length && !calibrationResultRuns.length ? (
                  <p className="muted">Ainda não há resultados para este teste.</p>
                ) : null}
              </div>
              {!calibrationResultFormOpen ? (
                <div className="modal-footer">
                  <button type="button" className="secondary-button" onClick={() => setCalibrationResultTestKey(null)}>
                    Fechar
                  </button>
                  <button type="button" className="primary-button" onClick={() => setCalibrationResultFormOpen(true)} disabled={!selectedPrinterId || loading}>
                    Adicionar resultado
                  </button>
                </div>
              ) : null}
              {calibrationResultFormOpen ? (
                <form className="test-result-form" onSubmit={(event) => void createCalibrationRun(event)}>
                  {calibrationResultFormConfig ? <p className="muted">{calibrationResultFormConfig.summary}</p> : null}
                  <select
                    aria-label="Resultado do teste"
                    value={calibrationResultStatus}
                    onChange={(event) => setCalibrationResultStatus(event.target.value as CalibrationRunRecord["result_status"])}
                  >
                    <option value="passed">aprovado</option>
                    <option value="warning">atenção</option>
                    <option value="failed">falhou</option>
                    <option value="skipped">ignorado</option>
                  </select>
                  {calibrationResultFormConfig?.showMaterial ? (
                    <label>
                      <span>Material</span>
                      <input value={calibrationMaterial} onChange={(event) => setCalibrationMaterial(event.target.value)} placeholder="Ex.: PLA, ABS, ASA" />
                    </label>
                  ) : null}
                  {calibrationResultFormConfig?.showPlate ? (
                    <label>
                      <span>Chapa</span>
                      <input value={calibrationPlateName} onChange={(event) => setCalibrationPlateName(event.target.value)} placeholder="Ex.: Texturizada, lisa, PEI" />
                    </label>
                  ) : null}
                  {calibrationResultFormConfig?.showNozzle ? (
                    <label>
                      <span>Toolhead/nozzle</span>
                      <input value={calibrationNozzle} onChange={(event) => setCalibrationNozzle(event.target.value)} placeholder="Ex.: T0, T1, 0.4" />
                    </label>
                  ) : null}
                  <label>
                    <span>{calibrationResultFormConfig?.observedLabel ?? "Valor observado"}</span>
                    <input
                      value={calibrationObservedValue}
                      onChange={(event) => setCalibrationObservedValue(event.target.value)}
                      placeholder={calibrationResultFormConfig?.observedPlaceholder ?? "Resumo objetivo do resultado"}
                    />
                  </label>
                  <label>
                    <span>{calibrationResultFormConfig?.notesLabel ?? "Notas"}</span>
                    <textarea
                      value={calibrationNotes}
                      onChange={(event) => setCalibrationNotes(event.target.value)}
                      placeholder={calibrationResultFormConfig?.notesPlaceholder ?? "Detalhes úteis para repetir ou investigar depois"}
                    />
                  </label>
                  <div className="modal-footer">
                    <button type="button" className="secondary-button" onClick={() => setCalibrationResultFormOpen(false)}>
                      Cancelar
                    </button>
                    <button type="submit" className="primary-button" disabled={!selectedPrinterId || loading}>
                      Salvar resultado
                    </button>
                  </div>
                </form>
              ) : null}
            </div>
          </div>
        ) : null}

        <article className="panel wide panel-section panel-calibration">
          <div className="panel-heading">
            <div>
              <h2>Contexto de calibração</h2>
              <p className="muted">Estado da impressora ativa, sequência recomendada e histórico local.</p>
            </div>
            <strong>{selectedPrinter?.name ?? "Sem impressora"}</strong>
          </div>
          <div className="calibration-summary">
            <Badge label="Origem" value={formatOperationDataState(operationStatus?.data_state)} />
            <Badge label="Print state" value={operationStatus?.miscellaneous.print_state ?? "-"} />
            <Badge label="Hotend" value={formatTemperature(hotendTemperature?.temperature)} />
            <Badge label="Mesa" value={formatTemperature(bedTemperature?.temperature)} />
            <Badge label="Catálogo" value={calibrationSummary?.catalog_count ?? calibrationTests.length + calibrationHiddenTests.length} />
            <Badge label="Liberados" value={calibrationTests.length} />
            <Badge label="Bloqueados" value={calibrationBlockedGcodeCount} />
            <Badge label="Último Z" value={formatLatestZOffset(zOffsetRecords[0])} />
          </div>
          {operationStatus?.data_state === "last_snapshot" ? (
            <div className="operation-state last-snapshot">
              <Database size={17} />
              <div>
                <strong>Usando último snapshot conhecido</strong>
                <span>
                  Snapshot #{operationStatus.last_snapshot?.id ?? "-"} de {operationStatus.last_snapshot?.created_at ?? "-"}.
                  A impressora selecionada existe, mas a leitura ao vivo do Moonraker não respondeu neste carregamento.
                </span>
              </div>
            </div>
          ) : null}
          {operationStatus?.data_state === "offline" ? (
            <div className="operation-state offline">
              <AlertTriangle size={17} />
              <div>
                <strong>Moonraker sem leitura ao vivo</strong>
                <span>{operationStatus.error ?? "A tela mantém catálogo e histórico local, mas bloqueia testes que exigem G-code."}</span>
              </div>
            </div>
          ) : null}
          <div className="calibration-flow-grid">
            <section className="calibration-recommendations calibration-roadmap-panel">
              <div className="section-heading-compact">
                <strong>Sequência de calibração</strong>
                <span>{visibleCalibrationCompletedSteps}/{calibrationSequencePreview.length} visíveis tratados</span>
              </div>
              <p className="muted calibration-section-note">
                Siga de cima para baixo quando fizer sentido. Itens com G-code somem sem leitura ao vivo; use Pular para seguir sem aprovar.
              </p>
              {calibrationHiddenTests.length ? (
                <p className="muted calibration-section-note">
                  {calibrationHiddenTests.length} item(ns) que dependem da impressora online estão ocultos neste contexto.
                </p>
              ) : null}
              {calibrationSequencePreview.length === 0 ? <p className="muted">Aguardando sequência da impressora selecionada.</p> : null}
              <ol className="calibration-sequence-list">
                {calibrationSequencePreview.map((step) => {
                  const stepTest = calibrationTests.find((test) => test.test_key === step.test_key);
                  const hiddenReason = calibrationHiddenTests.find((test) => test.test_key === step.test_key)?.reason;
                  return (
                    <li key={`${step.order}-${step.test_key}`} className={`calibration-sequence-row ${step.status}`}>
                      <span className="calibration-step-index">{step.order}</span>
                      <span className="calibration-step-phase">{formatCalibrationPhase(step.phase).replace(/^\d+\.\s*/, "")}</span>
                      <span className="calibration-step-main">
                        <strong>{step.title}</strong>
                        <small>{formatExecutionMode(step.execution_mode)} · risco {formatRiskLevel(step.risk_level)}</small>
                      </span>
                      <em>{hiddenReason ? "bloqueado" : formatCalibrationSequenceStatus(step.status)}</em>
                      <span className="calibration-step-actions">
                        <button
                          type="button"
                          className="icon-button calibration-action-icon"
                          onClick={() => stepTest && setCalibrationHelpTestKey(stepTest.test_key)}
                          disabled={!stepTest}
                          aria-label={`Ajuda de ${step.title}`}
                          title="Ajuda"
                        >
                          <HelpCircle size={16} />
                        </button>
                        {stepTest?.gcode.length ? (
                          <button
                            type="button"
                            className="icon-button calibration-action-icon"
                            onClick={() => void openCalibrationExecute(stepTest)}
                            disabled={!selectedPrinterId || loading || Boolean(hiddenReason)}
                            aria-label={`Executar ${step.title}`}
                            title="Executar"
                          >
                            <Play size={16} />
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="icon-button calibration-action-icon"
                            onClick={() => stepTest && openCalibrationResult(stepTest, true)}
                            disabled={!selectedPrinterId || loading || !stepTest}
                            aria-label={`Registrar resultado de ${step.title}`}
                            title="Registrar"
                          >
                            <ClipboardCheck size={16} />
                          </button>
                        )}
                        <button
                          type="button"
                          className="icon-button calibration-action-icon"
                          onClick={() => stepTest && openCalibrationResult(stepTest, true, "skipped")}
                          disabled={!selectedPrinterId || loading || !stepTest}
                          aria-label={`Pular ${step.title}`}
                          title="Pular"
                        >
                          <SkipForward size={16} />
                        </button>
                      </span>
                    </li>
                  );
                })}
              </ol>
            </section>
            <section className="calibration-recommendations calibration-action-panel">
              <div className="section-heading-compact">
                <strong>Próximo ajuste</strong>
                <span>{calibrationVisibleGcodeCount} com G-code liberado(s)</span>
              </div>
              {visibleCalibrationRecommendations.length === 0 ? <p className="muted">Sem recomendações pendentes visíveis neste contexto.</p> : null}
              {visibleCalibrationRecommendations.map((test) => {
                const blockedReason = calibrationHiddenTests.find((hidden) => hidden.test_key === test.test_key)?.reason;
                const availableTest = calibrationTests.find((candidate) => candidate.test_key === test.test_key);
                return (
                  <div key={test.test_key} className={`calibration-next-row ${test.risk_level}`}>
                    <span className="calibration-next-title">
                      <strong>{test.title}</strong>
                      <em>{blockedReason ? "bloqueado" : "disponível"}</em>
                    </span>
                    <small>{formatCalibrationCategory(test.category)} · risco {formatRiskLevel(test.risk_level)}</small>
                    <small>{blockedReason ?? test.reason}</small>
                    <span className="calibration-next-actions">
                      <button
                        type="button"
                        className="icon-button calibration-action-icon"
                        onClick={() => availableTest && setCalibrationHelpTestKey(availableTest.test_key)}
                        disabled={!availableTest}
                        aria-label={`Ver orientação de ${test.title}`}
                        title="Ver orientação"
                      >
                        <HelpCircle size={16} />
                      </button>
                      {availableTest?.gcode.length ? (
                        <button
                          type="button"
                          className="icon-button calibration-action-icon"
                          onClick={() => void openCalibrationExecute(availableTest)}
                          disabled={!selectedPrinterId || loading || Boolean(blockedReason)}
                          aria-label={`Executar ${test.title} com confirmação`}
                          title="Executar com confirmação"
                        >
                          <Play size={16} />
                        </button>
                      ) : (
                        <button
                          type="button"
                          className="icon-button calibration-action-icon"
                          onClick={() => availableTest && openCalibrationResult(availableTest, true)}
                          disabled={!selectedPrinterId || loading || !availableTest}
                          aria-label={`Registrar resultado de ${test.title}`}
                          title="Registrar resultado"
                        >
                          <ClipboardCheck size={16} />
                        </button>
                      )}
                    </span>
                  </div>
                );
              })}
            </section>
          </div>
        </article>

        <article className="panel wide panel-section panel-calibration calibration-fine-tune-panel">
          <div className="panel-heading">
            <div>
              <h2>Perfil aprovado de primeira camada</h2>
              <p className="muted">Registre apenas depois de aprovar a primeira camada. Futuramente este perfil deve ser sugerido pelos resultados acima.</p>
            </div>
            <strong>{formatLatestZOffset(zOffsetRecords[0])}</strong>
          </div>
          {!zOffsetFormOpen ? (
            <div className="first-layer-empty-state">
              <div>
                <strong>O que será registrado?</strong>
                <span>
                  Chapa usada, material, toolhead/nozzle, valor final de Z-offset e observações do teste. O app usa isso para comparar ajustes futuros.
                </span>
              </div>
              <button type="button" onClick={() => setZOffsetFormOpen(true)} disabled={!selectedPrinterId || loading}>
                Registrar perfil aprovado
              </button>
            </div>
          ) : null}
          {zOffsetFormOpen ? (
            <div className="wizard-actions">
              <button type="button" onClick={() => void evaluateZOffsetWizard()} disabled={!selectedPrinterId || loading}>
                Avaliar antes de salvar
              </button>
              <span>Preencha com o material e o valor real usado no teste. Nada é assumido automaticamente.</span>
            </div>
          ) : null}
          {zOffsetWizardPlan ? (
            <div className={`z-offset-wizard ${zOffsetWizardPlan.alert_level}`}>
              <div>
                <strong>{formatZOffsetAlert(zOffsetWizardPlan.alert_level)}</strong>
                <span>{zOffsetWizardPlan.recommendation}</span>
              </div>
              <div className="wizard-summary">
                <Badge label="Anterior" value={formatOptionalNumber(zOffsetWizardPlan.previous_offset_value)} />
                <Badge label="Novo" value={zOffsetWizardPlan.proposed_offset_value.toFixed(3)} />
                <Badge label="Delta" value={formatOptionalNumber(zOffsetWizardPlan.delta_value)} />
                <Badge label="Modo" value={zOffsetWizardPlan.safe_mode} />
              </div>
              <div className="wizard-steps">
                {zOffsetWizardPlan.steps.map((step) => (
                  <label key={step.key} className="wizard-step">
                    <input
                      type="checkbox"
                      checked={zOffsetWizardChecks[step.key] ?? false}
                      onChange={() => toggleWizardCheck(step.key)}
                    />
                    <span>
                      <strong>{step.title}</strong>
                      <small>{step.detail}</small>
                      {step.command ? <code>{step.command}</code> : null}
                    </span>
                  </label>
                ))}
              </div>
              <small className="muted">
                Checklist confirmado: {confirmedWizardSteps(zOffsetWizardChecks)}/{zOffsetWizardPlan.steps.length}
              </small>
            </div>
          ) : null}
          {zOffsetFormOpen ? (
            <form className="z-offset-form" onSubmit={(event) => void createZOffsetRecord(event)}>
              <label>
                <span>Chapa</span>
                <input
                  aria-label="Chapa"
                  value={zOffsetPlateName}
                  onChange={(event) => setZOffsetPlateName(event.target.value)}
                  placeholder="Ex.: Texturizada, lisa, PEI"
                />
              </label>
              <label>
                <span>Material</span>
                <input
                  aria-label="Material"
                  value={zOffsetMaterial}
                  onChange={(event) => setZOffsetMaterial(event.target.value)}
                  placeholder="Ex.: PLA, ABS, ASA"
                />
              </label>
              <label>
                <span>Toolhead/nozzle</span>
                <input
                  aria-label="Nozzle ou toolhead"
                  value={zOffsetNozzle}
                  onChange={(event) => setZOffsetNozzle(event.target.value)}
                  placeholder="Ex.: T0, T1, 0.4"
                />
              </label>
              <label>
                <span>Z-offset aprovado</span>
                <input
                  aria-label="Valor do Z-offset"
                  type="number"
                  step="0.001"
                  value={zOffsetValue}
                  onChange={(event) => setZOffsetValue(event.target.value)}
                  placeholder="Ex.: -0.295"
                />
              </label>
              <label>
                <span>Observação</span>
                <textarea
                  aria-label="Notas do Z-offset"
                  value={zOffsetNotes}
                  onChange={(event) => setZOffsetNotes(event.target.value)}
                  placeholder="Ex.: primeira camada uniforme após limpeza da mesa"
                />
              </label>
              <div className="z-offset-form-actions">
                <button type="button" onClick={() => setZOffsetFormOpen(false)}>
                  Cancelar
                </button>
                <button type="submit" disabled={!selectedPrinterId || loading}>
                  Salvar perfil
                </button>
              </div>
            </form>
          ) : null}
          <div className="z-offset-list">
            {zOffsetRecords.length === 0 ? <p className="muted">Nenhum perfil aprovado registrado ainda.</p> : null}
            {zOffsetRecords.map((record) => (
              <div key={record.id} className={`z-offset-row ${record.alert_level}`}>
                <div>
                  <strong>{record.offset_value.toFixed(3)}</strong>
                  <span>
                    {record.plate_name} · {record.material} · {record.nozzle} · {record.recorded_at}
                  </span>
                  <small>
                    Anterior: {formatOptionalNumber(record.previous_offset_value)} · Delta:{" "}
                    {formatOptionalNumber(record.delta_value)} · {formatZOffsetAlert(record.alert_level)}
                  </small>
                  {record.notes ? <small>{record.notes}</small> : null}
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-maintenance">
          <div className="maintenance-workspace">
            <section className="maintenance-hero">
              <div>
                <span className="section-kicker">Plano preventivo</span>
                <h2>{selectedPrinter?.name ?? "Impressora"}</h2>
                <p>
                  {nextMaintenanceTask
                    ? `${nextMaintenanceTask.name}: ${formatDueStatus(nextMaintenanceTask)}`
                    : "Nenhuma rotina preventiva criada."}
                </p>
              </div>
              <div className="maintenance-hero-actions">
                {maintenancePrintHoursAvailable ? (
                  <div className="maintenance-print-hours-chip">
                    <Timer size={16} />
                    <span>Total de impressão</span>
                    <strong>{formatHours(maintenancePrintHours.total_print_hours ?? 0)}</strong>
                  </div>
                ) : null}
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => void createDefaultMaintenanceTasks()}
                  disabled={!selectedPrinterId || loading || maintenanceSummary?.recommended_tasks.length === 0}
                >
                  <Plus size={16} />
                  Recarregar catálogo
                </button>
              </div>
            </section>

            <div className="maintenance-status-grid">
              <Metric label="Vencidas" value={String(maintenanceSummary?.counts.due ?? 0)} />
              <Metric label="Próximas" value={String(maintenanceSummary?.counts.soon ?? 0)} />
              <Metric label="Em dia" value={String(maintenanceSummary?.counts.ok ?? 0)} />
              <Metric label="Registradas" value={String(maintenanceTasks.length)} />
            </div>

            <section className="maintenance-panel-card">
              <div className="maintenance-section-heading">
                <div>
                  <h3>Rotinas preventivas</h3>
                  <p className="muted">Cada rotina gera alerta quando vencer.</p>
                </div>
                <div className="dense-toolbar filter-toolbar" aria-label="Filtros de manutenção">
                  <button type="button" className={maintenanceFilter === "all" ? "active" : ""} onClick={() => setMaintenanceFilter("all")}>
                    Todas
                  </button>
                  <button type="button" className={maintenanceFilter === "due" ? "active" : ""} onClick={() => setMaintenanceFilter("due")}>
                    Vencidas
                  </button>
                  <button type="button" className={maintenanceFilter === "soon" ? "active" : ""} onClick={() => setMaintenanceFilter("soon")}>
                    Próximas
                  </button>
                  <button type="button" className={maintenanceFilter === "ok" ? "active" : ""} onClick={() => setMaintenanceFilter("ok")}>
                    Em dia
                  </button>
                </div>
              </div>

              {visibleMaintenanceTasks.length === 0 ? (
                <div className="empty-maintenance-state">
                  <strong>Nenhuma rotina neste filtro.</strong>
                  <span>O catálogo padrão será carregado automaticamente para esta impressora.</span>
                </div>
              ) : null}

              <div className="maintenance-card-grid">
                {visibleMaintenanceTasks.map((task) => (
                  <article key={task.id} className={`maintenance-task-card ${task.is_active ? task.due_status : "inactive"}`}>
                    <div className="maintenance-task-card-header">
                      <span className={`status-pill ${task.is_active ? task.due_status : "inactive"}`}>{formatDueStatus(task)}</span>
                      <strong>{task.name}</strong>
                    </div>
                    <div className="maintenance-task-meta">
                      <span>{task.component}</span>
                      <span>{task.is_active ? formatMaintenanceInterval(task) : "Sem lembrete recorrente"}</span>
                      <span>Última: {formatOptionalLocalDateTime(task.last_done_at)}</span>
                      {task.interval_kind === "print_hours" ? (
                        <>
                          <span>Base: {formatOptionalHours(task.last_done_print_hours)}</span>
                          <span>Atual: {formatOptionalHours(task.current_print_hours)}{task.current_print_hours_source === "cached" ? " · desatualizado" : ""}</span>
                          <span>{formatPrintHoursDueLine(task)}</span>
                        </>
                      ) : null}
                    </div>
                    <div className="maintenance-card-actions">
                      <button type="button" className="maintenance-done-button" onClick={() => openMaintenanceDoneModal(task)} disabled={loading}>
                        <CheckCircle2 size={14} />
                        Marcar feita
                      </button>
                      {task.last_done_at ? (
                        <button
                          type="button"
                          className="ghost-button danger-ghost"
                          onClick={() => void deleteLatestMaintenanceTaskEvent(task.id)}
                          disabled={loading}
                        >
                          <Undo2 size={14} />
                          Desfazer
                        </button>
                      ) : null}
                    </div>
                  </article>
                ))}
              </div>

              {maintenanceSummary?.recommended_tasks.length ? (
                <div className="maintenance-catalog-note">
                  <strong>{maintenanceSummary.recommended_tasks.length} rotina(s) do catálogo ainda não foram ativadas.</strong>
                  <button type="button" className="secondary-button" onClick={() => void createDefaultMaintenanceTasks()} disabled={!selectedPrinterId || loading}>
                    Ativar restantes
                  </button>
                </div>
              ) : null}
            </section>

            <section
              className="maintenance-free-card"
              role="button"
              tabIndex={0}
              onClick={() => openMaintenanceFreeModal()}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  openMaintenanceFreeModal();
                }
              }}
            >
              <div>
                <span className="section-kicker">Registro livre</span>
                <h3>Falha, ajuste ou anotação</h3>
                <p>Use para algo que não está no catálogo. Pode virar lembrete, se você definir um prazo.</p>
              </div>
              <button type="button" className="secondary-button" onClick={() => openMaintenanceFreeModal()}>
                <Plus size={16} />
                Adicionar registro
              </button>
            </section>

            <section className="maintenance-panel-card">
              <div className="maintenance-section-heading">
                <div>
                  <h3>Histórico</h3>
                  <p className="muted">{maintenanceEvents.length} registro(s)</p>
                </div>
              </div>
              <div className="maintenance-timeline">
                {maintenanceEvents.length === 0 ? <p className="muted">Nenhum evento registrado.</p> : null}
                {maintenanceEvents.map((event) => (
                  <div key={event.id} className="maintenance-event-row">
                    <div className="maintenance-event-content">
                      <strong>{event.title}</strong>
                      <span>
                        {formatMaintenanceEventType(event.event_type)} · {event.component ?? "-"} · {formatLocalDateTime(event.performed_at)}
                      </span>
                      {event.notes ? <small>{event.notes}</small> : null}
                    </div>
                    <button
                      type="button"
                      className="ghost-button danger-ghost"
                      onClick={() => void deleteMaintenanceEvent(event.id)}
                      disabled={loading}
                    >
                      <Trash2 size={14} />
                      Remover
                    </button>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </article>

        <article className="panel wide panel-section panel-reports">
          <div className="panel-heading">
            <h2>Relatório sanitizado</h2>
            <button type="button" onClick={() => void loadSanitizedReport()} disabled={!selectedPrinterId || loading}>
              Gerar relatório
            </button>
          </div>
          <p className="muted">
            Markdown read-only para compartilhar diagnóstico sem URLs, IPs, caminhos locais ou valores sensíveis detectáveis.
          </p>
          {sanitizedReport ? (
            <>
              <div className="audit-counts">
                <Badge label="Formato" value={sanitizedReport.format} />
                <Badge label="Modo" value={sanitizedReport.safe_mode} />
                <Badge label="Origem" value={formatChecklistDataState(sanitizedReport.data_state)} />
                <Badge label="Redações" value={sanitizedReport.redactions.length} />
                <Badge label="Impressora" value={sanitizedReport.printer_id} />
              </div>
              <div className="redaction-list">
                {sanitizedReport.redactions.length === 0 ? (
                  <span>Nenhuma redação detectada nos dados usados.</span>
                ) : (
                  sanitizedReport.redactions.map((redaction) => <span key={redaction}>{formatRedaction(redaction)}</span>)
                )}
              </div>
              <pre className="report-preview">{sanitizedReport.markdown}</pre>
            </>
          ) : null}
        </article>

        <article className="panel wide panel-section panel-reports">
          <div className="panel-heading">
            <h2>Backups</h2>
            <strong>Dry-run seguro</strong>
          </div>
          <form className="backup-form" onSubmit={(event) => void createBackupPolicy(event)}>
            <input
              aria-label="Nome da política"
              value={backupName}
              onChange={(event) => setBackupName(event.target.value)}
              placeholder="Nome"
            />
            <input
              aria-label="Origem do backup"
              value={backupSourcePath}
              onChange={(event) => setBackupSourcePath(event.target.value)}
              placeholder="/home/pi/printer_data/config"
            />
            <input
              aria-label="Destino do backup"
              value={backupDestinationPath}
              onChange={(event) => setBackupDestinationPath(event.target.value)}
              placeholder="/home/pi/printer_data/backups/printora"
            />
            <label className="inline-check">
              <input
                type="checkbox"
                checked={backupDryRunOnly}
                onChange={(event) => setBackupDryRunOnly(event.target.checked)}
              />
              Somente dry-run
            </label>
            <button type="submit" disabled={!selectedPrinterId || loading}>
              Criar política
            </button>
          </form>
          <div className="backup-list">
            {backupPolicies.length === 0 ? <p className="muted">Nenhuma política de backup cadastrada.</p> : null}
            {backupPolicies.map((policy) => (
              <div key={policy.id} className="backup-row">
                <div>
                  <strong>{policy.name}</strong>
                  <span>{policy.source_path}</span>
                  <small>
                    Destino: {policy.destination_path} · {policy.dry_run_only ? "somente dry-run" : "execução local habilitada"}
                  </small>
                </div>
                <div>
                  <small>Exclusões: {policy.exclude_patterns.join(", ")}</small>
                </div>
                <div className="backup-actions">
                  <button type="button" onClick={() => void createBackupDryRun(policy.id)} disabled={loading}>
                    Dry-run
                  </button>
                  <button
                    type="button"
                    onClick={() => void executeLocalBackup(policy.id)}
                    disabled={loading || policy.dry_run_only}
                  >
                    Executar local
                  </button>
                </div>
              </div>
            ))}
          </div>
          <details className="backup-runs collapsible-panel">
            <summary>Histórico de backups</summary>
            {backupRuns.length === 0 ? <p className="muted">Nenhum dry-run registrado.</p> : null}
            {backupRuns.map((run) => (
              <div key={run.id} className="backup-run-row">
                <strong>#{run.id} · {run.status}</strong>
                <span>{run.created_at}</span>
                <small>{run.message}</small>
              </div>
            ))}
          </details>
          <div className="backup-form">
            <input
              aria-label="Backup base"
              value={backupCompareBasePath}
              onChange={(event) => setBackupCompareBasePath(event.target.value)}
              placeholder="/path/base.zip"
            />
            <input
              aria-label="Backup alvo"
              value={backupCompareTargetPath}
              onChange={(event) => setBackupCompareTargetPath(event.target.value)}
              placeholder="/path/novo.zip"
            />
            <button type="button" onClick={() => void compareBackupArchives()} disabled={loading || !backupCompareBasePath || !backupCompareTargetPath}>
              Comparar backups
            </button>
          </div>
          {backupCompareResult ? (
            <div className="backup-run-row">
              <strong>{backupCompareResult.summary}</strong>
              <small>Adicionados: {backupCompareResult.added.join(", ") || "-"}</small>
              <small>Removidos: {backupCompareResult.removed.join(", ") || "-"}</small>
              <small>Alterados: {backupCompareResult.changed.join(", ") || "-"}</small>
            </div>
          ) : null}
          <div className="backup-form">
            <input
              aria-label="Arquivo de backup para restore"
              value={backupRestoreArchivePath}
              onChange={(event) => setBackupRestoreArchivePath(event.target.value)}
              placeholder="/path/backup.zip"
            />
            <input
              aria-label="Raiz de restore"
              value={backupRestoreRoot}
              onChange={(event) => setBackupRestoreRoot(event.target.value)}
              placeholder="/home/pi/printer_data/config"
            />
            <textarea
              aria-label="Arquivos para restore"
              value={backupRestoreFiles}
              onChange={(event) => setBackupRestoreFiles(event.target.value)}
              placeholder="printer.cfg"
            />
            <input
              aria-label="Confirmação do gate de restore"
              value={backupRestoreConfirmation}
              onChange={(event) => setBackupRestoreConfirmation(event.target.value)}
              placeholder="BLOCK_REAL_RESTORE"
            />
            <button type="button" onClick={() => void createBackupRestorePlan()} disabled={loading || !backupRestoreArchivePath || !backupRestoreRoot}>
              Planejar restore
            </button>
            <button type="button" onClick={() => void validateBackupRestoreGate()} disabled={loading || !backupRestoreArchivePath || !backupRestoreRoot}>
              Validar gate restore
            </button>
          </div>
          {backupRestorePlan ? (
            <details className="backup-run-row" open>
              <summary>
                Restore dry-run · {backupRestorePlan.selected_files.length} arquivo(s) · bloqueado: {formatBoolean(backupRestorePlan.blocked)}
              </summary>
              <small>{backupRestorePlan.message}</small>
              {backupRestorePlan.missing_files.length ? <small>Ausentes: {backupRestorePlan.missing_files.join(", ")}</small> : null}
              <pre>{backupRestorePlan.planned_commands.join("\n")}</pre>
            </details>
          ) : null}
          {backupRestoreGate ? (
            <details className="backup-run-row" open>
              <summary>
                Gate restore · confirmação: {formatBoolean(backupRestoreGate.accepted_confirmation)} · bloqueado:{" "}
                {formatBoolean(backupRestoreGate.blocked)}
              </summary>
              <small>{backupRestoreGate.message}</small>
              <small>Modo: {backupRestoreGate.safe_mode}</small>
              <strong>Rollback futuro obrigatório</strong>
              <ol>
                {backupRestoreGate.rollback_plan.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ol>
              <pre>{backupRestoreGate.plan.planned_commands.join("\n")}</pre>
            </details>
          ) : null}
        </article>

        <article className="panel wide panel-section panel-reports">
          <h2>Snapshots</h2>
          {snapshots.length >= 2 ? (
            <div className="snapshot-compare">
              <label>
                Base
                <select
                  value={fromSnapshotId ?? ""}
                  onChange={(event) => setFromSnapshotId(Number(event.target.value))}
                >
                  {snapshots.map((snapshot) => (
                    <option key={snapshot.id} value={snapshot.id}>
                      #{snapshot.id} · {snapshot.created_at}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Atual
                <select
                  value={toSnapshotId ?? ""}
                  onChange={(event) => setToSnapshotId(Number(event.target.value))}
                >
                  {snapshots.map((snapshot) => (
                    <option key={snapshot.id} value={snapshot.id}>
                      #{snapshot.id} · {snapshot.created_at}
                    </option>
                  ))}
                </select>
              </label>
              <button
                type="button"
                onClick={() => void compareSnapshots()}
                disabled={!fromSnapshotId || !toSnapshotId || fromSnapshotId === toSnapshotId || loading}
              >
                Comparar
              </button>
            </div>
          ) : null}
          {snapshotDiff ? (
            <div className={`snapshot-diff ${snapshotDiff.highest_severity}`}>
              <strong>{snapshotDiff.summary}</strong>
              {snapshotDiff.changes.length === 0 ? (
                <p className="muted">Nenhuma mudança relevante detectada.</p>
              ) : (
                <div className="diff-list">
                  {snapshotDiff.changes.map((change) => (
                    <div key={`${change.field}-${change.title}`} className={`diff-row ${change.severity}`}>
                      <div>
                        <strong>{change.title}</strong>
                        <span>{formatSeverity(change.severity)}</span>
                      </div>
                      <p>{change.detail}</p>
                      <small>
                        Antes: {formatUnknown(change.before)} · Depois: {formatUnknown(change.after)}
                      </small>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
          <div className="snapshot-list">
            {snapshots.length === 0 ? <p className="muted">Nenhum snapshot capturado.</p> : null}
            {snapshots.map((snapshot) => (
              <div key={snapshot.id} className="snapshot-row">
                <strong>#{snapshot.id}</strong>
                <span>{snapshot.created_at}</span>
                <span>{snapshot.snapshot_type}</span>
                <small>{formatUnknown(snapshot.summary)}</small>
              </div>
            ))}
          </div>
        </article>

        <article className="panel panel-section panel-monitoring">
          <h2>Moonraker</h2>
          <Metric label="Conexão" value={status?.connected ? "Conectado" : "Desconectado"} />
          <Metric label="URL" value={status?.moonraker_url ?? "-"} />
          <Metric label="Klippy" value={status?.server?.klippy_state ?? "-"} />
          <Metric label="Moonraker" value={status?.server?.moonraker_version ?? "-"} />
        </article>

        <article className="panel panel-section panel-monitoring">
          <h2>Klipper</h2>
          <Metric label="Estado" value={status?.printer?.state ?? "-"} />
          <Metric label="Mensagem" value={status?.printer?.state_message ?? "-"} />
          <Metric label="Versão" value={status?.printer?.software_version ?? "-"} />
        </article>

        <article className={`panel wide panel-section panel-settings releases-panel ${releasePanelClass(systemReleases)}`}>
          <div className="panel-header-row">
            <div>
              <h2>Releases do Printora</h2>
              <p>{releaseLoading ? "Consultando GitHub Releases..." : systemReleases?.message ?? "Status ainda não carregado."}</p>
            </div>
            <button
              type="button"
              className="secondary-button"
              onClick={() => void loadSystemReleases()}
              disabled={releaseLoading}
            >
              <RefreshCw size={16} />
              {releaseLoading ? "Verificando" : "Verificar releases"}
            </button>
          </div>
          <div className="release-summary-grid">
            <Metric label="Versão instalada" value={systemReleases?.installed_version ?? "-"} />
            <Metric label="Última release" value={systemReleases?.latest_release?.tag ?? "-"} />
            <Metric label="Canal" value={systemReleases?.channel ?? "-"} />
            <Metric label="Status" value={formatReleaseUpdateStatus(systemReleases, releaseLoading, releaseError)} />
          </div>
          {releaseError ? (
            <div className="action-result warning">
              <strong>Erro de rede</strong>
              <span>{releaseError}</span>
            </div>
          ) : null}
          {systemReleases?.error ? (
            <div className="action-result warning">
              <strong>{formatReleaseSourceStatus(systemReleases.status)}</strong>
              <span>{systemReleases.error}</span>
            </div>
          ) : null}
          {systemReleases?.latest_release ? (
            <div className="release-latest-card">
              <div>
                <span className={`status-pill ${releaseStatusPillClass(systemReleases)}`}>
                  {formatReleaseUpdateStatus(systemReleases, false, null)}
                </span>
                <strong>{systemReleases.latest_release.name}</strong>
                <small>
                  {systemReleases.latest_release.tag} · {systemReleases.latest_release.published_at ?? "sem data"} · {systemReleases.latest_release.channel}
                </small>
              </div>
              <p>{systemReleases.latest_release.changelog_summary || "Sem changelog informado."}</p>
              {systemReleases.latest_release_available ? (
                <div className="update-actions">
                  <button type="button" className="secondary-button" onClick={() => void planSelfUpdate()} disabled={releaseLoading}>
                    <ShieldCheck size={16} />
                    Planejar update
                  </button>
                  {selfUpdatePlan?.run.target_tag === systemReleases.latest_release.tag && selfUpdatePlan.update_supported ? (
                    <button type="button" className="secondary-button" onClick={() => setSelfUpdateModalOpen(true)}>
                      <ShieldAlert size={16} />
                      Atualizar agora
                    </button>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
          {selfUpdateMessage ? (
            <div className={`action-result ${selfUpdateConnectionLost ? "warning" : ""}`}>
              <strong>{selfUpdateConnectionLost ? "Conexão interrompida" : "Updater do Printora"}</strong>
              <span>{selfUpdateMessage}</span>
            </div>
          ) : null}
          <div className="release-list">
            <details className="collapsible-panel">
              <summary>Releases anteriores</summary>
              {releaseLoading ? <p className="muted">Carregando releases de produção...</p> : null}
              {!releaseLoading && displayedReleaseRows.length === 0 ? (
                <p className="muted">Nenhuma release anterior para listar.</p>
              ) : null}
              {displayedReleaseRows.map((release) => (
                <div key={release.tag} className={`release-row ${release.installed ? "installed" : ""}`}>
                  <div>
                    <strong>{release.name}</strong>
                    <span>
                      {release.tag} · {release.published_at ?? "sem data"} · {release.installed ? "instalada" : release.channel}
                    </span>
                  </div>
                  <p>{release.changelog_summary || "Sem changelog informado."}</p>
                </div>
              ))}
            </details>
          </div>
          <div className="self-update-history">
            <div className="panel-header-row compact">
              <div>
                <h3>Histórico de updates</h3>
              </div>
              <button type="button" className="ghost-button" onClick={() => void loadSelfUpdateHistory()}>
                <History size={15} />
                Recarregar
              </button>
            </div>
            {selfUpdateHistory.length === 0 ? <p className="muted">Nenhum update do Printora registrado.</p> : null}
            {selfUpdateHistory.slice(0, 5).map((run) => (
              <div key={run.id} className={`update-row ${selfUpdateRunClass(run.status)}`}>
                <div className="update-main">
                  <div>
                    <strong>#{run.id} · {run.target_tag}</strong>
                    <span>
                      {formatSelfUpdateStatus(run.status)} · {run.created_at}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => {
                      setSelfUpdateConfirmation("");
                      setSelfUpdateRollbackConfirmation("");
                      setSelfUpdatePlan({
                        safe_mode: "history",
                        update_supported: isSelfUpdateEnvironmentSupported(run.environment),
                        can_apply: false,
                        message: "Detalhes do update registrado.",
                        run,
                      });
                      setSelfUpdateModalOpen(true);
                    }}
                  >
                    <FileText size={15} />
                    Ver detalhes
                  </button>
                  {canRollbackSelfUpdateRun(run) ? (
                    <button
                      type="button"
                      className="secondary-button"
                      onClick={() => {
                        setSelfUpdateConfirmation("");
                        setSelfUpdateRollbackConfirmation("");
                        setSelfUpdatePlan({
                          safe_mode: "history",
                          update_supported: isSelfUpdateEnvironmentSupported(run.environment),
                          can_apply: false,
                          message: "Revise os detalhes antes do rollback.",
                          run,
                        });
                        setSelfUpdateModalOpen(true);
                      }}
                    >
                      <Undo2 size={15} />
                      Rollback
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className={`panel ${checklist?.can_print ? "ok" : "warn"} panel-section panel-monitoring`}>
          <h2>Checklist pós-update</h2>
          <strong className="summary">{checklist?.summary ?? "Aguardando dados"}</strong>
          {checklist ? (
            <div className="checklist-meta">
              <span>{formatChecklistDataState(checklist.data_state)}</span>
              <span>{checklist.source}</span>
            </div>
          ) : null}
          <div className="checks">
            {checklist?.items.map((item) => (
              <div key={item.key} className="check">
                <span className={checklistDotClass(item)} />
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-monitoring panel-reports">
          <h2>Auditoria somente leitura</h2>
          <strong className="summary">{audit?.summary ?? "Aguardando dados"}</strong>
          {audit ? (
            <div className="checklist-meta">
              <span>{formatChecklistDataState(audit.data_state ?? "live")}</span>
              <span>{audit.source ?? "-"}</span>
            </div>
          ) : null}
          <div className="audit-counts">
            <Badge label="Corrigir agora" value={audit?.counts.corrigir_agora ?? 0} />
            <Badge label="Monitorar" value={audit?.counts.monitorar ?? 0} />
            <Badge label="Precisa confirmação" value={audit?.counts.precisa_confirmacao ?? 0} />
            <Badge label="Ignorar" value={audit?.counts.ignorar ?? 0} />
          </div>
          <div className="findings">
            {audit?.findings.map((finding) => (
              <div key={finding.id} className={`finding ${finding.severity}`}>
                <div>
                  <strong>{finding.title}</strong>
                  <span>{finding.category} · {formatClassification(finding.classification)}</span>
                </div>
                <p>{finding.detail}</p>
                <small>{finding.safe_action}</small>
              </div>
            ))}
          </div>
        </article>

        <details className="panel wide panel-section panel-monitoring panel-settings collapsible-panel host-diagnostics-panel">
          <summary>Diagnóstico avançado do host</summary>
          <p className="muted">Leitura técnica do computador onde o Printora roda. Use quando precisar investigar systemd, CAN, symlinks ou repositórios locais.</p>
          <strong className="summary">{hostAudit?.summary ?? "Aguardando dados"}</strong>
          <div className="audit-counts">
            <Badge icon={Settings} label="Modo" value={hostAudit?.mode ?? "-"} />
            <Badge icon={Activity} label="Executou" value={hostAudit?.executed ? "sim" : "não"} />
            <Badge icon={AlertTriangle} label="Monitorar" value={hostAudit?.counts.monitorar ?? 0} />
            <Badge icon={ShieldCheck} label="Corrigir" value={hostAudit?.counts.corrigir_agora ?? 0} />
          </div>
          <div className="section-summary">
            {hostAudit?.section_summary
              ? Object.entries(hostAudit.section_summary).map(([key, value]) => (
                  <Metric key={key} label={formatMetricLabel(key)} value={formatUnknown(value)} />
                ))
              : null}
          </div>
          <div className="findings">
            {hostAudit?.findings.map((finding) => (
              <div key={finding.id} className={`finding ${finding.severity}`}>
                <div>
                  <strong>{finding.title}</strong>
                  <span>{finding.category} · {formatClassification(finding.classification)}</span>
                </div>
                <p>{finding.detail}</p>
                <small>{finding.safe_action}</small>
              </div>
            ))}
          </div>
        </details>
        </section>
      </div>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ConnectionTestRow({
  label,
  result,
  emptyDetail,
}: {
  label: string;
  result?: ConnectionCheckResult | null;
  emptyDetail?: string;
}) {
  if (!result) {
    return (
      <div className="connection-test-row idle">
        <span>{label}</span>
        <strong>não testado</strong>
        <small>{emptyDetail ?? "Clique em testar conexões."}</small>
      </div>
    );
  }
  return (
    <div className={`connection-test-row ${result.ok ? "ok" : "failed"}`}>
      <span>{label}</span>
      <strong>{result.ok ? "OK" : "falhou"}</strong>
      <small>{result.target} · {result.detail}</small>
    </div>
  );
}

function Badge({ icon: Icon, label, value }: { icon?: LucideIcon; label: string; value: number | string }) {
  return (
    <div className="badge">
      {Icon ? (
        <span className="badge-icon">
          <Icon size={17} strokeWidth={2.1} />
        </span>
      ) : null}
      <span className="badge-text">
        <span>{label}</span>
        <strong>{value}</strong>
      </span>
    </div>
  );
}

function OperationActionParameterFields({
  action,
  values,
  onChange,
}: {
  action: OperationAction;
  values: Record<string, string>;
  onChange: (actionId: string, parameterName: string, value: string) => void;
}) {
  const parameters = operationActionParameterSpecs(action.id);
  if (parameters.length === 0) {
    return <small className="operation-action-no-params">Sem parâmetros.</small>;
  }
  return (
    <div className="operation-action-params">
      {parameters.map((parameter) => (
        <label key={`${action.id}-${parameter.name}`}>
          <span>{formatOperationParameterLabel(parameter.name)}</span>
          {parameter.type === "enum" ? (
            <select
              value={values[parameter.name] ?? String(parameter.default ?? parameter.values?.[0] ?? "")}
              onChange={(event) => onChange(action.id, parameter.name, event.target.value)}
            >
              {(parameter.values ?? []).map((value) => (
                <option key={value} value={value}>
                  {value}
                </option>
              ))}
            </select>
          ) : (
            <input
              type={parameter.type === "number" ? "number" : "text"}
              min={parameter.min}
              max={parameter.max}
              value={values[parameter.name] ?? String(parameter.default ?? 0)}
              onChange={(event) => onChange(action.id, parameter.name, event.target.value)}
            />
          )}
        </label>
      ))}
    </div>
  );
}

function formatClassification(classification: AuditFinding["classification"]) {
  return classification.replace("_", " ");
}

function formatMetricLabel(label: string) {
  const labels: Record<string, string> = {
    klipper_state: "Klipper",
    klipper_version: "Versão Klipper",
    moonraker_version: "Moonraker",
    cpu_temp: "CPU temp.",
    disk_available_bytes: "Disco livre",
    memory_available_bytes: "Memória livre",
    api_latency_ms: "Latência API",
    data_state: "Origem",
    snapshot_count: "Snapshots",
    latest_snapshot_id: "Último snapshot",
    latest_diff_severity: "Último diff",
  };
  return labels[label] ?? label.replaceAll("_", " ");
}

function validatePrinterConnectionInput(moonrakerUrl: string, sshHost: string) {
  try {
    const parsedUrl = new URL(moonrakerUrl.trim());
    if (!["http:", "https:"].includes(parsedUrl.protocol)) {
      return "A URL do Moonraker precisa começar com http:// ou https://.";
    }
    if (parsedUrl.hostname.endsWith(".loca")) {
      return `Host Moonraker inválido: use ${parsedUrl.hostname}l ou um IP.`;
    }
  } catch {
    return "URL Moonraker inválida. Exemplo: http://voron.local:7125.";
  }

  const cleanSshHost = sshHost.trim();
  if (cleanSshHost.endsWith(".loca")) {
    return `Host SSH inválido: use ${cleanSshHost}l ou um IP.`;
  }
  return null;
}

function extractHost(url: string) {
  try {
    return new URL(url).hostname;
  } catch {
    return "";
  }
}

function formatSshStatus(printer: PrinterRecord) {
  if (!printer.ssh_host || !printer.ssh_username) {
    return "pendente";
  }
  return printer.ssh_credential_configured ? "configurado" : "sem credencial";
}

function formatSeverity(severity: SnapshotDiffItem["severity"]) {
  const labels: Record<SnapshotDiffItem["severity"], string> = {
    info: "informativo",
    monitorar: "monitorar",
    risco: "risco",
    bloqueio: "bloqueio",
  };
  return labels[severity];
}

function formatHealthSeverity(severity: HealthItem["severity"]) {
  const labels: Record<HealthItem["severity"], string> = {
    ok: "ok",
    info: "informativo",
    warning: "atenção",
    blocker: "bloqueio",
  };
  return labels[severity];
}

function formatRedaction(redaction: string) {
  const labels: Record<string, string> = {
    urls: "URLs",
    ip_addresses: "IPs",
    home_paths: "caminhos locais",
    secret_values: "valores sensíveis",
  };
  return labels[redaction] ?? redaction;
}

function formatMaintenanceEventType(eventType: MaintenanceEventRecord["event_type"]) {
  const labels: Record<MaintenanceEventRecord["event_type"], string> = {
    maintenance: "manutenção",
    failure: "falha",
    adjustment: "ajuste",
    note: "nota",
  };
  return labels[eventType];
}

function formatOptionalLocalDateTime(value?: string | null) {
  return value ? formatLocalDateTime(value) : "nunca";
}

function formatLocalDateTime(value: string | Date) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) {
    return typeof value === "string" ? value : "-";
  }
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(date);
}

function formatDueStatus(task: MaintenanceTaskRecord) {
  if (!task.is_active) {
    return "sem lembrete";
  }
  if (task.interval_kind === "print_hours") {
    if (task.due_status === "due") {
      return "pendente";
    }
    if (task.due_status === "soon") {
      return `${formatHours(task.print_hours_until_due ?? 0)} restantes · atenção`;
    }
    if (task.due_status === "not_validated") {
      return "aguardando horas";
    }
    if (task.due_status === "needs_review") {
      return "base precisa revisão";
    }
    if (task.due_status === "unknown") {
      return "status inválido";
    }
    return `${formatHours(task.print_hours_until_due ?? 0)} restantes`;
  }
  if (task.due_status === "due") {
    return "pendente";
  }
  if (task.due_status === "soon") {
    return `${task.days_until_due ?? "-"} dias restantes · atenção`;
  }
  if (task.due_status === "unknown") {
    return "data inválida";
  }
  return `${task.days_until_due ?? "-"} dias restantes`;
}

function formatMaintenanceInterval(task: MaintenanceTaskRecord) {
  if (task.interval_kind === "print_hours") {
    return `A cada ${formatHours(task.interval_value)} de impressão`;
  }
  return `A cada ${Math.round(task.interval_value || task.interval_days)} dias`;
}

function formatMaintenanceIntervalValue(task: MaintenanceTaskRecord) {
  const value = task.interval_kind === "print_hours" ? task.interval_value : task.interval_value || task.interval_days;
  return Number.isInteger(value) ? String(value) : String(Number(value.toFixed(1)));
}

function formatPrintHoursDueLine(task: MaintenanceTaskRecord) {
  if (task.due_status === "not_validated") {
    return task.due_detail ?? "Aguardando leitura de horas";
  }
  if (task.due_status === "needs_review") {
    return task.due_detail ?? "Base precisa revisão";
  }
  if (task.print_hours_until_due === null || task.print_hours_until_due === undefined) {
    return task.due_detail ?? "Sem leitura de horas";
  }
  if (task.due_status === "due") {
    const overdue = Math.max(0, (task.print_hours_delta ?? 0) - task.interval_value);
    return `Vencida há ${formatHours(overdue)}`;
  }
  return `Faltam ${formatHours(task.print_hours_until_due)}`;
}

function formatOptionalHours(value?: number | null) {
  return value === null || value === undefined ? "pendente" : formatHours(value);
}

function formatHours(value: number) {
  return `${Number(value.toFixed(1))}h`;
}

function formatLatestZOffset(record: ZOffsetRecord | undefined) {
  if (!record) {
    return "Sem histórico";
  }
  return `${record.offset_value.toFixed(3)} · ${formatZOffsetAlert(record.alert_level)}`;
}

function formatZOffsetAlert(alertLevel: ZOffsetRecord["alert_level"]) {
  const labels: Record<ZOffsetRecord["alert_level"], string> = {
    ok: "ok",
    monitorar: "monitorar",
    revisar: "revisar antes de imprimir",
  };
  return labels[alertLevel];
}

function formatOptionalNumber(value: number | null | undefined) {
  return typeof value === "number" ? value.toFixed(3) : "-";
}

function formatOptionalInt(value: number | null | undefined) {
  return typeof value === "number" ? String(value) : "-";
}

function formatLatestCan(record: CanBusRecord | undefined) {
  if (!record) {
    return "Sem histórico";
  }
  return `${formatCanAlert(record.alert_level)} · retries ${record.tx_retries}`;
}

function formatCanAlert(alertLevel: CanBusRecord["alert_level"]) {
  const labels: Record<CanBusRecord["alert_level"], string> = {
    ok: "ok",
    monitorar: "monitorar",
    problema: "problema físico/elétrico possível",
  };
  return labels[alertLevel];
}

function formatPluginClassification(classification: PluginAuditItem["classification"]) {
  const labels: Record<PluginAuditItem["classification"], string> = {
    necessario: "necessário",
    opcional: "opcional",
    legado_lixo_tecnico: "legado/lixo técnico",
    perigoso_remover_agora: "perigoso remover agora",
    seguro_remover_depois_backup: "seguro remover depois de backup",
    precisa_confirmacao: "precisa confirmação",
  };
  return labels[classification];
}

function formatPluginAction(action: PluginAuditItem["action"]) {
  const labels: Record<PluginAuditItem["action"], string> = {
    manter: "manter",
    investigar: "investigar",
    remover_depois_backup: "remover depois de backup",
    nao_remover_agora: "não remover agora",
  };
  return labels[action];
}

function formatUpdateStatus(status: UpdateComponent["status"]) {
  const labels: Record<UpdateComponent["status"], string> = {
    up_to_date: "atualizado",
    update_available: "update disponível",
    warning: "atenção",
    busy: "ocupado",
    unknown: "desconhecido",
  };
  return labels[status];
}

function formatReleaseUpdateStatus(
  releases: SystemReleasesResponse | null,
  loading: boolean,
  fetchError: string | null,
) {
  if (loading) {
    return "carregando";
  }
  if (fetchError) {
    return "erro de rede";
  }
  if (!releases) {
    return "não carregado";
  }
  if (releases.status !== "ok") {
    return formatReleaseSourceStatus(releases.status);
  }
  const labels: Record<SystemReleasesResponse["update_status"], string> = {
    up_to_date: "já atualizado",
    outdated: "update disponível",
    unknown: releases.releases.length === 0 ? "sem release publicada" : "desconhecido",
  };
  return labels[releases.update_status];
}

function formatReleaseSourceStatus(status: SystemReleasesResponse["status"]) {
  const labels: Record<SystemReleasesResponse["status"], string> = {
    ok: "online",
    offline: "GitHub offline",
    rate_limited: "limite do GitHub",
    disabled: "desabilitado",
    error: "erro de rede",
  };
  return labels[status];
}

function releaseStatusPillClass(releases: SystemReleasesResponse | null) {
  if (!releases || releases.status !== "ok") {
    return "warning";
  }
  if (releases.update_status === "up_to_date") {
    return "up_to_date";
  }
  if (releases.update_status === "outdated") {
    return "update_available";
  }
  return "warning";
}

function releasePanelClass(releases: SystemReleasesResponse | null) {
  if (!releases) {
    return "";
  }
  if (releases.status !== "ok") {
    return "warn";
  }
  return releases.update_status === "up_to_date" ? "ok" : "warn";
}

function countPendingUpdates(status: UpdateStatusResponse | null) {
  if (!status) {
    return "-";
  }
  return status.components.filter((component) => component.can_update || component.status === "update_available").length;
}

function isUpdateTargetConfirmedUpdated(status: UpdateStatusResponse | null, target: string) {
  if (!status) {
    return false;
  }
  if (target === "all") {
    return status.components.every((component) => !component.can_update && component.status !== "update_available" && component.status !== "busy");
  }
  const component = status.components.find((item) => item.name === target);
  return Boolean(component && !component.can_update && component.status === "up_to_date");
}

function buildAlertCenterItems({
  health,
  updateStatus,
  checklist,
  audit,
}: {
  health: HealthResponse | null;
  updateStatus: UpdateStatusResponse | null;
  checklist: ChecklistResponse | null;
  audit: AuditResponse | null;
}): AlertCenterItem[] {
  const items: AlertCenterItem[] = [];

  health?.items
    .filter((item) => item.severity === "blocker" || item.severity === "warning")
    .forEach((item) => {
      items.push({
        id: `health-${item.key}`,
        source: "Health Check",
        title: item.title,
        detail: item.detail,
        action: item.action,
        severity: item.severity === "blocker" ? "blocker" : "warning",
      });
    });

  updateStatus?.components
    .filter((component) => component.can_update || component.status === "warning" || component.warnings.length > 0 || component.anomalies.length > 0)
    .forEach((component) => {
      items.push({
        id: `update-${component.name}`,
        source: "Update Manager",
        title: component.title,
        detail:
          component.status === "warning"
            ? [...component.warnings, ...component.anomalies].filter(Boolean).join(" · ") || "Componente com aviso no Update Manager."
            : `${component.current_version ?? "-"} → ${component.remote_version ?? component.full_version ?? "-"}`,
        action: component.can_update ? "Atualização disponível. Revise e execute pela tela Atualizações." : "Reanalise o componente antes de agir.",
        severity: component.status === "warning" || component.anomalies.length > 0 ? "warning" : "info",
      });
    });

  checklist?.items
    .filter((item) => !item.ok)
    .forEach((item) => {
      items.push({
        id: `checklist-${item.key}`,
        source: "Checklist pós-update",
        title: item.title,
        detail: item.detail,
        action: "Corrija este item antes de considerar a impressora pronta.",
        severity: item.severity === "blocker" ? "blocker" : "warning",
      });
    });

  audit?.findings
    .filter((finding) => finding.severity === "blocker" || finding.severity === "warning")
    .forEach((finding) => {
      items.push({
        id: `audit-${finding.id}`,
        source: `Auditoria · ${finding.category}`,
        title: finding.title,
        detail: finding.detail,
        action: finding.safe_action,
        severity: finding.severity,
      });
    });

  return items;
}

function alertCenterIcon(severity: AlertCenterItem["severity"]): LucideIcon {
  const icons: Record<AlertCenterItem["severity"], LucideIcon> = {
    blocker: AlertTriangle,
    warning: AlertTriangle,
    info: Bell,
  };
  return icons[severity];
}

async function readApiError(response: Response): Promise<string> {
  const fallback = `HTTP ${response.status}${response.statusText ? ` ${response.statusText}` : ""}`;
  const text = await response.text();
  if (!text.trim()) {
    return fallback;
  }
  try {
    const payload = JSON.parse(text) as { detail?: unknown };
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }
    if (payload.detail && typeof payload.detail !== "string") {
      return JSON.stringify(payload.detail);
    }
  } catch {
    return text;
  }
  return fallback;
}

function delay(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function moonrakerWebsocketUrl(moonrakerUrl: string): string | null {
  try {
    const url = new URL(moonrakerUrl);
    url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
    url.pathname = "/websocket";
    url.search = "";
    url.hash = "";
    return url.toString();
  } catch {
    return null;
  }
}

function parseMoonrakerUpdateMessage(rawData: string): { message: string; complete: boolean } | null {
  try {
    const payload = JSON.parse(rawData) as {
      method?: string;
      params?: Array<{
        application?: string;
        message?: string;
        complete?: boolean;
      }>;
    };
    if (payload.method !== "notify_update_response") {
      return null;
    }
    const response = payload.params?.[0];
    if (!response?.message) {
      return null;
    }
    const application = response.application ? `${response.application}: ` : "";
    return {
      message: `${application}${response.message}`,
      complete: Boolean(response.complete),
    };
  } catch {
    return null;
  }
}

function formatUpdatePhase(phase: UpdateDialogState["phase"]) {
  const labels: Record<UpdateDialogState["phase"], string> = {
    confirm: "Aguardando confirmação",
    running: "Update em andamento",
    done: "Update concluído",
    failed: "Update com erro",
  };
  return labels[phase];
}

function updatePhaseIcon(phase: UpdateDialogState["phase"]): LucideIcon {
  const icons: Record<UpdateDialogState["phase"], LucideIcon> = {
    confirm: AlertTriangle,
    running: RefreshCw,
    done: CheckCircle2,
    failed: AlertTriangle,
  };
  return icons[phase];
}

function updateStatusIcon(status: UpdateComponent["status"]): LucideIcon {
  const icons: Record<UpdateComponent["status"], LucideIcon> = {
    up_to_date: CheckCircle2,
    update_available: RefreshCw,
    warning: AlertTriangle,
    busy: Gauge,
    unknown: Gauge,
  };
  return icons[status];
}

function formatBoolean(value: boolean | null | undefined) {
  if (typeof value !== "boolean") {
    return "-";
  }
  return value ? "sim" : "não";
}

function formatConnectionType(connectionType: BoardPreset["connection_type"]) {
  const labels: Record<BoardPreset["connection_type"], string> = {
    usb: "USB",
    can: "CAN",
    usb_can_bridge: "USB-CAN bridge",
  };
  return labels[connectionType];
}

function formatCalibrationCategory(category: string) {
  const labels: Record<string, string> = {
    extrusao_base: "extrusão base",
    validacao_mecanica: "validação mecânica",
    nivelamento: "nivelamento",
    probe: "probe",
    primeira_camada: "primeira camada",
    material: "material",
    extrusao: "extrusão",
    movimento: "movimento",
    qualidade: "qualidade",
    temperatura: "temperatura",
    perifericos: "periféricos",
    dimensional: "dimensional",
  };
  return labels[category] ?? category;
}

function formatExecutionMode(mode: CalibrationTestRecord["execution_mode"]) {
  const labels: Record<CalibrationTestRecord["execution_mode"], string> = {
    read_only: "somente leitura",
    manual: "manual",
    gcode_review_required: "G-code exige revisão",
    blocked_while_printing: "bloqueado imprimindo",
  };
  return labels[mode];
}

function formatRiskLevel(riskLevel: CalibrationTestRecord["risk_level"]) {
  const labels: Record<CalibrationTestRecord["risk_level"], string> = {
    low: "baixo",
    medium: "médio",
    high: "alto",
  };
  return labels[riskLevel];
}

function formatCalibrationResult(resultStatus: CalibrationRunRecord["result_status"]) {
  const labels: Record<CalibrationRunRecord["result_status"], string> = {
    passed: "aprovado",
    warning: "atenção",
    failed: "falhou",
    skipped: "ignorado",
  };
  return labels[resultStatus];
}

function formatCalibrationExecutionStatus(status: string) {
  const labels: Record<string, string> = {
    executed: "executado",
    blocked: "bloqueado",
    failed: "falhou",
    failed_partial: "falhou parcialmente",
  };
  return labels[status] ?? status;
}

function calibrationExecutionRowClass(status: string) {
  if (status === "executed") {
    return "passed";
  }
  if (status === "failed" || status === "failed_partial") {
    return "failed";
  }
  return "warning";
}

function summarizeCalibrationExecutionFinalState(execution: CalibrationExecutionRecord) {
  const finalState = latestCalibrationExecutionFinalState(execution);
  if (!finalState) {
    return `${execution.sent_commands.length}/${execution.commands.length} comando(s) confirmado(s)`;
  }
  const klipper = typeof finalState.klipper_state === "string" ? finalState.klipper_state : "-";
  const klippy = typeof finalState.klippy_state === "string" ? finalState.klippy_state : "-";
  const printState = typeof finalState.print_state === "string" && finalState.print_state ? finalState.print_state : "-";
  const homedAxes = typeof finalState.homed_axes === "string" && finalState.homed_axes ? ` · homed ${finalState.homed_axes}` : "";
  return `Final: Klipper ${klipper} · Klippy ${klippy} · print ${printState}${homedAxes}`;
}

function formatCalibrationExecutionResult(execution: CalibrationExecutionRecord) {
  return JSON.stringify(execution.result, null, 2);
}

function buildCalibrationExecutionNotes(execution: CalibrationExecutionRecord) {
  const commandText = execution.sent_commands.length ? execution.sent_commands.join(", ") : "-";
  return [
    execution.message,
    summarizeCalibrationExecutionFinalState(execution),
    `Comandos confirmados: ${commandText}`,
    "Retorno final Moonraker:",
    formatCalibrationExecutionResult(execution),
  ].filter(Boolean).join("\n");
}

function latestCalibrationExecutionFinalState(execution: CalibrationExecutionRecord) {
  for (let index = execution.result.length - 1; index >= 0; index -= 1) {
    const item = execution.result[index];
    const finalState = item.final_state;
    if (finalState && typeof finalState === "object" && !Array.isArray(finalState)) {
      return finalState as Record<string, unknown>;
    }
  }
  return null;
}

function formatCalibrationTestTitle(testKey: string, tests: CalibrationTestRecord[]) {
  return tests.find((test) => test.test_key === testKey)?.title ?? testKey;
}

function formatCalibrationSequenceStatus(status: CalibrationSequencePlan["steps"][number]["status"]) {
  if (status === "completed") {
    return "concluído";
  }
  if (status === "skipped") {
    return "pulado";
  }
  return "pendente";
}

function groupCalibrationSteps(steps: CalibrationSequencePlan["steps"]) {
  const groups = new Map<string, CalibrationSequencePlan["steps"]>();
  steps.forEach((step) => {
    const current = groups.get(step.phase) ?? [];
    current.push(step);
    groups.set(step.phase, current);
  });
  return Array.from(groups.entries()).map(([phase, phaseSteps]) => ({
    phase,
    steps: phaseSteps,
    completed: phaseSteps.filter((step) => step.status === "completed").length,
  }));
}

function formatCalibrationPhase(phase: string) {
  const labels: Record<string, string> = {
    "01_base_mecanica": "1. Base mecânica",
    "02_temperatura": "2. Temperatura",
    "03_extrusao_base": "3. Extrusão base",
    "04_probe_mesa": "4. Probe e mesa",
    "05_primeira_camada": "5. Primeira camada",
    "06_material": "6. Material e fluxo",
    "07_movimento": "7. Movimento e vibração",
    "08_acabamento": "8. Acabamento",
    "09_dimensional": "9. Dimensional",
    "10_perifericos": "10. Periféricos",
  };
  return labels[phase] ?? phase.replace(/^[0-9]+_/, "").replaceAll("_", " ");
}

function getCalibrationResultFormConfig(test: CalibrationTestRecord): CalibrationResultFormConfig {
  const base: CalibrationResultFormConfig = {
    summary: "Registre o que foi verificado neste item. O histórico serve para liberar a próxima revisão com evidência local.",
    observedLabel: "Resultado objetivo",
    observedPlaceholder: "Ex.: aprovado sem folgas, range 0.012 mm, temperatura estável",
    notesLabel: "Evidência e observações",
    notesPlaceholder: "O que foi visto, corrigido, medido ou precisa ser revisado depois",
    showMaterial: false,
    showPlate: false,
    showNozzle: false,
  };
  if (test.test_key === "mechanical_preflight" || test.category === "validacao_mecanica") {
    return {
      ...base,
      summary: "Use este registro para confirmar a inspeção física antes de ajustes por software.",
      observedLabel: "Resumo da inspeção",
      observedPlaceholder: "Ex.: correias firmes, toolhead sem folga, cabos livres",
      notesLabel: "Problemas encontrados ou correções feitas",
      notesPlaceholder: "Ex.: reapertado parafuso X, cabo do toolhead reposicionado, sem ação necessária",
    };
  }
  if (test.category === "temperatura") {
    return {
      ...base,
      observedLabel: "Temperatura e estabilidade",
      observedPlaceholder: "Ex.: 220 °C estável, overshoot baixo, mesa estabilizou em 60 °C",
      notesLabel: "Condição do teste",
      notesPlaceholder: "Material usado, tempo de estabilização, oscilação observada ou erro do Klipper",
      showMaterial: true,
    };
  }
  if (test.category === "primeira_camada") {
    return {
      ...base,
      summary: "Este resultado deve refletir o teste real de primeira camada. Use o perfil aprovado abaixo só quando este teste estiver bom.",
      observedLabel: "Z-offset/resultado visual",
      observedPlaceholder: "Ex.: -0.295, linhas aderidas sem raspar",
      notesLabel: "Aderência e aparência",
      notesPlaceholder: "Uniformidade, cantos, excesso de esmagamento, limpeza da mesa e ajuste usado",
      showMaterial: true,
      showPlate: true,
      showNozzle: true,
    };
  }
  if (test.category === "material" || test.category === "extrusao" || test.category === "extrusao_base") {
    return {
      ...base,
      observedLabel: "Valor medido ou escolhido",
      observedPlaceholder: "Ex.: flow 0.96, PA 0.035, 18 mm3/s, extrusão real 49.6 mm",
      notesLabel: "Material, perfil e evidência",
      notesPlaceholder: "Marca/cor do filamento, perfil do slicer, peça usada, falhas ou aprovação visual",
      showMaterial: true,
      showPlate: test.category === "material",
      showNozzle: true,
    };
  }
  if (test.category === "probe" || test.category === "nivelamento") {
    return {
      ...base,
      observedLabel: "Medição ou conclusão",
      observedPlaceholder: "Ex.: probe repetível, QGL dentro da tolerância, offset XY conferido",
      notesLabel: "Condição da mesa/probe",
      notesPlaceholder: "Estado da chapa, bico limpo, range, retries, ajuste manual ou bloqueio encontrado",
      showPlate: true,
      showNozzle: true,
    };
  }
  if (test.category === "movimento" || test.category === "qualidade" || test.category === "dimensional") {
    return {
      ...base,
      observedLabel: "Medição ou artefato observado",
      observedPlaceholder: "Ex.: sem ringing visível, X 20.02 mm, sem layer shift",
      notesLabel: "Peça de teste e interpretação",
      notesPlaceholder: "Velocidade, aceleração, medidas, foto/referência e próximos ajustes",
      showMaterial: true,
      showNozzle: true,
    };
  }
  return base;
}

function confirmedWizardSteps(checks: Record<string, boolean>) {
  return Object.values(checks).filter(Boolean).length;
}

function formatDecision(decision: HealthResponse["decision"] | undefined) {
  if (decision === "ok_para_imprimir") {
    return "OK";
  }
  if (decision === "monitorar") {
    return "Monitorar";
  }
  if (decision === "nao_imprimir") {
    return "Não imprimir";
  }
  return "-";
}

function healthPanelClass(decision: HealthResponse["decision"] | undefined) {
  if (decision === "ok_para_imprimir") {
    return "ok";
  }
  if (decision === "nao_imprimir") {
    return "danger";
  }
  return "warn";
}

function overviewRiskClass(decision: HealthResponse["decision"] | undefined) {
  if (decision === "ok_para_imprimir") {
    return "ok";
  }
  if (decision === "nao_imprimir") {
    return "danger";
  }
  if (decision === "monitorar") {
    return "warn";
  }
  return "unknown";
}

function healthFindingClass(severity: HealthItem["severity"]) {
  if (severity === "blocker") {
    return "blocker";
  }
  if (severity === "warning") {
    return "warning";
  }
  return "info";
}

function checklistDotClass(item: ChecklistItem) {
  if (item.ok) {
    return "dot good";
  }
  if (item.severity === "manual" || item.status === "manual") {
    return "dot manual";
  }
  return "dot bad";
}

function formatChecklistDataState(dataState: string) {
  if (dataState === "live") {
    return "ao vivo";
  }
  if (dataState === "last_snapshot") {
    return "último snapshot";
  }
  if (dataState === "offline") {
    return "offline";
  }
  if (dataState === "no_data") {
    return "sem dados";
  }
  return dataState;
}

function buildTemperatureSeries(history: OperationTemperatureHistoryRow[]) {
  const series = new Map<
    string,
    Array<{ snapshotId: number | null; createdAt: string; temperature: number }>
  >();
  history.forEach((row) => {
    row.readings.forEach((reading) => {
      if (typeof reading.temperature !== "number") {
        return;
      }
      const points = series.get(reading.name) ?? [];
      points.push({ snapshotId: row.snapshot_id, createdAt: row.created_at, temperature: reading.temperature });
      series.set(reading.name, points);
    });
  });
  return Array.from(series.entries()).map(([name, points]) => {
    const temperatures = points.map((point) => point.temperature);
    return {
      name,
      points,
      min: Math.min(...temperatures),
      max: Math.max(...temperatures),
    };
  });
}

function temperatureBarHeight(value: number, min: number, max: number) {
  if (max === min) {
    return 55;
  }
  return Math.max(18, Math.round(((value - min) / (max - min)) * 82) + 18);
}

function operationActionParameterSpecs(actionId: string): OperationActionParameterSpec[] {
  const specs: Record<string, OperationActionParameterSpec[]> = {
    move_xy: [
      { name: "axis", type: "enum", values: ["X", "Y"], default: "X" },
      { name: "distance_mm", type: "number", default: 10, min: -50, max: 50 },
      { name: "feedrate", type: "number", default: 6000, min: 600, max: 12000 },
    ],
    move_z: [
      { name: "distance_mm", type: "number", default: 5, min: -10, max: 10 },
      { name: "feedrate", type: "number", default: 1200, min: 120, max: 3000 },
    ],
    extrude: [
      { name: "length_mm", type: "number", default: 5, min: -10, max: 50 },
      { name: "feedrate", type: "number", default: 300, min: 60, max: 1200 },
    ],
    set_hotend_temp: [{ name: "temperature", type: "number", default: 0, min: 0, max: 300 }],
    set_bed_temp: [{ name: "temperature", type: "number", default: 0, min: 0, max: 130 }],
    set_fan: [{ name: "speed_percent", type: "number", default: 0, min: 0, max: 100 }],
    set_led: [
      { name: "led_name", type: "text", default: "" },
      { name: "brightness_percent", type: "number", default: 0, min: 0, max: 100 },
    ],
  };
  return specs[actionId] ?? [];
}

function buildOperationActionPayload(values: Record<string, string>) {
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => {
      const numericValue = Number(value);
      return [key, value.trim() !== "" && Number.isFinite(numericValue) ? numericValue : value];
    }),
  );
}

function formatOperationParameterLabel(name: string) {
  const labels: Record<string, string> = {
    axis: "Eixo",
    distance_mm: "Distância mm",
    feedrate: "Feedrate",
    length_mm: "Comprimento mm",
    temperature: "Temperatura",
    speed_percent: "Velocidade %",
    led_name: "Nome do LED",
    brightness_percent: "Brilho %",
  };
  return labels[name] ?? name;
}

function formatOperationActionId(actionId: string) {
  return actionId.replaceAll("_", " ");
}

function formatOperationCapabilityStatus(status: OperationCapability["status"]) {
  if (status === "supported") {
    return "suportado";
  }
  if (status === "blocked") {
    return "bloqueado";
  }
  return "desconhecido";
}

function formatRollbackPlan(plan: string | string[]) {
  return Array.isArray(plan) ? plan.join(" · ") : plan;
}

function formatOperationDataState(dataState: OperationStatusResponse["data_state"] | undefined) {
  if (dataState === "live") {
    return "ao vivo";
  }
  if (dataState === "offline") {
    return "offline";
  }
  if (dataState === "fixture") {
    return "fixture";
  }
  if (dataState === "last_snapshot") {
    return "snapshot";
  }
  return "-";
}

function formatOperationValue(value: unknown, unit?: string | null) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }
  const normalized = typeof value === "number" ? Number(value.toFixed(2)).toString() : formatUnknown(value);
  return unit && unit !== "bytes" ? `${normalized} ${unit}` : normalized;
}

function formatTemperature(value: unknown) {
  if (typeof value !== "number") {
    return "-";
  }
  return `${Number(value.toFixed(1))} °C`;
}

function formatPercent(value: unknown) {
  if (typeof value !== "number") {
    return "-";
  }
  return `${Math.round(value * 100)}%`;
}

function formatPosition(value: unknown) {
  if (!Array.isArray(value)) {
    return "-";
  }
  return value
    .slice(0, 3)
    .map((axis) => (typeof axis === "number" ? Number(axis.toFixed(2)) : axis))
    .join(" / ");
}

function formatUnknown(value: unknown): string {
  if (value === null || value === undefined) {
    return "-";
  }
  if (typeof value === "string") {
    return value || "-";
  }
  return JSON.stringify(value) ?? "-";
}

createRoot(document.getElementById("root")!).render(<App />);
