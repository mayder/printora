import { Activity, FileText, Gauge, Home, ListChecks, Printer, RefreshCw, Settings, SlidersHorizontal, Wrench, Zap } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type AppSection =
  | "overview"
  | "printers"
  | "operation"
  | "monitoring"
  | "updates"
  | "calibration"
  | "tests"
  | "firmware"
  | "maintenance"
  | "reports"
  | "settings";

export const appSections: Array<{
  key: AppSection;
  icon: LucideIcon;
  label: string;
  detail: string;
  purpose: string;
}> = [
  {
    key: "overview",
    icon: Home,
    label: "Visão geral",
    detail: "Dashboard geral da frota e da impressora selecionada.",
    purpose: "Use esta tela para saber rapidamente se há bloqueios, alertas ou pendências antes de trabalhar na impressora.",
  },
  {
    key: "printers",
    icon: Printer,
    label: "Impressoras",
    detail: "Cadastro, descoberta e seleção da impressora ativa.",
    purpose: "Gerencie as impressoras cadastradas e defina qual delas controla o contexto do restante do sistema.",
  },
  {
    key: "operation",
    icon: Gauge,
    label: "Operação",
    detail: "Painéis read-only no estilo Mainsail.",
    purpose: "Acompanhe estado operacional, temperaturas, toolhead, extrusor e periféricos sem enviar comandos para a impressora.",
  },
  {
    key: "monitoring",
    icon: Activity,
    label: "Monitoramento",
    detail: "Telemetria ao vivo da impressora.",
    purpose: "Acompanhe em tempo real temperaturas, progresso, comunicação, fans, sistema e CAN da impressora ativa.",
  },
  {
    key: "updates",
    icon: RefreshCw,
    label: "Atualizações",
    detail: "Update Manager da impressora selecionada.",
    purpose: "Veja componentes desatualizados e execute updates pelo Moonraker, no mesmo modelo do Mainsail.",
  },
  {
    key: "calibration",
    icon: SlidersHorizontal,
    label: "Calibração",
    detail: "Z-offset, primeira camada e ajustes manuais.",
    purpose: "Registre offsets, siga o wizard manual e compare variações por chapa, material e toolhead.",
  },
  {
    key: "tests",
    icon: ListChecks,
    label: "Testes",
    detail: "Centro de testes Voron e histórico de resultados.",
    purpose: "Escolha um teste, revise a ajuda quando precisar e execute com confirmação presencial.",
  },
  {
    key: "firmware",
    icon: Zap,
    label: "Firmware",
    detail: "Inventario de MCUs, associacao de placas, build e flash planejado.",
    purpose: "Gerencie MCUs, presets, builds e flash planejado para a impressora ativa.",
  },
  {
    key: "maintenance",
    icon: Wrench,
    label: "Manutenção",
    detail: "Backups, tarefas preventivas e diário da impressora.",
    purpose: "Acompanhe manutenção preventiva, eventos e backups locais com histórico por impressora.",
  },
  {
    key: "reports",
    icon: FileText,
    label: "Relatórios",
    detail: "Auditorias, snapshots, diffs e relatórios sanitizados.",
    purpose: "Gere diagnósticos compartilháveis e compare snapshots sem expor dados sensíveis.",
  },
  {
    key: "settings",
    icon: Settings,
    label: "Configurações",
    detail: "Preferências, integrações e contexto da impressora ativa.",
    purpose: "Versão instalada, releases e updates do próprio Printora.",
  },
];

export const navGroups: Array<{ title: string; sections: AppSection[] }> = [
  { title: "Principal", sections: ["overview", "printers"] },
  { title: "Impressora ativa", sections: ["operation", "monitoring", "updates", "calibration", "tests", "firmware", "maintenance"] },
  { title: "Diagnóstico", sections: ["reports", "settings"] },
];

export const onlinePrinterSections = new Set<AppSection>([
  "operation",
  "monitoring",
  "updates",
  "calibration",
  "tests",
  "firmware",
  "reports",
]);

export const selectedPrinterLocalSections = new Set<AppSection>(["maintenance"]);

export type PrinterAvailability = "none" | "unknown" | "online" | "offline";

export function canShowSection(sectionKey: AppSection, printerAvailability: PrinterAvailability) {
  if (onlinePrinterSections.has(sectionKey)) {
    return printerAvailability === "online";
  }
  if (selectedPrinterLocalSections.has(sectionKey)) {
    return printerAvailability !== "none";
  }
  return true;
}

export function shouldRedirectSection(sectionKey: AppSection, printerAvailability: PrinterAvailability) {
  if (onlinePrinterSections.has(sectionKey)) {
    return printerAvailability === "none" || printerAvailability === "offline";
  }
  if (selectedPrinterLocalSections.has(sectionKey)) {
    return printerAvailability === "none";
  }
  return false;
}

export function getInitialSection(): AppSection {
  const section = new URLSearchParams(window.location.search).get("section") ?? window.location.hash.replace("#", "");
  return appSections.some((candidate) => candidate.key === section) ? (section as AppSection) : "overview";
}
