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
