import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  ChevronRight,
  Circle,
  FileArchive,
  ListChecks,
  Radio,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";
import {
  deriveOnboardingCompletion,
  inspectOnboardingRequirements,
  loadOnboardingEvidence,
  nextOnboardingStep,
  readOnboardingResume,
  writeOnboardingResume,
  type OnboardingEvidence,
  type OnboardingStepKey,
} from "../services/onboardingProgress";
import type { PrinterRecord } from "../types/printers";
import type { ScreenPropsFor } from "./ScreenProps";
import "../styles/onboarding.css";

type OnboardingScreenProps = ScreenPropsFor<
  | "fleetPairingOverviews"
  | "loadFleetAgentPairings"
  | "loadPrinters"
  | "openCreatePrinterModal"
  | "openEditPrinterModal"
  | "printers"
  | "selectPrinter"
  | "setActiveSection"
>;

const EMPTY_EVIDENCE: OnboardingEvidence = {
  connectedPrinterIds: [],
  projects: null,
  slicingJobs: null,
  preflights: null,
  unavailableSources: [],
};

const STEP_ORDER: OnboardingStepKey[] = ["environment", "printer", "agent", "project", "preflight", "complete"];

export function OnboardingScreen(props: OnboardingScreenProps) {
  const {
    fleetPairingOverviews,
    loadFleetAgentPairings,
    loadPrinters,
    openCreatePrinterModal,
    openEditPrinterModal,
    printers,
    selectPrinter,
    setActiveSection,
  } = props;
  const requirements = useMemo(() => inspectOnboardingRequirements(), []);
  const [evidence, setEvidence] = useState<OnboardingEvidence>(EMPTY_EVIDENCE);
  const [loading, setLoading] = useState(true);
  const [selectedStep, setSelectedStep] = useState<OnboardingStepKey>(() => readOnboardingResume(window.localStorage)?.step ?? "environment");

  const refreshEvidence = useCallback(async () => {
    setLoading(true);
    const nextEvidence = await loadOnboardingEvidence(printers);
    setEvidence(nextEvidence);
    setLoading(false);
  }, [printers]);

  const printerSignature = printers
    .map((printer) => `${printer.id}:${printer.cloud_status}:${printer.latest_agent_last_seen_at ?? ""}`)
    .join("|");

  useEffect(() => {
    void refreshEvidence();
  }, [printerSignature]);

  const completion = deriveOnboardingCompletion(requirements, printers, evidence);
  const nextStep = nextOnboardingStep(completion);
  const completedCount = Object.values(completion).filter(Boolean).length;
  const allSourcesAvailable = evidence.unavailableSources.length === 0;

  useEffect(() => {
    if (loading || !allSourcesAvailable) return;
    setSelectedStep(nextStep);
    writeOnboardingResume(window.localStorage, nextStep);
  }, [allSourcesAvailable, loading, nextStep]);

  async function refreshAll() {
    await Promise.allSettled([loadPrinters(), loadFleetAgentPairings()]);
    await refreshEvidence();
  }

  function continueAt(step: OnboardingStepKey, action: () => void) {
    setSelectedStep(step);
    writeOnboardingResume(window.localStorage, step);
    action();
  }

  const steps = buildSteps(completion, evidence, printers, fleetPairingOverviews);
  const activePrinter = choosePrinter(printers, evidence.connectedPrinterIds);

  return (
    <article className="panel wide panel-section onboarding-panel">
      <div className="panel-heading onboarding-heading">
        <div>
          <span className="onboarding-eyebrow">Primeiros passos</span>
          <h2>Prepare sua primeira impressão com segurança</h2>
          <p className="muted">Siga uma etapa por vez. O Printora confirma os resultados reais e explica os termos quando você precisar.</p>
        </div>
        <button type="button" className="secondary-button" onClick={() => void refreshAll()} disabled={loading}>
          <RefreshCw className={loading ? "button-busy-icon" : undefined} size={16} />
          {loading ? "Verificando" : "Verificar novamente"}
        </button>
      </div>

      <section className="onboarding-progress" aria-label={`${completedCount} de 5 etapas concluídas`}>
        <div>
          <strong>{completedCount} de 5 etapas concluídas</strong>
          <span>{completedCount === 5 ? "Tudo pronto para continuar." : "Seu avanço fica salvo neste dispositivo."}</span>
        </div>
        <div className="onboarding-progress-track" aria-hidden="true">
          <span style={{ width: `${completedCount * 20}%` }} />
        </div>
      </section>

      {evidence.unavailableSources.length > 0 ? (
        <div className="onboarding-message warning" role="status">
          <AlertTriangle size={18} />
          <div>
            <strong>Não foi possível confirmar todas as etapas agora</strong>
            <span>A conexão ou algum serviço não respondeu. Nenhuma etapa foi marcada como concluída sem confirmação, e seu ponto de retorno foi preservado.</span>
          </div>
        </div>
      ) : null}

      <div className="onboarding-layout">
        <nav className="onboarding-step-list" aria-label="Etapas dos primeiros passos">
          {steps.map((step, index) => {
            const isSelected = selectedStep === step.key;
            const StatusIcon = step.complete ? CheckCircle2 : index === STEP_ORDER.indexOf(nextStep) ? ChevronRight : Circle;
            return (
              <button
                key={step.key}
                type="button"
                className={`onboarding-step-button ${isSelected ? "active" : ""} ${step.complete ? "complete" : ""}`}
                onClick={() => setSelectedStep(step.key)}
                aria-current={isSelected ? "step" : undefined}
              >
                <StatusIcon size={18} />
                <span>
                  <small>Etapa {index + 1}</small>
                  <strong>{step.title}</strong>
                </span>
              </button>
            );
          })}
        </nav>

        <section className="onboarding-step-detail" aria-live="polite">
          {renderStepDetail({
            step: steps.find((candidate) => candidate.key === selectedStep) ?? steps[0],
            requirements,
            loading,
            printers,
            activePrinter,
            onRefresh: refreshAll,
            onAddPrinter: openCreatePrinterModal,
            onEditPrinter: openEditPrinterModal,
            onOpenAgents: () => continueAt("agent", () => {
              if (activePrinter) selectPrinter(activePrinter.id);
              setActiveSection("agents");
            }),
            onOpenProjects: (step) => continueAt(step, () => setActiveSection("projects")),
            onFinish: () => continueAt("complete", () => setActiveSection("overview")),
          })}
        </section>
      </div>
    </article>
  );
}

