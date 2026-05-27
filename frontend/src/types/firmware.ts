export type FirmwareBuildConfig = {
  schema_version: number;
  architecture: string;
  mcu: string;
  processor_model: string;
  bootloader_offset: string;
  clock_reference: string;
  communication_interface: string;
  connection_type: "usb" | "can" | "usb_can_bridge";
  canbus_pins?: string | null;
  usb_pins?: string | null;
  serial_pins?: string | null;
  config_file: string;
  build_output: string;
};

export type FirmwareBuildConfigValidation = {
  status: "complete" | "missing_data" | "invalid";
  missing_fields: string[];
  invalid_fields: string[];
};

export type FirmwareConfigPreview = {
  safe_mode: string;
  preset_id: string;
  config_file: string;
  build_output: string;
  build_config_schema_version: number;
  content: string;
  lines: string[];
  artifact_saved: boolean;
  artifact_path?: string | null;
  message: string;
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
  config_file: string;
  build_output: string;
  default_flash_method: "katapult_can" | "katapult_usb_can" | "dfu_usb" | "manual";
  build_config: FirmwareBuildConfig;
  build_config_validation: FirmwareBuildConfigValidation;
  build_config_status: "complete" | "missing_data" | "invalid";
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
  catalog_references: {
    id: string;
    label: string;
    role: "mainboard" | "toolhead" | "can_adapter" | "unknown";
    connection: "can" | "usb" | "usb_can_bridge" | "dedicated_usb_can" | "unknown";
    guide_url: string;
    preset_ids: string[];
    known_mcus: string[];
    flash_method?: "katapult_can" | "katapult_usb_can" | "dfu_usb" | "manual" | "unknown" | null;
    bootloader?: string | null;
    safety_notes: string[];
  }[];
  guide_url?: string | null;
  action_label: string;
  detail: string;
};

export type FirmwareCatalogSummary = {
  safe_mode: string;
  source: {
    name: string;
    url: string;
    retrieved_at: string;
    notes: string[];
  };
  generated_at?: string | null;
  manifest_total_pages: number;
  catalog_counts: Record<string, number>;
  category_counts: Record<string, number>;
  status_counts: Record<string, number>;
  hardware_role_counts: Record<string, number>;
  hardware_without_local_preset: Record<string, string[]>;
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
  catalog_hardware_without_local_preset: Record<string, string[]>;
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
  preset_id?: string | null;
  preset_build_config_status?: "complete" | "missing_data" | "invalid" | null;
  generated_config_path?: string | null;
  work_dir?: string | null;
  expected_build_output?: string | null;
  log_path?: string | null;
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
