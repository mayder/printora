import { CheckCircle2, Timer, X } from "lucide-react";
import { Metric } from "../common";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

type MaintenanceDoneModalProps = ScreenPropsFor<
  | "formatHours"
  | "formatLocalDateTime"
  | "formatMaintenanceInterval"
  | "formatOptionalLocalDateTime"
  | "loading"
  | "maintenanceDoneDisableReminder"
  | "maintenanceDoneIntervalKind"
  | "maintenanceDoneIntervalValue"
  | "maintenanceDoneNotes"
  | "maintenanceDoneTask"
  | "maintenanceHoursDisabledMessage"
  | "maintenancePrintHours"
  | "maintenancePrintHoursAvailable"
  | "selectedPrinter"
  | "setMaintenanceDoneDisableReminder"
  | "setMaintenanceDoneIntervalKind"
  | "setMaintenanceDoneIntervalValue"
  | "setMaintenanceDoneNotes"
  | "setMaintenanceDoneTask"
  | "submitMaintenanceDone"
>;

export function MaintenanceDoneModal(props: MaintenanceDoneModalProps) {
  const {
    formatHours,
    formatLocalDateTime,
    formatMaintenanceInterval,
    formatOptionalLocalDateTime,
    loading,
    maintenanceDoneDisableReminder,
    maintenanceDoneIntervalKind,
    maintenanceDoneIntervalValue,
    maintenanceDoneNotes,
    maintenanceDoneTask,
    maintenanceHoursDisabledMessage,
    maintenancePrintHours,
    maintenancePrintHoursAvailable,
    selectedPrinter,
    setMaintenanceDoneDisableReminder,
    setMaintenanceDoneIntervalKind,
    setMaintenanceDoneIntervalValue,
    setMaintenanceDoneNotes,
    setMaintenanceDoneTask,
    submitMaintenanceDone,
  } = props;

  if (!maintenanceDoneTask) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Registrar ${maintenanceDoneTask.name}`}>
      <div className="modal-card maintenance-modal-card">
        <div className="modal-header">
          <div>
            <h2>{maintenanceDoneTask.name}</h2>
            <p>{selectedPrinter?.name ?? "Impressora"} · {formatLocalDateTime(new Date())}</p>
          </div>
          <button type="button" className="ghost-button" onClick={() => setMaintenanceDoneTask(null)}>
            <X size={16} />
            Fechar
          </button>
        </div>
        <form className="maintenance-modal-form" onSubmit={(event) => void submitMaintenanceDone(event)}>
          <div className="maintenance-selected-printer">
            <span>Impressora selecionada</span>
            <strong>{selectedPrinter?.name ?? "Impressora"}</strong>
            <small>{selectedPrinter?.moonraker_url ?? "-"}</small>
          </div>
          <div className="maintenance-modal-summary">
            <Metric label="Componente" value={maintenanceDoneTask.component} />
            <Metric label="Última" value={formatOptionalLocalDateTime(maintenanceDoneTask.last_done_at)} />
            <Metric label="Lembrete atual" value={maintenanceDoneTask.is_active ? formatMaintenanceInterval(maintenanceDoneTask) : "sem lembrete"} />
          </div>
          {maintenancePrintHoursAvailable ? (
            <div className="maintenance-print-hours-banner">
              <Timer size={16} />
              <span>Horas atuais de impressão</span>
              <strong>{formatHours(maintenancePrintHours!.total_print_hours ?? 0)}</strong>
            </div>
          ) : (
            <p className="maintenance-modal-hint">{maintenanceHoursDisabledMessage}</p>
          )}
          <label className="form-field">
            <span>Observação</span>
            <textarea
              value={maintenanceDoneNotes}
              onChange={(event) => setMaintenanceDoneNotes(event.target.value)}
              placeholder="O que foi feito, peça trocada, condição encontrada..."
            />
          </label>
          <p className="maintenance-modal-hint">
            Com o prazo preenchido, o Printora volta a avisar quando vencer. Se deixar vazio, esta rotina fica registrada e não gera novo lembrete.
          </p>
          <div className="form-grid two-columns">
            <label className="form-field">
              <span>Lembrar por</span>
              <select
                value={maintenanceDoneIntervalKind}
                onChange={(event) => {
                  const value = event.target.value as "days" | "print_hours";
                  if (value === "print_hours" && !maintenancePrintHoursAvailable) {
                    return;
                  }
                  setMaintenanceDoneIntervalKind(value);
                  setMaintenanceDoneDisableReminder(false);
                }}
                disabled={maintenanceDoneDisableReminder}
              >
                <option value="days">Dias</option>
                <option value="print_hours" disabled={!maintenancePrintHoursAvailable}>Horas de impressão</option>
              </select>
            </label>
            <label className="form-field">
              <span>Valor</span>
              <input
                type="number"
                min="1"
                max={maintenanceDoneIntervalKind === "days" ? "3650" : "100000"}
                step={maintenanceDoneIntervalKind === "days" ? "1" : "0.1"}
                value={maintenanceDoneIntervalValue}
                onChange={(event) => {
                  setMaintenanceDoneIntervalValue(event.target.value);
                  setMaintenanceDoneDisableReminder(false);
                }}
                placeholder="Vazio para nunca lembrar"
                disabled={maintenanceDoneDisableReminder}
              />
            </label>
          </div>
          <div className="form-grid two-columns">
            <label className="inline-check maintenance-no-reminder">
              <input
                type="checkbox"
                checked={maintenanceDoneDisableReminder || !maintenanceDoneIntervalValue.trim()}
                onChange={(event) => {
                  setMaintenanceDoneDisableReminder(event.target.checked);
                  if (event.target.checked) {
                    setMaintenanceDoneIntervalValue("");
                  }
                }}
              />
              Não lembrar de novo
            </label>
          </div>
          <div className="modal-footer">
            <button type="button" className="ghost-button" onClick={() => setMaintenanceDoneTask(null)}>
              <X size={16} />
              Cancelar
            </button>
            <button type="submit" className="primary-button" disabled={loading}>
              <CheckCircle2 size={16} />
              Confirmar manutenção
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
