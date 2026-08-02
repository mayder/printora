export type MaterialSource = "local" | "spoolman";
export type MaterialStorageState = "unknown" | "sealed" | "open" | "drying" | "dry";

export interface MaterialAlert {
  code: string;
  severity: "info" | "warning";
  title: string;
  detail: string;
  action: string;
}

export interface MaterialSpool {
  id: number;
  owner_user_id: number;
  material_profile_id: number | null;
  source: MaterialSource;
  external_id: string | null;
  name: string;
  material_type: string;
  brand: string;
  color_name: string;
  color_hex: string | null;
  lot_code: string;
  initial_weight_g: number | null;
  remaining_weight_g: number | null;
  location: string;
  storage_state: MaterialStorageState;
  opened_at: string | null;
  dried_at: string | null;
  expires_at: string | null;
  revision: number;
  status: "active" | "archived";
  last_synced_at: string | null;
  created_at: string;
  updated_at: string;
  alerts: MaterialAlert[];
}

export interface MaterialSpoolPayload {
  material_profile_id?: number | null;
  name: string;
  material_type: string;
  brand?: string;
  color_name?: string;
  color_hex?: string | null;
  lot_code?: string;
  initial_weight_g?: number | null;
  remaining_weight_g?: number | null;
  location?: string;
  storage_state?: MaterialStorageState;
  opened_at?: string | null;
  dried_at?: string | null;
  expires_at?: string | null;
  revision?: number;
}

export interface MaterialConsumption {
  id: number;
  spool_id: number;
  predicted_weight_g: number | null;
  actual_weight_g: number | null;
  status: "planned" | "confirmed" | "released";
  remaining_weight_after_g: number | null;
  note: string;
  created_at: string;
}

export interface MaterialQualitySample {
  id: number;
  spool_id: number;
  sample_type: "dimensional" | "calibration";
  metric_name: string;
  nominal_value_mm: number;
  measured_value_mm: number;
  tolerance_mm: number;
  deviation_mm: number;
  result: "passed" | "failed";
  photo_object_id: number | null;
  note: string;
  created_at: string;
}

export interface MaterialCompatibilityResult {
  status: "compatible" | "incompatible" | "unknown";
  reasons: string[];
  warnings: string[];
  available_weight_g: number | null;
  required_weight_g: number | null;
}

export interface SpoolmanSyncResult {
  printer_id: number;
  status: "synced" | "unavailable";
  imported: number;
  updated: number;
  total: number;
  detail: string;
}
