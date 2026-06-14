import { Activity, FileText, Home, Info, Network, Printer, Radio, RefreshCw, Scale, Settings, SlidersHorizontal, Users, Wrench, Zap } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export type AppSection =
  | "overview"
  | "printers"
  | "printer-detail"
  | "agents"
  | "agent-detail"
  | "social"
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
    detail: "Dashboard global da frota, agentes, alertas e ações pendentes.",
    purpose: "Use esta tela para acompanhar saúde, manutenção, updates, calibração, agentes e impressoras da frota inteira.",
  },
  {
    key: "printers",
    icon: Printer,
    label: "Impressoras",
    detail: "Cadastro, busca e acesso ao detalhe de cada impressora.",
    purpose: "Gerencie a frota e abra uma impressora para operar, diagnosticar, atualizar, calibrar ou manter.",
  },
  {
    key: "printer-detail",
    icon: Printer,
    label: "Detalhe da impressora",
    detail: "Contexto operacional de uma impressora.",
    purpose: "Operação, atualização, calibração, firmware, manutenção, diagnóstico, backups e agentes ficam dentro da impressora selecionada.",
  },
  {
    key: "agents",
    icon: Radio,
    label: "Agentes",
    detail: "Lista de agentes, detalhe, instalação por token e saúde.",
    purpose: "Gerencie os agentes da frota e abra um agente para diagnosticar saúde, fila, versão, logs sanitizados e vínculo.",
  },
  {
    key: "agent-detail",
    icon: Radio,
    label: "Detalhe do agente",
    detail: "Diagnóstico e vínculo de um agente.",
    purpose: "Veja saúde, fila, doctor remoto, suporte e credencial do agente dentro do registro selecionado.",
  },
  {
    key: "social",
    icon: Users,
    label: "Social",
    detail: "Perfil público, catálogo, comunidades e relações.",
    purpose: "Gerencie identidade social, impressoras públicas, comunidades automáticas e relações sem conceder acesso operacional.",
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
    label: "Administração",
    detail: "Configuração global, versão publicada e status da plataforma.",
    purpose: "Administre informações globais do Printora. Diagnósticos de impressora e agente ficam dentro dos registros.",
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
  { title: "Principal", sections: ["overview", "printers", "agents", "social", "setup"] },
  { title: "Sistema", sections: ["settings"] },
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
  void printerAvailability;
  if (sectionKey === "printer-detail" || sectionKey === "agent-detail") {
    return false;
  }
  if (onlinePrinterSections.has(sectionKey) || selectedPrinterLocalSections.has(sectionKey)) {
    return false;
  }
  return true;
}

export function shouldRedirectSection(sectionKey: AppSection, printerAvailability: PrinterAvailability) {
  void printerAvailability;
  if (sectionKey === "monitoring" || sectionKey === "updates" || sectionKey === "tests" || sectionKey === "firmware" || sectionKey === "maintenance") {
    return true;
  }
  return false;
}

export function canUsePrinterTab(sectionKey: AppSection, printerAvailability: PrinterAvailability) {
  if (onlinePrinterSections.has(sectionKey)) {
    return printerAvailability === "online";
  }
  if (selectedPrinterLocalSections.has(sectionKey)) {
    return printerAvailability !== "none";
  }
  return true;
}

export function getInitialSection(): AppSection {
  const section = new URLSearchParams(window.location.search).get("section") ?? window.location.hash.replace("#", "");
  if (section === "operation") return "monitoring";
  if (section === "calibration") return "tests";
  return appSections.some((candidate) => candidate.key === section) ? (section as AppSection) : "overview";
}
