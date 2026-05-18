import React from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  AlertTriangle,
  Bell,
  Camera,
  CheckCircle2,
  Database,
  FileText,
  Gauge,
  Home,
  ListChecks,
  Plus,
  Printer,
  Radio,
  RefreshCw,
  Search,
  Server,
  Settings,
  ShieldCheck,
  SlidersHorizontal,
  Wrench,
  Zap,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import "./styles.css";

type ChecklistItem = {
  key: string;
  title: string;
  ok: boolean;
  severity: string;
  detail: string;
};

type ChecklistResponse = {
  can_print: boolean;
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

type PrinterRecord = {
  id: number;
  name: string;
  moonraker_url: string;
  host_audit_mode: "disabled" | "local" | "ssh";
  host_audit_ssh_target?: string | null;
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
  printer_id: number;
  moonraker_url: string;
  decision: "ok_para_imprimir" | "monitorar" | "nao_imprimir";
  summary: string;
  metrics: Record<string, unknown>;
  counts: Record<string, number>;
  items: HealthItem[];
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

type SanitizedReport = {
  printer_id: number;
  safe_mode: string;
  format: "markdown";
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
};

type MaintenanceTaskRecord = {
  id: number;
  printer_id: number;
  name: string;
  component: string;
  interval_days: number;
  last_done_at?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  due_status: "due" | "ok" | "unknown";
  days_until_due?: number | null;
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
  notes: string;
  created_at: string;
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
};

type PluginAuditResponse = {
  printer_id: number;
  safe_mode: string;
  source: string;
  summary: string;
  items: PluginAuditItem[];
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

type AppSection =
  | "overview"
  | "printers"
  | "monitoring"
  | "calibration"
  | "tests"
  | "firmware"
  | "maintenance"
  | "reports"
  | "settings";

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
    key: "monitoring",
    icon: Activity,
    label: "Monitoramento",
    detail: "Health, logs, CAN, Moonraker, Klipper e host.",
    purpose: "Analise saúde, logs e sinais técnicos antes de imprimir, atualizar ou diagnosticar falhas.",
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
    purpose: "Consulte testes, critérios de sucesso e registre resultados sem executar G-code automaticamente.",
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
    purpose: "Centralize ajustes do app, seleção de impressora e integrações futuras.",
  },
];

const navGroups: Array<{ title: string; sections: AppSection[] }> = [
  { title: "Principal", sections: ["overview", "printers"] },
  { title: "Impressora ativa", sections: ["monitoring", "calibration", "tests", "firmware", "maintenance"] },
  { title: "Diagnóstico", sections: ["reports", "settings"] },
];

function App() {
  const [printers, setPrinters] = React.useState<PrinterRecord[]>([]);
  const [selectedPrinterId, setSelectedPrinterId] = React.useState<number | null>(null);
  const [activeSection, setActiveSection] = React.useState<AppSection>("overview");
  const [discovery, setDiscovery] = React.useState<PrinterDiscoveryResponse | null>(null);
  const [printerModalOpen, setPrinterModalOpen] = React.useState(false);
  const [newPrinterName, setNewPrinterName] = React.useState("Voron - Mayder");
  const [newPrinterUrl, setNewPrinterUrl] = React.useState("http://voron.local:7125");
  const [snapshots, setSnapshots] = React.useState<SnapshotRecord[]>([]);
  const [fromSnapshotId, setFromSnapshotId] = React.useState<number | null>(null);
  const [toSnapshotId, setToSnapshotId] = React.useState<number | null>(null);
  const [snapshotDiff, setSnapshotDiff] = React.useState<SnapshotDiff | null>(null);
  const [status, setStatus] = React.useState<MoonrakerStatus | null>(null);
  const [health, setHealth] = React.useState<HealthResponse | null>(null);
  const [checklist, setChecklist] = React.useState<ChecklistResponse | null>(null);
  const [audit, setAudit] = React.useState<AuditResponse | null>(null);
  const [hostAudit, setHostAudit] = React.useState<AuditResponse | null>(null);
  const [backupPolicies, setBackupPolicies] = React.useState<BackupPolicyRecord[]>([]);
  const [backupRuns, setBackupRuns] = React.useState<BackupRunRecord[]>([]);
  const [sanitizedReport, setSanitizedReport] = React.useState<SanitizedReport | null>(null);
  const [maintenanceEvents, setMaintenanceEvents] = React.useState<MaintenanceEventRecord[]>([]);
  const [maintenanceTasks, setMaintenanceTasks] = React.useState<MaintenanceTaskRecord[]>([]);
  const [zOffsetRecords, setZOffsetRecords] = React.useState<ZOffsetRecord[]>([]);
  const [canRecords, setCanRecords] = React.useState<CanBusRecord[]>([]);
  const [pluginAudit, setPluginAudit] = React.useState<PluginAuditResponse | null>(null);
  const [boardPresets, setBoardPresets] = React.useState<BoardPreset[]>([]);
  const [firmwareBoards, setFirmwareBoards] = React.useState<FirmwareBoardRecord[]>([]);
  const [firmwareBuildRuns, setFirmwareBuildRuns] = React.useState<FirmwareBuildRunRecord[]>([]);
  const [firmwareFlashRuns, setFirmwareFlashRuns] = React.useState<FirmwareFlashRunRecord[]>([]);
  const [calibrationTests, setCalibrationTests] = React.useState<CalibrationTestRecord[]>([]);
  const [calibrationRuns, setCalibrationRuns] = React.useState<CalibrationRunRecord[]>([]);
  const [zOffsetWizardPlan, setZOffsetWizardPlan] = React.useState<ZOffsetWizardPlan | null>(null);
  const [zOffsetWizardChecks, setZOffsetWizardChecks] = React.useState<Record<string, boolean>>({});
  const [maintenanceEventType, setMaintenanceEventType] =
    React.useState<MaintenanceEventRecord["event_type"]>("maintenance");
  const [maintenanceComponent, setMaintenanceComponent] = React.useState("motion");
  const [maintenanceTitle, setMaintenanceTitle] = React.useState("Lubrificação / inspeção");
  const [maintenanceNotes, setMaintenanceNotes] = React.useState("");
  const [maintenanceTaskName, setMaintenanceTaskName] = React.useState("Limpar mesa");
  const [maintenanceTaskComponent, setMaintenanceTaskComponent] = React.useState("bed");
  const [maintenanceTaskIntervalDays, setMaintenanceTaskIntervalDays] = React.useState(30);
  const [zOffsetPlateName, setZOffsetPlateName] = React.useState("Texturizada");
  const [zOffsetMaterial, setZOffsetMaterial] = React.useState("PLA");
  const [zOffsetNozzle, setZOffsetNozzle] = React.useState("T0");
  const [zOffsetValue, setZOffsetValue] = React.useState(-0.295);
  const [zOffsetNotes, setZOffsetNotes] = React.useState("");
  const [canInterfaceName, setCanInterfaceName] = React.useState("can0");
  const [canRxError, setCanRxError] = React.useState(0);
  const [canTxError, setCanTxError] = React.useState(0);
  const [canTxRetries, setCanTxRetries] = React.useState(0);
  const [canBusState, setCanBusState] = React.useState("ERROR-ACTIVE");
  const [canBitrate, setCanBitrate] = React.useState(1000000);
  const [canNotes, setCanNotes] = React.useState("");
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
  const [calibrationTestKey, setCalibrationTestKey] = React.useState("probe_accuracy_center");
  const [calibrationResultStatus, setCalibrationResultStatus] =
    React.useState<CalibrationRunRecord["result_status"]>("passed");
  const [calibrationMaterial, setCalibrationMaterial] = React.useState("PLA");
  const [calibrationPlateName, setCalibrationPlateName] = React.useState("Texturizada");
  const [calibrationNozzle, setCalibrationNozzle] = React.useState("T0");
  const [calibrationObservedValue, setCalibrationObservedValue] = React.useState("");
  const [calibrationNotes, setCalibrationNotes] = React.useState("");
  const [calibrationGcodeReviewed, setCalibrationGcodeReviewed] = React.useState(false);
  const [backupName, setBackupName] = React.useState("Config backup");
  const [backupSourcePath, setBackupSourcePath] = React.useState("/home/pi/printer_data/config");
  const [backupDestinationPath, setBackupDestinationPath] = React.useState(
    "/home/pi/printer_data/backups/mayderprintlab",
  );
  const [backupDryRunOnly, setBackupDryRunOnly] = React.useState(true);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function loadStatus() {
    setLoading(true);
    setError(null);
    try {
      const statusResponse = await fetch("/api/moonraker/status");
      const statusPayload = (await statusResponse.json()) as MoonrakerStatus;
      setStatus(statusPayload);

      const checklistResponse = await fetch("/api/checklist/post-update");
      if (checklistResponse.ok) {
        setChecklist((await checklistResponse.json()) as ChecklistResponse);
      }

      const auditResponse = await fetch("/api/audit/read-only");
      if (auditResponse.ok) {
        setAudit((await auditResponse.json()) as AuditResponse);
      }

      const hostAuditResponse = await fetch("/api/audit/host-read-only");
      if (hostAuditResponse.ok) {
        setHostAudit((await hostAuditResponse.json()) as AuditResponse);
      }

      await loadBoardPresets();
      await loadCalibrationTests();
      await loadPrinters();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
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
    await loadSnapshots(printerId);
    await loadPrinterHealth(printerId);
    await loadBackups(printerId);
    await loadMaintenance(printerId);
    await loadZOffsets(printerId);
    await loadCanRecords(printerId);
    await loadPluginAudit(printerId);
    await loadFirmwareBoards(printerId);
    await loadFirmwareBuildRuns(printerId);
    await loadFirmwareFlashRuns(printerId);
    await loadCalibrationRuns(printerId);
  }

  function selectPrinter(printerId: number) {
    setSelectedPrinterId(printerId);
    setSanitizedReport(null);
    void loadPrinterContext(printerId);
  }

  async function createPrinter(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/printers", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newPrinterName,
          moonraker_url: newPrinterUrl,
          host_audit_mode: "disabled",
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const created = (await response.json()) as PrinterRecord;
      await loadPrinters();
      setSelectedPrinterId(created.id);
      await loadPrinterContext(created.id);
      setPrinterModalOpen(false);
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

  function useDiscoveredPrinter(candidate: DiscoveredPrinter) {
    setNewPrinterName(candidate.name);
    setNewPrinterUrl(candidate.moonraker_url);
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
      await loadPrinterHealth(selectedPrinterId);
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

  async function loadMaintenance(printerId: number) {
    const [eventsResponse, tasksResponse] = await Promise.all([
      fetch(`/api/printers/${printerId}/maintenance/events`),
      fetch(`/api/printers/${printerId}/maintenance/tasks`),
    ]);
    if (eventsResponse.ok) {
      const payload = (await eventsResponse.json()) as { events: MaintenanceEventRecord[] };
      setMaintenanceEvents(payload.events);
    }
    if (tasksResponse.ok) {
      const payload = (await tasksResponse.json()) as { tasks: MaintenanceTaskRecord[] };
      setMaintenanceTasks(payload.tasks);
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
    const response = await fetch(`/api/printers/${printerId}/can/records`);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { records: CanBusRecord[] };
    setCanRecords(payload.records);
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

  async function loadCalibrationTests() {
    const response = await fetch("/api/calibration/tests");
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { tests: CalibrationTestRecord[] };
    setCalibrationTests(payload.tests);
    setCalibrationTestKey((current) => current || payload.tests[0]?.test_key || "");
  }

  async function loadCalibrationRuns(printerId: number) {
    const response = await fetch(`/api/printers/${printerId}/calibration/runs`);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { runs: CalibrationRunRecord[] };
    setCalibrationRuns(payload.runs);
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
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationObservedValue("");
      setCalibrationNotes("");
      setCalibrationGcodeReviewed(false);
      await loadCalibrationRuns(selectedPrinterId);
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
      await loadCanRecords(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createZOffsetRecord(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/z-offsets`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          plate_name: zOffsetPlateName,
          material: zOffsetMaterial,
          nozzle: zOffsetNozzle,
          offset_value: zOffsetValue,
          notes: zOffsetNotes,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setZOffsetNotes("");
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
    setLoading(true);
    setError(null);
    try {
      const query = new URLSearchParams({
        plate_name: zOffsetPlateName,
        material: zOffsetMaterial,
        nozzle: zOffsetNozzle,
        proposed_offset_value: String(zOffsetValue),
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

  async function createMaintenanceEvent(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/maintenance/events`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          event_type: maintenanceEventType,
          component: maintenanceComponent,
          title: maintenanceTitle,
          notes: maintenanceNotes,
        }),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setMaintenanceNotes("");
      await loadMaintenance(selectedPrinterId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setLoading(false);
    }
  }

  async function createMaintenanceTask(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/printers/${selectedPrinterId}/maintenance/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: maintenanceTaskName,
          component: maintenanceTaskComponent,
          interval_days: maintenanceTaskIntervalDays,
        }),
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

  async function completeMaintenanceTask(taskId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/maintenance/tasks/${taskId}/complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: "Concluído pelo painel MayderPrintLab." }),
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

  const activeSectionMeta = appSections.find((section) => section.key === activeSection) ?? appSections[0];
  const selectedPrinter = printers.find((printer) => printer.id === selectedPrinterId);
  const ActiveIcon = activeSectionMeta.icon;
  const alertCount = (health?.counts.blocker ?? 0) + (health?.counts.warning ?? 0);

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Navegação principal">
        <div className="brand">
          <div className="brand-mark">M</div>
          <div>
            <strong>MayderPrintLab</strong>
            <span>Klipper Ops</span>
          </div>
        </div>
        <nav className="sidebar-nav">
          {navGroups.map((group) => (
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
                    onClick={() => setActiveSection(section.key)}
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
          <span>Impressora</span>
          <strong>{selectedPrinter?.name ?? "não selecionada"}</strong>
        </div>
      </aside>

      <div className={`workspace section-${activeSection}`}>
        <header className="topbar">
          <div className="topbar-title">
            <span className="section-icon">
              <ActiveIcon size={22} strokeWidth={2.2} />
            </span>
            <div>
              <h1>{activeSectionMeta.label}</h1>
              <p>{activeSectionMeta.detail}</p>
            </div>
          </div>
          <div className="topbar-actions">
            <label className="context-select">
              Impressora ativa
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
            <span>{selectedPrinter?.moonraker_url ?? "Moonraker não selecionado"}</span>
            <button type="button" className="icon-button" title="Alertas">
              <Bell size={18} />
              {alertCount > 0 ? <strong>{alertCount}</strong> : null}
            </button>
            <button type="button" className="icon-button" title="Configurar impressoras" onClick={() => setPrinterModalOpen(true)}>
              <Settings size={18} />
            </button>
            <button type="button" className="primary-button" onClick={() => void loadStatus()} disabled={loading}>
              <RefreshCw size={16} />
              {loading ? "Atualizando" : "Atualizar"}
            </button>
          </div>
        </header>

        <section className="page-helper">
          <strong>{activeSectionMeta.purpose}</strong>
          <span>{selectedPrinter ? `Contexto atual: ${selectedPrinter.name}` : "Selecione uma impressora para carregar os dados por contexto."}</span>
        </section>

        {error ? <section className="alert danger">{error}</section> : null}

        {printerModalOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Cadastrar impressora">
            <div className="modal-card">
              <div className="modal-header">
                <div>
                  <h2>Cadastrar impressora</h2>
                  <p>Detecte Moonraker na rede local ou informe os dados manualmente.</p>
                </div>
                <button type="button" className="ghost-button" onClick={() => setPrinterModalOpen(false)}>
                  Fechar
                </button>
              </div>
              <div className="modal-actions">
                <button type="button" className="secondary-button" onClick={() => void discoverPrinters()} disabled={loading}>
                  <Search size={16} />
                  Buscar na rede
                </button>
                <span>Leitura segura: HTTP GET em `/server/info`, sem G-code e sem cadastro automático.</span>
              </div>
              {discovery ? (
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
              <form className="modal-form" onSubmit={(event) => void createPrinter(event)}>
                <input
                  aria-label="Nome da impressora"
                  value={newPrinterName}
                  onChange={(event) => setNewPrinterName(event.target.value)}
                  placeholder="Nome da impressora"
                />
                <input
                  aria-label="URL Moonraker"
                  value={newPrinterUrl}
                  onChange={(event) => setNewPrinterUrl(event.target.value)}
                  placeholder="http://printer.local:7125"
                />
                <button type="submit" className="primary-button" disabled={loading}>
                  <Plus size={16} />
                  Cadastrar impressora
                </button>
              </form>
            </div>
          </div>
        ) : null}

        <section className="grid">
        <article className="panel wide panel-section panel-overview panel-printers panel-settings">
          <div className="panel-heading">
            <div>
              <h2>Dashboard de impressoras</h2>
              <p className="muted">Visão rápida das impressoras cadastradas e do contexto ativo do sistema.</p>
            </div>
            <button type="button" className="primary-button" onClick={() => setPrinterModalOpen(true)}>
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
                  <Metric label="Klipper" value={printer.id === selectedPrinterId ? health?.metrics.klipper_state ? String(health.metrics.klipper_state) : "-" : "-"} />
                  <Metric label="Moonraker" value={printer.id === selectedPrinterId ? health?.metrics.moonraker_version ? String(health.metrics.moonraker_version) : "-" : "-"} />
                  <Metric label="Local" value={printer.location ?? "-"} />
                </div>
                <div className="printer-card-actions">
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

        <article className={`panel wide health ${healthPanelClass(health?.decision)} panel-section panel-overview panel-monitoring`}>
          <div className="panel-heading">
            <h2>Health Check</h2>
            <strong>{health?.summary ?? "Aguardando dados"}</strong>
          </div>
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

        <article className="panel wide panel-section panel-monitoring">
          <div className="panel-heading">
            <h2>Monitor CAN</h2>
            <strong>{formatLatestCan(canRecords[0])}</strong>
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
                </div>
                <p>{item.risk}</p>
                <small>{item.recommendation}</small>
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
            {firmwareBoards.length === 0 ? <p className="muted">Nenhuma placa cadastrada.</p> : null}
            {firmwareBoards.map((board) => (
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
                  <button type="button" onClick={() => void createFirmwareBuildDryRun(board.id)} disabled={loading}>
                    Dry-run build
                  </button>
                  <button type="button" onClick={() => void createFirmwareFlashDryRun(board.id)} disabled={loading}>
                    Dry-run flash
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
          </div>
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
            <h2>Calibração e testes</h2>
            <strong>{calibrationTests.length} itens catalogados</strong>
          </div>
          <p className="muted">
            Catálogo seguro: esta área apenas lista testes, pré-condições, critérios e G-code para revisão. Nada é enviado
            para a impressora.
          </p>
          <form className="calibration-run-form" onSubmit={(event) => void createCalibrationRun(event)}>
            <select
              aria-label="Teste de calibração"
              value={calibrationTestKey}
              onChange={(event) => setCalibrationTestKey(event.target.value)}
            >
              {calibrationTests.map((test) => (
                <option key={test.test_key} value={test.test_key}>
                  {test.title}
                </option>
              ))}
            </select>
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
            <input
              aria-label="Material"
              value={calibrationMaterial}
              onChange={(event) => setCalibrationMaterial(event.target.value)}
              placeholder="PLA"
            />
            <input
              aria-label="Chapa"
              value={calibrationPlateName}
              onChange={(event) => setCalibrationPlateName(event.target.value)}
              placeholder="Texturizada"
            />
            <input
              aria-label="Nozzle"
              value={calibrationNozzle}
              onChange={(event) => setCalibrationNozzle(event.target.value)}
              placeholder="T0"
            />
            <input
              aria-label="Valor observado"
              value={calibrationObservedValue}
              onChange={(event) => setCalibrationObservedValue(event.target.value)}
              placeholder="Ex.: range 0.0125"
            />
            <label className="inline-check">
              <input
                type="checkbox"
                checked={calibrationGcodeReviewed}
                onChange={(event) => setCalibrationGcodeReviewed(event.target.checked)}
              />
              G-code revisado
            </label>
            <textarea
              aria-label="Notas da calibração"
              value={calibrationNotes}
              onChange={(event) => setCalibrationNotes(event.target.value)}
              placeholder="Notas, medidas, decisão e próximos ajustes"
            />
            <button type="submit" disabled={!selectedPrinterId || loading || calibrationTests.length === 0}>
              Registrar resultado
            </button>
          </form>
          <div className="calibration-run-list">
            {calibrationRuns.length === 0 ? <p className="muted">Nenhum resultado de calibração registrado.</p> : null}
            {calibrationRuns.slice(0, 8).map((run) => (
              <div key={run.id} className={`calibration-run-row ${run.result_status}`}>
                <strong>
                  {run.test_title} · {formatCalibrationResult(run.result_status)}
                </strong>
                <span>
                  {run.material || "-"} · {run.plate_name || "-"} · {run.nozzle || "-"} · {run.created_at}
                </span>
                <small>
                  Valor: {run.observed_value || "-"} · G-code revisado: {formatBoolean(run.gcode_reviewed)}
                </small>
                {run.notes ? <small>{run.notes}</small> : null}
              </div>
            ))}
          </div>
          <div className="calibration-list">
            {calibrationTests.map((test) => (
              <details key={test.test_key} className={`calibration-row ${test.risk_level}`}>
                <summary>
                  <span>
                    <strong>{test.title}</strong>
                    <small>
                      {formatCalibrationCategory(test.category)} · {formatExecutionMode(test.execution_mode)} · risco{" "}
                      {formatRiskLevel(test.risk_level)}
                    </small>
                  </span>
                  {test.blocked_while_printing ? <em>bloquear imprimindo</em> : null}
                </summary>
                <div className="calibration-detail">
                  <p>{test.objective}</p>
                  <small>Fonte: {test.source}</small>
                  <strong>Pré-condições</strong>
                  <ol>
                    {test.prerequisites.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                  <strong>Critérios de sucesso</strong>
                  <ol>
                    {test.success_criteria.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ol>
                  {test.gcode.length > 0 ? (
                    <>
                      <strong>G-code sugerido para revisão futura</strong>
                      <pre>{test.gcode.join("\n")}</pre>
                    </>
                  ) : null}
                  <small>{test.notes}</small>
                </div>
              </details>
            ))}
          </div>
        </article>

        <article className="panel wide panel-section panel-calibration">
          <div className="panel-heading">
            <h2>Z-offset</h2>
            <strong>{formatLatestZOffset(zOffsetRecords[0])}</strong>
          </div>
          <div className="wizard-actions">
            <button type="button" onClick={() => void evaluateZOffsetWizard()} disabled={!selectedPrinterId || loading}>
              Avaliar wizard
            </button>
            <span>Fluxo manual: o app orienta, mas não envia G-code nem altera config.</span>
          </div>
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
          <form className="z-offset-form" onSubmit={(event) => void createZOffsetRecord(event)}>
            <input
              aria-label="Chapa"
              value={zOffsetPlateName}
              onChange={(event) => setZOffsetPlateName(event.target.value)}
              placeholder="Chapa"
            />
            <input
              aria-label="Material"
              value={zOffsetMaterial}
              onChange={(event) => setZOffsetMaterial(event.target.value)}
              placeholder="Material"
            />
            <input
              aria-label="Nozzle ou toolhead"
              value={zOffsetNozzle}
              onChange={(event) => setZOffsetNozzle(event.target.value)}
              placeholder="T0"
            />
            <input
              aria-label="Valor do Z-offset"
              type="number"
              step="0.001"
              value={zOffsetValue}
              onChange={(event) => setZOffsetValue(Number(event.target.value))}
            />
            <textarea
              aria-label="Notas do Z-offset"
              value={zOffsetNotes}
              onChange={(event) => setZOffsetNotes(event.target.value)}
              placeholder="Ex.: calibrado com papel após limpeza da mesa"
            />
            <button type="submit" disabled={!selectedPrinterId || loading}>
              Registrar
            </button>
          </form>
          <div className="z-offset-list">
            {zOffsetRecords.length === 0 ? <p className="muted">Nenhum Z-offset registrado.</p> : null}
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
          <div className="panel-heading">
            <h2>Manutenção</h2>
            <strong>{maintenanceTasks.filter((task) => task.due_status === "due").length} pendentes</strong>
          </div>
          <div className="maintenance-layout">
            <section>
              <h3>Tarefas preventivas</h3>
              <form className="maintenance-task-form" onSubmit={(event) => void createMaintenanceTask(event)}>
                <input
                  aria-label="Nome da tarefa preventiva"
                  value={maintenanceTaskName}
                  onChange={(event) => setMaintenanceTaskName(event.target.value)}
                  placeholder="Tarefa"
                />
                <input
                  aria-label="Componente da tarefa"
                  value={maintenanceTaskComponent}
                  onChange={(event) => setMaintenanceTaskComponent(event.target.value)}
                  placeholder="Componente"
                />
                <input
                  aria-label="Intervalo em dias"
                  type="number"
                  min="1"
                  max="3650"
                  value={maintenanceTaskIntervalDays}
                  onChange={(event) => setMaintenanceTaskIntervalDays(Number(event.target.value))}
                />
                <button type="submit" disabled={!selectedPrinterId || loading}>
                  Criar
                </button>
              </form>
              <div className="maintenance-list">
                {maintenanceTasks.length === 0 ? <p className="muted">Nenhuma tarefa preventiva cadastrada.</p> : null}
                {maintenanceTasks.map((task) => (
                  <div key={task.id} className={`maintenance-row ${task.due_status}`}>
                    <div>
                      <strong>{task.name}</strong>
                      <span>{task.component} · a cada {task.interval_days} dias</span>
                      <small>
                        Última execução: {task.last_done_at ?? "nunca"} · {formatDueStatus(task)}
                      </small>
                    </div>
                    <button type="button" onClick={() => void completeMaintenanceTask(task.id)} disabled={loading}>
                      Concluir
                    </button>
                  </div>
                ))}
              </div>
            </section>
            <section>
              <h3>Diário</h3>
              <form className="maintenance-event-form" onSubmit={(event) => void createMaintenanceEvent(event)}>
                <select
                  aria-label="Tipo de evento"
                  value={maintenanceEventType}
                  onChange={(event) => setMaintenanceEventType(event.target.value as MaintenanceEventRecord["event_type"])}
                >
                  <option value="maintenance">manutenção</option>
                  <option value="failure">falha</option>
                  <option value="adjustment">ajuste</option>
                  <option value="note">nota</option>
                </select>
                <input
                  aria-label="Componente do evento"
                  value={maintenanceComponent}
                  onChange={(event) => setMaintenanceComponent(event.target.value)}
                  placeholder="Componente"
                />
                <input
                  aria-label="Título do evento"
                  value={maintenanceTitle}
                  onChange={(event) => setMaintenanceTitle(event.target.value)}
                  placeholder="Título"
                />
                <textarea
                  aria-label="Notas do evento"
                  value={maintenanceNotes}
                  onChange={(event) => setMaintenanceNotes(event.target.value)}
                  placeholder="Notas"
                />
                <button type="submit" disabled={!selectedPrinterId || loading}>
                  Registrar
                </button>
              </form>
              <div className="maintenance-list">
                {maintenanceEvents.length === 0 ? <p className="muted">Nenhum evento registrado.</p> : null}
                {maintenanceEvents.map((event) => (
                  <div key={event.id} className="maintenance-event-row">
                    <strong>{event.title}</strong>
                    <span>
                      {formatMaintenanceEventType(event.event_type)} · {event.component ?? "-"} · {event.performed_at}
                    </span>
                    {event.notes ? <small>{event.notes}</small> : null}
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
                <Badge label="Redações" value={sanitizedReport.redactions.length} />
                <Badge label="Impressora" value={sanitizedReport.printer_id} />
              </div>
              <pre className="report-preview">{sanitizedReport.markdown}</pre>
            </>
          ) : null}
        </article>

        <article className="panel wide panel-section panel-maintenance">
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
              placeholder="/home/pi/printer_data/backups/mayderprintlab"
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
          <div className="backup-runs">
            <h3>Histórico</h3>
            {backupRuns.length === 0 ? <p className="muted">Nenhum dry-run registrado.</p> : null}
            {backupRuns.map((run) => (
              <div key={run.id} className="backup-run-row">
                <strong>#{run.id} · {run.status}</strong>
                <span>{run.created_at}</span>
                <small>{run.message}</small>
              </div>
            ))}
          </div>
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

        <article className="panel panel-section panel-monitoring panel-settings">
          <h2>Moonraker</h2>
          <Metric label="Conexão" value={status?.connected ? "Conectado" : "Desconectado"} />
          <Metric label="URL" value={status?.moonraker_url ?? "-"} />
          <Metric label="Klippy" value={status?.server?.klippy_state ?? "-"} />
          <Metric label="Moonraker" value={status?.server?.moonraker_version ?? "-"} />
        </article>

        <article className="panel panel-section panel-monitoring panel-settings">
          <h2>Klipper</h2>
          <Metric label="Estado" value={status?.printer?.state ?? "-"} />
          <Metric label="Mensagem" value={status?.printer?.state_message ?? "-"} />
          <Metric label="Versão" value={status?.printer?.software_version ?? "-"} />
        </article>

        <article className={`panel ${checklist?.can_print ? "ok" : "warn"} panel-section panel-overview panel-monitoring`}>
          <h2>Checklist pós-update</h2>
          <strong className="summary">{checklist?.summary ?? "Aguardando dados"}</strong>
          <div className="checks">
            {checklist?.items.map((item) => (
              <div key={item.key} className="check">
                <span className={item.ok ? "dot good" : "dot bad"} />
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

        <article className="panel wide panel-section panel-monitoring panel-settings">
          <h2>Auditoria do host</h2>
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
        </article>
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
    snapshot_count: "Snapshots",
    latest_snapshot_id: "Último snapshot",
    latest_diff_severity: "Último diff",
  };
  return labels[label] ?? label.replaceAll("_", " ");
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

function formatMaintenanceEventType(eventType: MaintenanceEventRecord["event_type"]) {
  const labels: Record<MaintenanceEventRecord["event_type"], string> = {
    maintenance: "manutenção",
    failure: "falha",
    adjustment: "ajuste",
    note: "nota",
  };
  return labels[eventType];
}

function formatDueStatus(task: MaintenanceTaskRecord) {
  if (task.due_status === "due") {
    return "pendente";
  }
  if (task.due_status === "unknown") {
    return "data inválida";
  }
  return `${task.days_until_due ?? "-"} dias restantes`;
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
    validacao_mecanica: "validação mecânica",
    nivelamento: "nivelamento",
    probe: "probe",
    primeira_camada: "primeira camada",
    extrusao: "extrusão",
    movimento: "movimento",
    qualidade: "qualidade",
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

function healthFindingClass(severity: HealthItem["severity"]) {
  if (severity === "blocker") {
    return "blocker";
  }
  if (severity === "warning") {
    return "warning";
  }
  return "info";
}

function formatUnknown(value: unknown) {
  if (typeof value === "string") {
    return value || "-";
  }
  return JSON.stringify(value);
}

createRoot(document.getElementById("root")!).render(<App />);
