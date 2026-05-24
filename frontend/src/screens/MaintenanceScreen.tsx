import { Metric } from "../components/common";
import type { ScreenPropsFor } from "./ScreenProps";

type MaintenanceScreenProps = ScreenPropsFor<
  | "CheckCircle2"
  | "Plus"
  | "Timer"
  | "Trash2"
  | "Undo2"
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
  | "maintenanceSummary"
  | "maintenanceTasks"
  | "nextMaintenanceTask"
  | "openMaintenanceDoneModal"
  | "openMaintenanceFreeModal"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setMaintenanceFilter"
  | "status"
  | "visibleMaintenanceTasks"
>;

export function MaintenanceScreen(props: MaintenanceScreenProps) {
  const {
    CheckCircle2,
    Plus,
    Timer,
    Trash2,
    Undo2,
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
    maintenanceSummary,
    maintenanceTasks,
    nextMaintenanceTask,
    openMaintenanceDoneModal,
    openMaintenanceFreeModal,
    selectedPrinter,
    selectedPrinterId,
    setMaintenanceFilter,
    status,
    visibleMaintenanceTasks,
  } = props;

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
                </div>
              </div>

              {visibleMaintenanceTasks.length === 0 ? (
                <div className="empty-maintenance-state">
                  <strong>Nenhuma rotina neste filtro.</strong>
                  <span>O catálogo padrão será carregado automaticamente para esta impressora.</span>
                </div>
              ) : null}

              <div className="maintenance-card-grid">
                {visibleMaintenanceTasks.map((task: any) => (
                  <article key={task.id} className={`maintenance-task-card ${task.is_active ? task.due_status : "inactive"}`}>
                    <div className="maintenance-task-card-header">
                      <span className={`status-pill ${task.is_active ? task.due_status : "inactive"}`}>{formatDueStatus(task)}</span>
                      <strong>{task.name}</strong>
                    </div>
                    <div className="maintenance-task-meta">
                      <span>{task.component}</span>
                      <span>{task.is_active ? formatMaintenanceInterval(task) : "Sem lembrete recorrente"}</span>
                      <span>Última: {formatOptionalLocalDateTime(task.last_done_at)}</span>
                      {task.interval_kind === "print_hours" && maintenancePrintHoursAvailable ? (
                        <>
                          <span>Base: {formatOptionalHours(task.last_done_print_hours)}</span>
                          <span>Atual: {formatOptionalHours(task.current_print_hours)}{task.current_print_hours_source === "cached" ? " · desatualizado" : ""}</span>
                          <span>{formatPrintHoursDueLine(task)}</span>
                        </>
                      ) : null}
                    </div>
                    <div className="maintenance-card-actions">
                      <button type="button" className="maintenance-done-button" onClick={() => openMaintenanceDoneModal(task)} disabled={loading}>
                        <CheckCircle2 size={14} />
                        Marcar feita
                      </button>
                      {task.last_done_at ? (
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
                    </div>
                  </article>
                ))}
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


    </>
  );
}
