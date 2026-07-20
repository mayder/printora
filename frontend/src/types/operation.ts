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

export type OperationPrintSceneSegment = [number, number, number, number, number, number, number?];

export type OperationPrintScene = {
  kind?: string | null;
  units?: string | null;
  bed?: number[] | null;
  printed?: OperationPrintSceneSegment[] | null;
  current?: OperationPrintSceneSegment[] | null;
  future?: OperationPrintSceneSegment[] | null;
  current_layer?: number | null;
  total_layers?: number | null;
  current_layer_z?: number | null;
  printed_segment_count?: number | null;
  current_segment_count?: number | null;
  future_segment_count?: number | null;
  displayed_segment_count?: number | null;
  total_segment_count?: number | null;
  sampled?: boolean | null;
};

export type OperationPrintVisual = {
  data_uri?: string | null;
  width?: number | null;
  height?: number | null;
  source?: string | null;
  projection?: string | null;
  scene?: OperationPrintScene | null;
  current_layer?: number | null;
  total_layers?: number | null;
  truncated?: boolean | null;
};

export type OperationGcodeFile = {
  filename: string;
  path?: string | null;
  name?: string | null;
  directory?: string | null;
  size?: number | null;
  modified?: number | null;
  estimated_time?: number | null;
  slicer?: string | null;
  slicer_version?: string | null;
  object_height?: number | null;
  layer_height?: number | null;
  first_layer_height?: number | null;
  layer_count?: number | null;
  nozzle_diameter?: number | null;
  filament_total?: number | null;
  filament_weight_total?: number | null;
  filament_type?: string | null;
  filament_name?: string | null;
  first_layer_bed_temp?: number | null;
  first_layer_extr_temp?: number | null;
  print_start_time?: number | null;
  print_end_time?: number | null;
  last_print_duration?: number | null;
  metadata_available?: boolean | null;
  thumbnail?: OperationPrintVisual | null;
};

export type OperationGcodeDirectory = {
  path: string;
  name: string;
  parent?: string | null;
  file_count: number;
  total_size?: number | null;
  modified?: number | null;
};

export type OperationGcodeStorage = {
  total?: number | null;
  used?: number | null;
  free?: number | null;
};

export type GcodeFilesResponse = {
  printer_id: number;
  safe_mode: string;
  data_state: "live" | "cached" | "offline" | "error" | "unsupported";
  root: string;
  summary: string;
  files: OperationGcodeFile[];
  directories: OperationGcodeDirectory[];
  storage?: OperationGcodeStorage | null;
  fetched_at?: string | null;
  cache_ttl_seconds?: number | null;
  error?: string | null;
  agent?: {
    version?: string | null;
    expected_version?: string | null;
    ready?: boolean | null;
    diagnostic?: string | null;
  } | null;
};

export type GcodeFileActionName =
  | "preview"
  | "download"
  | "copy_path"
  | "history"
  | "print"
  | "rename"
  | "move"
  | "duplicate"
  | "delete";

export type GcodeFileActionState = {
  action: GcodeFileActionName;
  label: string;
  enabled: boolean;
  read_only: boolean;
  destructive: boolean;
  requires_target: boolean;
  requires_confirmation: boolean;
  requires_step_up: boolean;
  confirmation_phrase: string;
  block_reason: string;
  blockers: string[];
};

export type GcodeFileHistoryEntry = {
  id: number;
  created_at?: string | null;
  finished_at?: string | null;
  job_type: string;
  action: string;
  status: string;
  summary: string;
  filename: string;
  target_filename: string;
};

export type GcodeFileDetailResponse = {
  printer_id: number;
  safe_mode: string;
  data_state: "live" | "cached" | "offline" | "error" | "unsupported";
  summary: string;
  file: OperationGcodeFile;
  actions: GcodeFileActionState[];
  history: GcodeFileHistoryEntry[];
  current_print: {
    connected?: boolean | null;
    printing?: boolean | null;
    print_state?: string | null;
    filename?: string | null;
    klipper_state?: string | null;
    klippy_state?: string | null;
    error?: string | null;
  };
  preview_available: boolean;
  download_available: boolean;
  agent?: GcodeFilesResponse["agent"];
};

export type GcodeFileActionResponse = {
  printer_id: number;
  safe_mode: string;
  action: GcodeFileActionName;
  status: "ready" | "blocked" | "executed" | "failed";
  filename: string;
  target_filename: string;
  confirmation_phrase: string;
  confirmation_matched: boolean;
  blockers: string[];
  summary: string;
  job_id?: number | null;
  result: Record<string, unknown>;
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
  agent?: {
    version?: string | null;
    expected_version?: string | null;
    ready?: boolean | null;
    diagnostic?: string | null;
  };
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
    collection_state?: "loaded" | "objects_detected_without_status" | "objects_not_reported" | "none_detected" | string | null;
    detected_objects?: string[];
    missing_status_objects?: string[];
    progress?: number | null;
    progress_source?: string | null;
    file_progress?: number | null;
    file_position?: number | null;
    message?: string | null;
    print_state?: string | null;
    filename?: string | null;
    print_duration?: number | null;
    total_duration?: number | null;
    estimated_time?: number | null;
    remaining_time?: number | null;
    current_layer?: number | null;
    total_layers?: number | null;
    layer_source?: string | null;
    thumbnail?: OperationPrintVisual | null;
    layer_preview?: OperationPrintVisual | null;
    total_print_hours?: number | null;
    slicer?: string | null;
    slicer_version?: string | null;
    filament_total?: number | null;
    filament_weight_total?: number | null;
    object_height?: number | null;
    layer_height?: number | null;
    first_layer_height?: number | null;
    nozzle_diameter?: number | null;
    filament_type?: string | null;
    filament_name?: string | null;
    gcode_files?: OperationGcodeFile[];
  };
};
