import { AlertTriangle, Code2, Scale, ShieldCheck } from "lucide-react";
import type { ScreenPropsFor } from "./ScreenProps";

type LicenseScreenProps = ScreenPropsFor<"setActiveSection">;

export function LicenseScreen({ setActiveSection }: LicenseScreenProps) {
  return (
    <>
      <section className="panel panel-section panel-license license-hero">
        <div>
          <span className="about-kicker">Licença open source</span>
          <h2>Printora é distribuído sob a licença MIT.</h2>
          <p>
            Você pode usar, copiar, modificar, publicar e distribuir o projeto, desde que mantenha o aviso de copyright e a licença. O software é
            fornecido sem garantia de funcionamento, adequação ou responsabilidade por danos.
          </p>
        </div>
        <Scale size={54} />
      </section>

      <section className="panel panel-section panel-license license-grid-panel">
        <article>
          <ShieldCheck size={22} />
          <strong>Permissões</strong>
          <p>Uso pessoal ou comercial, cópia, modificação, distribuição e sublicenciamento, conforme a licença MIT.</p>
        </article>
        <article>
          <AlertTriangle size={22} />
          <strong>Sem garantia</strong>
          <p>O Printora é entregue “como está”. O usuário assume a responsabilidade por validar qualquer uso em impressoras, firmware e ambiente local.</p>
        </article>
        <article>
          <Code2 size={22} />
          <strong>Projeto público</strong>
          <p>
            Repositório oficial:{" "}
            <a href="https://github.com/mayder/printora" target="_blank" rel="noreferrer">
              github.com/mayder/printora
            </a>
          </p>
        </article>
      </section>

      <section className="panel panel-section panel-license license-text">
        <h2>Resumo Operacional</h2>
        <p>
          O Printora trabalha com diagnóstico, histórico, backup, manutenção e planejamento de firmware. Mesmo com fluxos conservadores, qualquer ação
          ligada a Klipper, Moonraker, systemd, firmware, MCU, EBB ou arquivos de configuração deve ser revisada antes de execução real.
        </p>
        <p>
          Nada nesta tela substitui leitura da licença no arquivo <code>LICENSE</code> do repositório. Para uso empresarial, distribuição pública ou
          produto derivado, revise a licença com assessoria jurídica própria.
        </p>
        <div className="panel-actions">
          <button type="button" className="secondary-button" onClick={() => setActiveSection("about")}>
            Voltar para Sobre
          </button>
          <a className="primary-button license-link-button" href="https://github.com/mayder/printora" target="_blank" rel="noreferrer">
            <Code2 size={16} />
            Abrir GitHub
          </a>
        </div>
      </section>
    </>
  );
}
