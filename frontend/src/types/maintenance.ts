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
  tags: string[];
  primary_tag?: string | null;
  is_applicable: boolean;
  not_applicable_at?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  due_status: "due" | "soon" | "ok" | "unknown" | "not_validated" | "needs_review" | "not_applicable";
  days_until_due?: number | null;
  print_hours_delta?: number | null;
  print_hours_until_due?: number | null;
  due_detail?: string | null;
  recommended_interval_kind?: "days" | "print_hours" | null;
  recommended_interval_value?: number | null;
  maintenance_help?: {
    how_to: string[];
    why: string;
    prevents: string[];
    recommendation: string;
  } | null;
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
