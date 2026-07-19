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
  object_name?: string | null;
  speed?: number | null;
  rpm?: number | null;
  controllable?: boolean | null;
};

export type OperationOutputPin = {
  name: string;
  object_name?: string | null;
  value?: number | null;
  controllable?: boolean | null;
};

export type OperationLed = {
  name: string;
  object_name?: string | null;
  brightness?: number | null;
  color?: string | null;
  controllable?: boolean | null;
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
    moonraker_response?: Record<string, unknown>;
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
    outputs?: OperationOutputPin[];
    leds?: OperationLed[];
    progress?: number | null;
    progress_source?: string | null;
    message?: string | null;
    print_state?: string | null;
    filename?: string | null;
    print_duration?: number | null;
    total_duration?: number | null;
    current_layer?: number | null;
    total_layers?: number | null;
    total_print_hours?: number | null;
  };
};
