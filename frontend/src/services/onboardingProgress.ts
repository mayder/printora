import { printProjectsApi } from "./printProjectsApi";
import { printerApi } from "./printerApi";
import { slicingApi, type PrintPreflight, type SlicingJob } from "./slicingApi";
import type { PrinterRecord } from "../types/printers";
import type { PrintProjectSummary } from "../types/printProjects";

export type OnboardingStepKey = "environment" | "printer" | "agent" | "project" | "preflight" | "complete";

export type OnboardingResume = {
  step: OnboardingStepKey;
  updatedAt: string;
};

export type OnboardingRequirement = {
  key: "browser" | "storage" | "network" | "secure_context";
  label: string;
  detail: string;
  status: "ready" | "warning" | "blocked";
};

export type OnboardingEvidence = {
  connectedPrinterIds: number[];
  projects: PrintProjectSummary[] | null;
  slicingJobs: SlicingJob[] | null;
  preflights: PrintPreflight[] | null;
  unavailableSources: Array<"moonraker" | "projects" | "slicing_jobs" | "preflights">;
};

export type OnboardingCompletion = {
  environment: boolean;
  printer: boolean;
  agent: boolean;
  project: boolean;
  preflight: boolean;
};

const RESUME_KEY = "printora.onboarding.resume.v1";
const STEP_KEYS: OnboardingStepKey[] = ["environment", "printer", "agent", "project", "preflight", "complete"];

export function readOnboardingResume(storage: Storage): OnboardingResume | null {
  const raw = storage.getItem(RESUME_KEY);
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as Partial<OnboardingResume>;
    if (!value.step || !STEP_KEYS.includes(value.step) || typeof value.updatedAt !== "string") {
      storage.removeItem(RESUME_KEY);
      return null;
    }
    return { step: value.step, updatedAt: value.updatedAt };
  } catch {
    storage.removeItem(RESUME_KEY);
    return null;
  }
}

export function writeOnboardingResume(storage: Storage, step: OnboardingStepKey, now = new Date()): OnboardingResume {
  const value = { step, updatedAt: now.toISOString() };
  storage.setItem(RESUME_KEY, JSON.stringify(value));
  return value;
}

export function inspectOnboardingRequirements(): OnboardingRequirement[] {
  const browserReady = typeof window.fetch === "function" && typeof Promise.allSettled === "function";
  const storageReady = canWriteLocalProgress(window.localStorage);
  const online = window.navigator.onLine;
  const secureContext = window.isSecureContext !== false;
  return [
    {
      key: "browser",
      label: "Navegador compatível",
      detail: browserReady ? "Os recursos necessários estão disponíveis." : "Atualize o navegador para continuar com segurança.",
      status: browserReady ? "ready" : "blocked",
    },
    {
      key: "storage",
      label: "Retomada neste dispositivo",
      detail: storageReady ? "O passo atual pode ser recuperado ao voltar." : "Libere o armazenamento local do navegador para preservar o passo atual.",
      status: storageReady ? "ready" : "blocked",
    },
    {
      key: "network",
      label: "Conexão de rede",
      detail: online ? "O navegador informa que a rede está disponível." : "Você está offline. O progresso local será mantido para tentar novamente.",
      status: online ? "ready" : "warning",
    },
    {
      key: "secure_context",
      label: "Conexão protegida",
      detail: secureContext ? "A página pode usar recursos protegidos do navegador." : "Abra o Printora por HTTPS ou no computador local para copiar credenciais com segurança.",
      status: secureContext ? "ready" : "warning",
    },
  ];
}

export async function loadOnboardingEvidence(printers: PrinterRecord[]): Promise<OnboardingEvidence> {
  const [moonraker, projects, slicingJobs, preflights] = await Promise.all([
    loadConnectedPrinters(printers),
    settle(() => printProjectsApi.myProjects()),
    settle(() => slicingApi.jobs()),
    settle(() => slicingApi.preflights()),
  ]);
  const unavailableSources: OnboardingEvidence["unavailableSources"] = [];
  if (!moonraker.available) unavailableSources.push("moonraker");
  if (projects.value === null) unavailableSources.push("projects");
  if (slicingJobs.value === null) unavailableSources.push("slicing_jobs");
  if (preflights.value === null) unavailableSources.push("preflights");
  return {
    connectedPrinterIds: moonraker.connectedPrinterIds,
    projects: projects.value,
    slicingJobs: slicingJobs.value,
    preflights: preflights.value,
    unavailableSources,
  };
}

export function deriveOnboardingCompletion(
  requirements: OnboardingRequirement[],
  printers: PrinterRecord[],
  evidence: OnboardingEvidence,
): OnboardingCompletion {
  return {
    environment: requirements.every((requirement) => requirement.status !== "blocked"),
    printer: evidence.connectedPrinterIds.length > 0,
    agent: printers.some((printer) => printer.cloud_status === "online"),
    project: Boolean(evidence.projects?.length),
    preflight: Boolean(evidence.preflights?.some((preflight) => preflight.status === "approved")),
  };
}

export function nextOnboardingStep(completion: OnboardingCompletion): OnboardingStepKey {
  if (!completion.environment) return "environment";
  if (!completion.printer) return "printer";
  if (!completion.agent) return "agent";
  if (!completion.project) return "project";
  if (!completion.preflight) return "preflight";
  return "complete";
}

function canWriteLocalProgress(storage: Storage): boolean {
  const probe = `${RESUME_KEY}.probe`;
  try {
    storage.setItem(probe, "1");
    storage.removeItem(probe);
    return true;
  } catch {
    return false;
  }
}

async function loadConnectedPrinters(printers: PrinterRecord[]) {
  if (printers.length === 0) return { available: true, connectedPrinterIds: [] as number[] };
  const results = await Promise.all(printers.map(async (printer) => {
    try {
      const response = await printerApi.moonrakerStatus(printer.id);
      if (!response.ok) return { available: false, printerId: printer.id, connected: false };
      const payload = (await response.json()) as { connected?: boolean };
      return { available: true, printerId: printer.id, connected: payload.connected === true };
    } catch {
      return { available: false, printerId: printer.id, connected: false };
    }
  }));
  return {
    available: results.some((result) => result.available),
    connectedPrinterIds: results.filter((result) => result.connected).map((result) => result.printerId),
  };
}

async function settle<T>(task: () => Promise<T>): Promise<{ value: T | null }> {
  try {
    return { value: await task() };
  } catch {
    return { value: null };
  }
}
