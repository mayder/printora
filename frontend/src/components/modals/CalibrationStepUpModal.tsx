import { KeyRound, X } from "lucide-react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

type CalibrationStepUpModalProps = ScreenPropsFor<
  | "authUser"
  | "calibrationStepUpBusy"
  | "calibrationStepUpCode"
  | "calibrationStepUpError"
  | "calibrationStepUpOpen"
  | "calibrationStepUpPassword"
  | "loading"
  | "setCalibrationStepUpCode"
  | "setCalibrationStepUpOpen"
  | "setCalibrationStepUpPassword"
  | "submitCalibrationStepUp"
>;

export function CalibrationStepUpModal(props: CalibrationStepUpModalProps) {
  const {
    authUser,
    calibrationStepUpBusy,
    calibrationStepUpCode,
    calibrationStepUpError,
    calibrationStepUpOpen,
    calibrationStepUpPassword,
    loading,
    setCalibrationStepUpCode,
    setCalibrationStepUpOpen,
    setCalibrationStepUpPassword,
    submitCalibrationStepUp,
  } = props;
  if (!calibrationStepUpOpen) {
    return null;
  }
  const usesMfa = Boolean(authUser?.mfa_enabled);
  const canSubmit = usesMfa ? calibrationStepUpCode.trim().length > 0 : calibrationStepUpPassword.trim().length > 0;

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Autorizar ação crítica">
      <div className="modal-card confirm-dialog-card calibration-step-up-card warning">
        <div className="modal-header">
          <div>
            <h2>
              <KeyRound size={20} />
              Autorizar ação crítica
            </h2>
            <p>Confirme sua identidade para enviar o SAVE_CONFIG para a impressora.</p>
          </div>
          <button type="button" className="ghost-button" onClick={() => setCalibrationStepUpOpen(false)}>
            <X size={16} />
            Fechar
          </button>
        </div>
        <label>
          <span>{usesMfa ? "Código 2FA" : "Senha atual da conta"}</span>
          <input
            value={usesMfa ? calibrationStepUpCode : calibrationStepUpPassword}
            onChange={(event) => {
              if (usesMfa) {
                setCalibrationStepUpCode(event.target.value);
              } else {
                setCalibrationStepUpPassword(event.target.value);
              }
            }}
            type={usesMfa ? "text" : "password"}
            inputMode={usesMfa ? "numeric" : undefined}
            autoComplete={usesMfa ? "one-time-code" : "current-password"}
            autoFocus
          />
        </label>
        {calibrationStepUpError ? <p className="form-error">{calibrationStepUpError}</p> : null}
        <div className="confirm-dialog-actions">
          <button type="button" className="secondary-button" onClick={() => setCalibrationStepUpOpen(false)}>
            Cancelar
          </button>
          <button
            type="button"
            className="primary-button"
            onClick={() => void submitCalibrationStepUp()}
            disabled={loading || calibrationStepUpBusy || !canSubmit}
          >
            {calibrationStepUpBusy ? "Autorizando" : "Autorizar e continuar"}
          </button>
        </div>
      </div>
    </div>
  );
}
