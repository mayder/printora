import { useState } from "react";
import { Metric } from "../components/common";
import type { MaintenanceTaskRecord } from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type MaintenanceScreenProps = ScreenPropsFor<
  | "CheckCircle2"
  | "CircleSlash"
  | "HelpCircle"
  | "Plus"
  | "Timer"
  | "Trash2"
  | "Undo2"
  | "X"
  | "createDefaultMaintenanceTasks"
  | "deleteLatestMaintenanceTaskEvent"
  | "deleteMaintenanceEvent"
  | "formatDueStatus"
  | "formatHours"
  | "formatLocalDateTime"
  | "formatMaintenanceEventType"
  | "formatMaintenanceInterval"
  | "formatOptionalHours"
  | "formatOptionalLocalDateTime"
  | "formatPrintHoursDueLine"
  | "loading"
  | "maintenanceEvents"
  | "maintenanceFilter"
  | "maintenancePrintHours"
  | "maintenancePrintHoursAvailable"
  | "maintenanceSort"
  | "maintenanceSummary"
  | "maintenanceTagFilter"
  | "maintenanceTagOptions"
  | "maintenanceTasks"
  | "nextMaintenanceTask"
  | "openMaintenanceDoneModal"
  | "openMaintenanceFreeModal"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setMaintenanceFilter"
  | "setMaintenanceSort"
  | "setMaintenanceTagFilter"
  | "status"
  | "updateMaintenanceTaskApplicability"
  | "visibleMaintenanceTasks"
>;

