import { Activity, FileText, Home, Info, Network, Printer, Radio, RefreshCw, Scale, Settings, SlidersHorizontal, Wrench, Zap } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type AppSection =
  | "overview"
  | "printers"
  | "agents"
  | "setup"
  | "monitoring"
  | "updates"
  | "tests"
  | "firmware"
  | "maintenance"
  | "reports"
  | "settings"
  | "account"
  | "about"
  | "license";

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
    key: "agents",
    icon: Radio,
    label: "Agentes",
    detail: "Lista de agentes, detalhe, instalação por token e saúde.",
    purpose: "Gerencie todos os agentes vinculados, detalhe a impressora de cada um e gere tokens de instalação quando necessário.",
  },
  {
    key: "setup",
    icon: Network,
    label: "Setup",
    detail: "Receita guiada para preparar a Pi e fechar a base Klipper.",
    purpose: "Siga a ordem: preparar sistema e SSH, validar a Pi, revisar planos, autorizar etapas críticas e cadastrar a impressora.",
  },
  {
    key: "monitoring",
    icon: Activity,
    label: "Operação",
    detail: "Operação e telemetria ao vivo da impressora.",
    purpose: "Acompanhe em tempo real temperaturas, movimento, extrusor, sistema, CAN e ações protegidas da impressora ativa.",
  },
  {
    key: "updates",
    icon: RefreshCw,
    label: "Atualizações",
    detail: "Update Manager da impressora selecionada.",
    purpose: "Veja componentes desatualizados e execute updates pelo Moonraker, no mesmo modelo do Mainsail.",
  },
  {
    key: "tests",
    icon: SlidersHorizontal,
    label: "Calibração",
    detail: "Centro de calibração Voron, testes e histórico de resultados.",
    purpose: "Escolha uma calibração, revise a ajuda quando precisar e execute ou registre com evidência.",
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
  {
    key: "account",
    icon: Info,
    label: "Conta",
    detail: "Cadastro, login, organizações opcionais e segurança.",
    purpose: "Gerencie acesso cloud, 2FA e organizações opcionais.",
  },
  {
    key: "about",
    icon: Info,
    label: "Sobre",
    detail: "Autoria, proposta do projeto e próximos passos.",
    purpose: "Conheça o Printora, seu autor, as funcionalidades atuais e a visão de evolução do produto.",
  },
  {
    key: "license",
    icon: Scale,
    label: "Licença",
    detail: "Condições de uso, responsabilidade e garantia.",
    purpose: "Leia os termos de uso open source, limitações de responsabilidade e cuidados operacionais.",
  },
];

export const navGroups: Array<{ title: string; sections: AppSection[] }> = [
  { title: "Principal", sections: ["overview", "printers", "agents", "setup"] },
  { title: "Impressora ativa", sections: ["monitoring", "updates", "tests", "firmware", "maintenance"] },
  { title: "Diagnóstico", sections: ["reports", "settings"] },
];

export const onlinePrinterSections = new Set<AppSection>([
  "monitoring",
  "updates",
  "tests",
  "reports",
]);

export const selectedPrinterLocalSections = new Set<AppSection>(["firmware", "maintenance"]);

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
  if (section === "operation") return "monitoring";
  if (section === "calibration") return "tests";
  return appSections.some((candidate) => candidate.key === section) ? (section as AppSection) : "overview";
}
