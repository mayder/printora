export type PluginAuditItem = {
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

export type PluginAuditResponse = {
  printer_id: number;
  safe_mode: string;
  source: string;
  summary: string;
  counts: Record<string, number>;
  unknown_update_manager_components: string[];
  items: PluginAuditItem[];
};