export function MaintenanceScreen(props: MaintenanceScreenProps) {
  const {
    CheckCircle2,
    CircleSlash,
    HelpCircle,
    Plus,
    Timer,
    Trash2,
    Undo2,
    X,
    createDefaultMaintenanceTasks,
    deleteLatestMaintenanceTaskEvent,
    deleteMaintenanceEvent,
    formatDueStatus,
    formatHours,
    formatLocalDateTime,
    formatMaintenanceEventType,
    formatMaintenanceInterval,
    formatOptionalHours,
    formatOptionalLocalDateTime,
    formatPrintHoursDueLine,
    loading,
    maintenanceEvents,
    maintenanceFilter,
    maintenancePrintHours,
    maintenancePrintHoursAvailable,
    maintenanceSort,
    maintenanceSummary,
    maintenanceTagFilter,
    maintenanceTagOptions,
    maintenanceTasks,
    nextMaintenanceTask,
    openMaintenanceDoneModal,
    openMaintenanceFreeModal,
    selectedPrinter,
    selectedPrinterId,
    setMaintenanceFilter,
    setMaintenanceSort,
    setMaintenanceTagFilter,
    status,
    updateMaintenanceTaskApplicability,
    visibleMaintenanceTasks,
  } = props;
  const [helpTask, setHelpTask] = useState<MaintenanceTaskRecord | null>(null);
  const helpContent = helpTask ? maintenanceHelpContent(helpTask) : null;
  const renderMaintenanceTask = (task: MaintenanceTaskRecord) => (
    <article key={task.id} className={`maintenance-task-card ${!task.is_applicable ? "not-applicable" : task.is_active ? task.due_status : "inactive"}`}>
      <div className="maintenance-task-card-header">
        <div className="maintenance-card-badge-row">
          <span className={`status-pill ${!task.is_applicable ? "not-applicable" : task.is_active ? task.due_status : "inactive"}`}>{formatDueStatus(task)}</span>
          <div className="maintenance-tag-list" aria-label="Áreas da rotina">
            {(task.tags ?? []).map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </div>
        </div>
        <strong>{task.name}</strong>
      </div>
      <div className="maintenance-task-meta">
        <span>{task.component}</span>
        <span>{!task.is_applicable ? "Oculta do plano preventivo" : task.is_active ? formatMaintenanceInterval(task) : "Sem lembrete recorrente"}</span>
        <span>Última: {formatOptionalLocalDateTime(task.last_done_at)}</span>
        {task.interval_kind === "print_hours" && maintenancePrintHoursAvailable ? (
          <>
            <span>Base: {formatOptionalHours(task.last_done_print_hours)}</span>
            <span>Atual: {formatOptionalHours(task.current_print_hours)}{task.current_print_hours_source === "cached" ? " · desatualizado" : ""}</span>
            <span>{formatPrintHoursDueLine(task)}</span>
          </>
        ) : null}
      </div>
      <div className={`maintenance-card-actions ${task.is_applicable && !task.last_done_at ? "has-na" : task.last_done_at || !task.is_applicable ? "has-undo" : ""}`}>
        {task.is_applicable ? (
          <button type="button" className="maintenance-done-button" onClick={() => openMaintenanceDoneModal(task)} disabled={loading}>
            <CheckCircle2 size={14} />
            Marcar feita
          </button>
        ) : null}
        <button type="button" className="secondary-button maintenance-help-button" onClick={() => setHelpTask(task)} disabled={loading}>
          <HelpCircle size={14} />
          Como fazer
        </button>
        {task.is_applicable && !task.last_done_at ? (
          <button
            type="button"
            className="ghost-button maintenance-na-button"
            onClick={() => void updateMaintenanceTaskApplicability(task.id, false)}
            disabled={loading}
            title="Marcar rotina como não aplicável para esta impressora"
          >
            <CircleSlash size={14} />
            N/A
          </button>
        ) : null}
        {task.is_applicable && task.last_done_at ? (
          <button
            type="button"
            className="ghost-button danger-ghost"
            onClick={() => void deleteLatestMaintenanceTaskEvent(task.id)}
            disabled={loading}
          >
            <Undo2 size={14} />
            Desfazer
          </button>
        ) : null}
        {!task.is_applicable ? (
          <button
            type="button"
            className="ghost-button"
            onClick={() => void updateMaintenanceTaskApplicability(task.id, true)}
            disabled={loading}
          >
            <Undo2 size={14} />
            Desfazer
          </button>
        ) : null}
      </div>
    </article>
  );

  return (
    <>
        <article className="panel wide panel-section panel-maintenance">
          <div className="maintenance-workspace">
            <section className="maintenance-hero">
              <div>
                <span className="section-kicker">Plano preventivo</span>
                <h2>{selectedPrinter?.name ?? "Impressora"}</h2>
                <p>
                  {nextMaintenanceTask
                    ? `${nextMaintenanceTask.name}: ${formatDueStatus(nextMaintenanceTask)}`
                    : "Nenhuma rotina preventiva criada."}
                </p>
              </div>
              <div className="maintenance-hero-actions">
                {maintenancePrintHoursAvailable ? (
                  <div className="maintenance-print-hours-chip">
                    <Timer size={16} />
                    <span>Total de impressão</span>
                    <strong>{formatHours(maintenancePrintHours!.total_print_hours ?? 0)}</strong>
                  </div>
                ) : null}
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => void createDefaultMaintenanceTasks()}
                  disabled={!selectedPrinterId || loading || maintenanceSummary?.recommended_tasks.length === 0}
                >
                  <Plus size={16} />
                  Recarregar catálogo
                </button>
              </div>
            </section>

            <div className="maintenance-status-grid">
              <Metric label="Vencidas" value={String(maintenanceSummary?.counts.due ?? 0)} />
              <Metric label="Próximas" value={String(maintenanceSummary?.counts.soon ?? 0)} />
              <Metric label="Em dia" value={String(maintenanceSummary?.counts.ok ?? 0)} />
              <Metric label="Registradas" value={String(maintenanceTasks.length)} />
            </div>

            <section className="maintenance-panel-card">
              <div className="maintenance-section-heading">
                <div>
                  <h3>Rotinas preventivas</h3>
                  <p className="muted">Cada rotina gera alerta quando vencer.</p>
                </div>
                <div className="maintenance-filter-row">
                  <div className="dense-toolbar filter-toolbar" aria-label="Filtros de manutenção">
                    <button type="button" className={maintenanceFilter === "all" ? "active" : ""} onClick={() => setMaintenanceFilter("all")}>
                      Todas
                    </button>
                    <button type="button" className={maintenanceFilter === "due" ? "active" : ""} onClick={() => setMaintenanceFilter("due")}>
                      Vencidas
                    </button>
                    <button type="button" className={maintenanceFilter === "soon" ? "active" : ""} onClick={() => setMaintenanceFilter("soon")}>
                      Próximas
                    </button>
                    <button type="button" className={maintenanceFilter === "ok" ? "active" : ""} onClick={() => setMaintenanceFilter("ok")}>
                      Em dia
                    </button>
                    <button type="button" className={maintenanceFilter === "not_applicable" ? "active" : ""} onClick={() => setMaintenanceFilter("not_applicable")}>
                      N/A
                    </button>
                  </div>
                  {maintenanceTagOptions.length ? (
                    <label className="maintenance-area-select">
                      <span>Área</span>
                      <select value={maintenanceTagFilter} onChange={(event) => setMaintenanceTagFilter(event.target.value)}>
                        <option value="all">Todas as áreas</option>
                        {maintenanceTagOptions.map((tag) => (
                          <option key={tag} value={tag}>
                            {tag}
                          </option>
                        ))}
                      </select>
                    </label>
                  ) : null}
                  <label className="maintenance-area-select">
                    <span>Ordenar</span>
                    <select value={maintenanceSort} onChange={(event) => setMaintenanceSort(event.target.value as typeof maintenanceSort)}>
                      <option value="area">Área</option>
                      <option value="title">Título</option>
                      <option value="criticality">Criticidade</option>
                      <option value="due">Vencimento</option>
                    </select>
                  </label>
                </div>
              </div>

              {visibleMaintenanceTasks.length === 0 ? (
                <div className="empty-maintenance-state">
                  <strong>Nenhuma rotina neste filtro.</strong>
                  <span>O catálogo padrão será carregado automaticamente para esta impressora.</span>
                </div>
              ) : null}

              <div className="maintenance-card-grid">
                {visibleMaintenanceTasks.map(renderMaintenanceTask)}
              </div>

              {maintenanceSummary?.recommended_tasks.length ? (
                <div className="maintenance-catalog-note">
                  <strong>{maintenanceSummary.recommended_tasks.length} rotina(s) do catálogo ainda não foram ativadas.</strong>
                  <button type="button" className="secondary-button" onClick={() => void createDefaultMaintenanceTasks()} disabled={!selectedPrinterId || loading}>
                    Ativar restantes
                  </button>
                </div>
              ) : null}
            </section>

            <section
              className="maintenance-free-card"
              role="button"
              tabIndex={0}
              onClick={() => openMaintenanceFreeModal()}
              onKeyDown={(event: any) => {
                if (event.key === "Enter" || event.key === " ") {
                  openMaintenanceFreeModal();
                }
              }}
            >
              <div>
                <span className="section-kicker">Registro livre</span>
                <h3>Falha, ajuste ou anotação</h3>
                <p>Use para algo que não está no catálogo. Pode virar lembrete, se você definir um prazo.</p>
              </div>
              <button type="button" className="secondary-button" onClick={() => openMaintenanceFreeModal()}>
                <Plus size={16} />
                Adicionar registro
              </button>
            </section>

            <section className="maintenance-panel-card">
              <div className="maintenance-section-heading">
                <div>
                  <h3>Histórico</h3>
                  <p className="muted">{maintenanceEvents.length} registro(s)</p>
                </div>
              </div>
              <div className="maintenance-timeline">
                {maintenanceEvents.length === 0 ? <p className="muted">Nenhum evento registrado.</p> : null}
                {maintenanceEvents.map((event: any) => (
                  <div key={event.id} className="maintenance-event-row">
                    <div className="maintenance-event-content">
                      <strong>{event.title}</strong>
                      <span>
                        {formatMaintenanceEventType(event.event_type)} · {event.component ?? "-"} · {formatLocalDateTime(event.performed_at)}
                      </span>
                      {event.notes ? <small>{event.notes}</small> : null}
                    </div>
                    <button
                      type="button"
                      className="ghost-button danger-ghost"
                      onClick={() => void deleteMaintenanceEvent(event.id)}
                      disabled={loading}
                    >
                      <Trash2 size={14} />
                      Remover
                    </button>
                  </div>
                ))}
              </div>
            </section>
          </div>
        </article>

        {helpTask && helpContent ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Como fazer: ${helpTask.name}`}>
            <div className="modal-card maintenance-help-modal-card">
              <div className="modal-header">
                <div>
                  <h2>{helpTask.name}</h2>
                  <p>{helpTask.component} · {helpTask.is_active ? formatMaintenanceInterval(helpTask) : "sem lembrete recorrente"}</p>
                </div>
                <button type="button" className="icon-button" onClick={() => setHelpTask(null)} aria-label="Fechar Como fazer">
                  <X size={18} />
                </button>
              </div>
              <div className="maintenance-help-content">
                <section>
                  <h3>Como fazer</h3>
                  <ol>
                    {helpContent.howTo.map((step) => (
                      <li key={step}>{step}</li>
                    ))}
                  </ol>
                </section>
                <section>
                  <h3>Por que fazer</h3>
                  <p>{helpContent.why}</p>
                </section>
                <section>
                  <h3>O que evita</h3>
                  <ul>
                    {helpContent.prevents.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </section>
                <section>
                  <h3>Antes de marcar feita</h3>
                  <p>{helpContent.recommendation}</p>
                </section>
              </div>
              <div className="modal-footer">
                <button type="button" className="secondary-button" onClick={() => setHelpTask(null)}>
                  Fechar
                </button>
                <button
                  type="button"
                  className="primary-button"
                  onClick={() => {
                    const task = helpTask;
                    setHelpTask(null);
                    openMaintenanceDoneModal(task);
                  }}
                >
                  <CheckCircle2 size={15} />
                  Marcar feita
                </button>
              </div>
            </div>
          </div>
        ) : null}

    </>
  );
}

type MaintenanceHelpContent = {
  howTo: string[];
  why: string;
  prevents: string[];
  recommendation: string;
};

function maintenanceHelpContent(task: MaintenanceTaskRecord): MaintenanceHelpContent {
  if (task.maintenance_help) {
    return {
      howTo: task.maintenance_help.how_to,
      why: task.maintenance_help.why,
      prevents: task.maintenance_help.prevents,
      recommendation: task.maintenance_help.recommendation,
    };
  }
  const fallback = genericMaintenanceHelp(task);
  return {
    howTo: fallback.howTo,
    why: fallback.why,
    prevents: fallback.prevents,
    recommendation: fallback.recommendation,
  };
}

function genericMaintenanceHelp(task: MaintenanceTaskRecord): MaintenanceHelpContent {
  return {
    howTo: [
      `Inspecione ${task.component} com a impressora parada e em condição segura.`,
      "Procure sujeira, folga, desgaste, ruído, atrito, cabo solto ou sinal de aquecimento.",
      "Corrija apenas o que for claro e reversível; se houver dúvida, registre uma nota em vez de forçar ajuste.",
      "Faça uma validação curta antes de iniciar uma impressão longa.",
    ],
    why: `Esta rotina mantém ${task.component} previsível e reduz falhas acumuladas que aparecem só durante impressões longas.`,
    prevents: ["Falhas intermitentes difíceis de reproduzir.", "Desgaste acelerado por falta de inspeção.", "Perda de tempo em diagnóstico depois que a peça já falhou."],
    recommendation: "Marque como feita quando a inspeção estiver concluída e não houver pendência crítica.",
  };
}
