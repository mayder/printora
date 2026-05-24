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