type StepView = {
  key: OnboardingStepKey;
  title: string;
  summary: string;
  complete: boolean;
  value: string;
};

function buildSteps(
  completion: ReturnType<typeof deriveOnboardingCompletion>,
  evidence: OnboardingEvidence,
  printers: PrinterRecord[],
  pairing: OnboardingScreenProps["fleetPairingOverviews"],
): StepView[] {
  const activeAgents = Object.values(pairing).flatMap((overview) => overview.agents).filter((agent) => agent.status === "active").length;
  const approvedPreflights = evidence.preflights?.filter((preflight) => preflight.status === "approved").length ?? 0;
  return [
    { key: "environment", title: "Conferir este dispositivo", summary: "Valide navegador, retomada local e rede.", complete: completion.environment, value: completion.environment ? "Dispositivo pronto" : "Ação necessária" },
    { key: "printer", title: "Conectar a impressora", summary: "Cadastre a máquina e confirme o Moonraker.", complete: completion.printer, value: completion.printer ? `${evidence.connectedPrinterIds.length} conectada(s)` : `${printers.length} cadastrada(s)` },
    { key: "agent", title: "Ligar o agente", summary: "Pareie o serviço que conversa com a impressora.", complete: completion.agent, value: completion.agent ? "Agente online" : activeAgents > 0 ? "Pareado, mas offline" : "Ainda não pareado" },
    { key: "project", title: "Escolher o primeiro projeto", summary: "Adicione o arquivo que deseja preparar.", complete: completion.project, value: evidence.projects === null ? "Não confirmado" : `${evidence.projects.length} projeto(s)` },
    { key: "preflight", title: "Fazer a checagem final", summary: "Valide o G-code sem iniciar a impressão.", complete: completion.preflight, value: evidence.preflights === null ? "Não confirmado" : `${approvedPreflights} aprovado(s)` },
    { key: "complete", title: "Tudo pronto", summary: "Revise o resultado e continue no Printora.", complete: completedCount(completion) === 5, value: completedCount(completion) === 5 ? "Concluído" : "Aguardando etapas" },
  ];
}

function renderStepDetail(input: {
  step: StepView;
  requirements: ReturnType<typeof inspectOnboardingRequirements>;
  loading: boolean;
  printers: PrinterRecord[];
  activePrinter: PrinterRecord | null;
  onRefresh: () => Promise<void>;
  onAddPrinter: () => void;
  onEditPrinter: (printer: PrinterRecord) => void;
  onOpenAgents: () => void;
  onOpenProjects: (step: "project" | "preflight") => void;
  onFinish: () => void;
}) {
  const { step } = input;
  const icon = stepIcon(step.key);
  const StepIcon = icon;
  return (
    <>
      <div className="onboarding-detail-heading">
        <span className={step.complete ? "ready" : "pending"}><StepIcon size={20} /></span>
        <div>
          <h3>{step.title}</h3>
          <p>{step.summary}</p>
        </div>
        <strong className={step.complete ? "onboarding-status ready" : "onboarding-status"}>{step.value}</strong>
      </div>
      {step.key === "environment" ? <Requirements requirements={input.requirements} onRefresh={input.onRefresh} loading={input.loading} /> : null}
      {step.key === "printer" ? <PrinterStep printers={input.printers} activePrinter={input.activePrinter} onAdd={input.onAddPrinter} onEdit={input.onEditPrinter} /> : null}
      {step.key === "agent" ? <AgentStep activePrinter={input.activePrinter} onOpen={input.onOpenAgents} /> : null}
      {step.key === "project" ? <ProjectStep onOpen={() => input.onOpenProjects("project")} /> : null}
      {step.key === "preflight" ? <PreflightStep onOpen={() => input.onOpenProjects("preflight")} /> : null}
      {step.key === "complete" ? <CompleteStep complete={step.complete} onFinish={input.onFinish} /> : null}
    </>
  );
}

