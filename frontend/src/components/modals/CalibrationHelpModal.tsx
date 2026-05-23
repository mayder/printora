import { X } from "lucide-react";
import type { ScreenPropsFor } from "../../screens/ScreenProps";

type CalibrationHelpModalProps = ScreenPropsFor<
  | "calibrationHelpTest"
  | "setCalibrationHelpTestKey"
>;

export function CalibrationHelpModal(props: CalibrationHelpModalProps) {
  const { calibrationHelpTest, setCalibrationHelpTestKey } = props;

  if (!calibrationHelpTest) {
    return null;
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={`Ajuda de ${calibrationHelpTest.title}`}>
      <div className="modal-card test-modal-card">
        <div className="modal-header">
          <div>
            <h2>{calibrationHelpTest.title}</h2>
            <p>{calibrationHelpTest.objective}</p>
          </div>
          <button type="button" className="icon-button" onClick={() => setCalibrationHelpTestKey(null)} aria-label="Fechar ajuda">
            <X size={18} />
          </button>
        </div>
        <div className="test-help-grid">
          <section>
            <strong>Antes de começar</strong>
            <ol>
              {calibrationHelpTest.prerequisites.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
          </section>
          <section>
            <strong>Sucesso esperado</strong>
            <ol>
              {calibrationHelpTest.success_criteria.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
          </section>
        </div>
        {calibrationHelpTest.gcode.length ? <pre>{calibrationHelpTest.gcode.join("\n")}</pre> : null}
        <div className="modal-footer">
          <button type="button" className="secondary-button" onClick={() => setCalibrationHelpTestKey(null)}>
            Fechar
          </button>
        </div>
      </div>
    </div>
  );
}
