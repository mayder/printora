export type FinanceRow = Record<string, string | number | boolean | null>;

export interface FinanceOverview {
  counts: Record<string, number>;
  orders: FinanceRow[];
  payments: FinanceRow[];
  ledger: FinanceRow[];
  disputes: FinanceRow[];
  payouts: FinanceRow[];
  reconciliations: FinanceRow[];
}

export interface ComplianceControl {
  control_key: string;
  status: string;
  evidence_present: boolean;
  reviewed_by_user_id: number | null;
  reviewed_at: string | null;
  expires_at: string | null;
}

export interface FinanceReadiness {
  payment_mode: string;
  runtime_supports_real_payments: boolean;
  real_payments_allowed: boolean;
  pending_controls: string[];
  blocked_controls: string[];
  controls: ComplianceControl[];
  retention_policies: Array<{
    data_class: string;
    retention_days: number;
    legal_basis: string;
    deletion_mode: string;
  }>;
  expired_audit_rows_preview: number;
}
