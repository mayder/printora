import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react";
import type { ConfirmDialogState } from "../../types";

type ConfirmDialogModalProps = {
  confirmDialog: ConfirmDialogState;
  resolveConfirmDialog: (confirmed: boolean) => void;
};

const toneIcons = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: AlertTriangle,
};

export function ConfirmDialogModal({ confirmDialog, resolveConfirmDialog }: ConfirmDialogModalProps) {
  if (!confirmDialog.open) {
    return null;
  }
  const Icon = toneIcons[confirmDialog.tone];
  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={confirmDialog.title}>
      <div className={`modal-card confirm-dialog-card ${confirmDialog.tone}`}>
        <div className="modal-header">
          <div>
            <h2>
              <Icon size={20} />
              {confirmDialog.title}
            </h2>
            <p>{confirmDialog.detail}</p>
          </div>
          <button type="button" className="ghost-button" onClick={() => resolveConfirmDialog(false)}>
            <X size={16} />
            Fechar
          </button>
        </div>
        {confirmDialog.evidence ? <div className="confirm-dialog-evidence">{confirmDialog.evidence}</div> : null}
        <div className="confirm-dialog-actions">
          <button type="button" className="secondary-button" onClick={() => resolveConfirmDialog(false)}>
            {confirmDialog.cancelLabel}
          </button>
          <button type="button" className={confirmDialog.tone === "danger" ? "danger-button" : "primary-button"} onClick={() => resolveConfirmDialog(true)}>
            {confirmDialog.confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
