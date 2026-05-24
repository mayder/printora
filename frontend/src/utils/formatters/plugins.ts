import type { PluginAuditItem } from "../../types";

export function formatPluginClassification(classification: PluginAuditItem["classification"]) {
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

export function formatPluginAction(action: PluginAuditItem["action"]) {
  const labels: Record<PluginAuditItem["action"], string> = {
    manter: "manter",
    investigar: "investigar",
    remover_depois_backup: "remover depois de backup",
    nao_remover_agora: "não remover agora",
  };
  return labels[action];
}
