import { AlertTriangle, CheckCircle2, Info, X } from "lucide-react";
import type { ToastRecord } from "../types";

type ToastViewportProps = {
  toasts: ToastRecord[];
  dismissToast: (toastId: number) => void;
};

const toneIcons = {
  info: Info,
  success: CheckCircle2,
  warning: AlertTriangle,
  danger: AlertTriangle,
};

export function ToastViewport({ toasts, dismissToast }: ToastViewportProps) {
  if (toasts.length === 0) {
    return null;
  }
  return (
    <div className="toast-viewport" aria-live="polite" aria-relevant="additions removals">
      {toasts.map((toast) => {
        const Icon = toneIcons[toast.tone];
        return (
          <div key={toast.id} className={`toast ${toast.tone}`}>
            <Icon size={17} />
            <div>
              <strong>{toast.title}</strong>
              {toast.detail ? <p>{toast.detail}</p> : null}
            </div>
            <button type="button" className="icon-button" onClick={() => dismissToast(toast.id)} aria-label="Fechar aviso">
              <X size={15} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
