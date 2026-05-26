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

  const printsTest = ["primeira_camada", "material", "extrusao", "qualidade", "dimensional"].includes(calibrationHelpTest.category);
  const useLabel = printsTest ? "Imprime peça ou padrão de teste" : calibrationHelpTest.gcode.length ? "Movimenta ou aquece sem imprimir peça" : "Inspeção ou registro manual";
  const modeDetail = calibrationHelpTest.gcode.length
    ? "Abre confirmação presencial antes de enviar comandos. Revise o G-code, confira a impressora e mantenha operador presente."
    : "Não envia comandos para a impressora. Use para registrar evidência, observação ou ajuste feito manualmente.";
  const expectedBenefit = calibrationHelpTest.notes || "Reduz tentativa e erro, deixa histórico comparável e ajuda a decidir o próximo ajuste com base em evidência.";
  const whyItMatters = printsTest
    ? "Ajuda a validar o comportamento real do material em uma impressão controlada antes de usar um modelo importante."
    : calibrationHelpTest.gcode.length
      ? "Confirma que a máquina responde de forma previsível antes de etapas mais sensíveis de calibração ou impressão."
      : "Garante que a base mecânica e visual esteja coerente antes de executar comandos ou imprimir testes.";

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
          <section className="test-help-wide">
            <strong>O que vai fazer</strong>
            <p>{calibrationHelpTest.objective}</p>
            <p>{modeDetail}</p>
          </section>
          <section>
            <strong>Quando usar</strong>
            <p>{whyItMatters}</p>
          </section>
          <section>
            <strong>Vantagem prática</strong>
            <p>{expectedBenefit}</p>
          </section>
          <section>
            <strong>Classificação</strong>
            <dl className="test-help-facts">
              <div>
                <dt>Uso</dt>
                <dd>{useLabel}</dd>
              </div>
              <div>
                <dt>Execução</dt>
                <dd>{calibrationHelpTest.gcode.length ? "Com G-code revisado" : "Manual"}</dd>
              </div>
              <div>
                <dt>Risco</dt>
                <dd>{calibrationHelpTest.risk_level}</dd>
              </div>
            </dl>
          </section>
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