function Requirements({ requirements, onRefresh, loading }: { requirements: ReturnType<typeof inspectOnboardingRequirements>; onRefresh: () => Promise<void>; loading: boolean }) {
  return (
    <div className="onboarding-checks">
      {requirements.map((requirement) => (
        <div key={requirement.key} className={`onboarding-check ${requirement.status}`}>
          {requirement.status === "ready" ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <div><strong>{requirement.label}</strong><span>{requirement.detail}</span></div>
        </div>
      ))}
      <button type="button" className="primary-button" onClick={() => void onRefresh()} disabled={loading}>Verificar este dispositivo</button>
    </div>
  );
}

function PrinterStep({ printers, activePrinter, onAdd, onEdit }: { printers: PrinterRecord[]; activePrinter: PrinterRecord | null; onAdd: () => void; onEdit: (printer: PrinterRecord) => void }) {
  return (
    <div className="onboarding-guidance">
      <p>Cadastre o endereço da impressora. O Printora fará uma leitura segura para confirmar se o Moonraker responde.</p>
      <details><summary>O que é Moonraker?</summary><p>É o serviço que permite ao Printora consultar o estado do Klipper e preparar operações na impressora.</p></details>
      {printers.length === 0 ? (
        <button type="button" className="primary-button" onClick={onAdd}>Cadastrar minha impressora</button>
      ) : (
        <button type="button" className="primary-button" onClick={() => onEdit(activePrinter ?? printers[0])}>Revisar conexão da impressora</button>
      )}
    </div>
  );
}

function AgentStep({ activePrinter, onOpen }: { activePrinter: PrinterRecord | null; onOpen: () => void }) {
  return (
    <div className="onboarding-guidance">
      <p>O agente é instalado perto da impressora e usa um código temporário. Repetir o processo não deve criar uma segunda instalação ativa.</p>
      <details><summary>Por que o agente é necessário?</summary><p>Ele faz a ponte segura entre o Printora e a rede local da impressora, sem colocar credenciais em links.</p></details>
      <button type="button" className="primary-button" onClick={onOpen} disabled={!activePrinter}>{activePrinter ? "Instalar ou revisar agente" : "Conecte a impressora primeiro"}</button>
    </div>
  );
}

function ProjectStep({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="onboarding-guidance">
      <p>Crie um projeto e adicione um arquivo STL ou 3MF. Use um modelo pequeno e conhecido para a primeira preparação.</p>
      <ul><li>Confira o nome e a versão do arquivo.</li><li>Escolha a impressora correta.</li><li>Não inicie a impressão nesta etapa.</li></ul>
      <button type="button" className="primary-button" onClick={onOpen}>Abrir meus projetos</button>
    </div>
  );
}

function PreflightStep({ onOpen }: { onOpen: () => void }) {
  return (
    <div className="onboarding-guidance">
      <p>Fatie o projeto e execute o preflight. Essa checagem procura bloqueios antes de qualquer comando físico.</p>
      <details><summary>O que é preflight?</summary><p>É a checagem final do arquivo, da impressora e do estado atual. Aprovar o preflight não inicia a impressão.</p></details>
      <button type="button" className="primary-button" onClick={onOpen}>Preparar projeto e fazer preflight</button>
    </div>
  );
}

function CompleteStep({ complete, onFinish }: { complete: boolean; onFinish: () => void }) {
  return complete ? (
    <div className="onboarding-complete">
      <ShieldCheck size={34} />
      <h3>Primeira preparação concluída</h3>
      <p>A impressora, o agente, o projeto e o preflight foram confirmados. Iniciar uma impressão continua exigindo sua revisão e confirmação.</p>
      <button type="button" className="primary-button" onClick={onFinish}>Ir para a visão geral</button>
    </div>
  ) : (
    <div className="onboarding-message"><ListChecks size={18} /><div><strong>Conclua as etapas anteriores</strong><span>O Printora só libera este resumo depois de confirmar os resultados reais.</span></div></div>
  );
}

function choosePrinter(printers: PrinterRecord[], connectedIds: number[]) {
  return printers.find((printer) => connectedIds.includes(printer.id)) ?? printers.find((printer) => printer.cloud_status === "online") ?? printers[0] ?? null;
}

function completedCount(completion: ReturnType<typeof deriveOnboardingCompletion>) {
  return Object.values(completion).filter(Boolean).length;
}

function stepIcon(step: OnboardingStepKey) {
  if (step === "printer") return CheckCircle2;
  if (step === "agent") return Radio;
  if (step === "project") return FileArchive;
  if (step === "preflight" || step === "complete") return ShieldCheck;
  return ListChecks;
}
