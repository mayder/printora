import { CheckCircle2, X } from "lucide-react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";
import type { MaintenanceEventRecord } from "../../types";

type MaintenanceFreeModalProps = ScreenPropsFor<
  | "formatHours"
  | "formatLocalDateTime"
  | "loading"
  | "maintenanceComponent"
  | "maintenanceEventType"
  | "maintenanceFreeIntervalKind"
  | "maintenanceFreeIntervalValue"
  | "maintenanceFreeModalOpen"
  | "maintenanceFreeReminderEnabled"
  | "maintenanceHoursDisabledMessage"
  | "maintenanceNotes"
  | "maintenancePrintHours"
  | "maintenancePrintHoursAvailable"
  | "maintenanceTitle"
  | "selectedPrinter"
  | "setMaintenanceComponent"
  | "setMaintenanceEventType"
  | "setMaintenanceFreeIntervalKind"
  | "setMaintenanceFreeIntervalValue"
  | "setMaintenanceFreeModalOpen"
  | "setMaintenanceFreeReminderEnabled"
  | "setMaintenanceNotes"
  | "setMaintenanceTitle"
  | "submitMaintenanceFreeEvent"
>;

export function MaintenanceFreeModal(props: MaintenanceFreeModalProps) {
  const {
    formatHours,
    formatLocalDateTime,
    loading,
    maintenanceComponent,
    maintenanceEventType,
    maintenanceFreeIntervalKind,
    maintenanceFreeIntervalValue,
    maintenanceFreeModalOpen,
    maintenanceFreeReminderEnabled,
    maintenanceHoursDisabledMessage,
    maintenanceNotes,
    maintenancePrintHours,
    maintenancePrintHoursAvailable,
    maintenanceTitle,
    selectedPrinter,
    setMaintenanceComponent,
    setMaintenanceEventType,
    setMaintenanceFreeIntervalKind,
    setMaintenanceFreeIntervalValue,
    setMaintenanceFreeModalOpen,
    setMaintenanceFreeReminderEnabled,
    setMaintenanceNotes,
    setMaintenanceTitle,
    submitMaintenanceFreeEvent,
  } = props;

  if (!maintenanceFreeModalOpen) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Registro livre de manutenção">
      <div className="modal-card maintenance-modal-card">
        <div className="modal-header">
          <div>
            <h2>Registro livre</h2>
            <p>{selectedPrinter?.name ?? "Impressora"} · {formatLocalDateTime(new Date())}</p>
          </div>
          <button type="button" className="ghost-button" onClick={() => setMaintenanceFreeModalOpen(false)}>
            <X size={16} />
            Fechar
          </button>
        </div>
        <form className="maintenance-modal-form" onSubmit={(event) => void submitMaintenanceFreeEvent(event)}>
          <div className="maintenance-selected-printer">
            <span>Impressora selecionada</span>
            <strong>{selectedPrinter?.name ?? "Impressora"}</strong>
            <small>{selectedPrinter?.moonraker_url ?? "-"}</small>
          </div>
          <div className="form-grid two-columns">
            <label className="form-field">
              <span>Tipo</span>
              <select
                value={maintenanceEventType}
                onChange={(event) => setMaintenanceEventType(event.target.value as MaintenanceEventRecord["event_type"])}
                required
              >
                <option value="" disabled>
                  Selecione o tipo
                </option>
                <option value="maintenance">manutenção</option>
                <option value="failure">falha</option>
                <option value="adjustment">ajuste</option>
                <option value="note">nota</option>
              </select>
            </label>
            <label className="form-field">
              <span>Componente</span>
              <input value={maintenanceComponent} onChange={(event) => setMaintenanceComponent(event.target.value)} required />
            </label>
          </div>
          <label className="form-field">
            <span>Título</span>
            <input value={maintenanceTitle} onChange={(event) => setMaintenanceTitle(event.target.value)} required />
          </label>
          <label className="form-field">
            <span>Notas</span>
            <textarea value={maintenanceNotes} onChange={(event) => setMaintenanceNotes(event.target.value)} />
          </label>
          <label className="inline-check maintenance-no-reminder">
            <input
              type="checkbox"
              checked={maintenanceFreeReminderEnabled}
              onChange={(event) => {
                setMaintenanceFreeReminderEnabled(event.target.checked);
                if (!event.target.checked) {
                  setMaintenanceFreeIntervalValue("");
                }
              }}
            />
            Criar lembrete recorrente
          </label>
          {maintenanceFreeReminderEnabled ? (
            <div className="form-grid two-columns">
              <label className="form-field">
                <span>Lembrar por</span>
                <select
                  value={maintenanceFreeIntervalKind}
                  onChange={(event) => {
                    const value = event.target.value as "days" | "print_hours";
                    if (value === "print_hours" && !maintenancePrintHoursAvailable) {
                      return;
                    }
                    setMaintenanceFreeIntervalKind(value);
                  }}
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
                  max={maintenanceFreeIntervalKind === "days" ? "3650" : "100000"}
                  step={maintenanceFreeIntervalKind === "days" ? "1" : "0.1"}
                  value={maintenanceFreeIntervalValue}
                  onChange={(event) => setMaintenanceFreeIntervalValue(event.target.value)}
                  required={maintenanceFreeReminderEnabled}
                />
              </label>
            </div>
          ) : null}
          <p className="maintenance-modal-hint">
            {maintenancePrintHoursAvailable
              ? `Horas atuais de impressão: ${formatHours(maintenancePrintHours!.total_print_hours ?? 0)}.`
              : `Sem lembrete recorrente, o registro fica apenas no histórico. ${maintenanceHoursDisabledMessage}`}
          </p>
          <div className="modal-footer">
            <button type="button" className="ghost-button" onClick={() => setMaintenanceFreeModalOpen(false)}>
              <X size={16} />
              Cancelar
            </button>
            <button type="submit" className="primary-button" disabled={loading || !maintenanceEventType || !maintenanceComponent.trim() || !maintenanceTitle.trim() || (maintenanceFreeReminderEnabled && maintenanceFreeIntervalKind === "print_hours" && !maintenancePrintHoursAvailable)}>
              <CheckCircle2 size={16} />
              Salvar registro
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
