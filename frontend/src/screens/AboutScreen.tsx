import { Code2, Cpu, Globe2, Languages, ShieldCheck, Sparkles, Wrench } from "lucide-react";
import type { ScreenPropsFor } from "./ScreenProps";

type AboutScreenProps = ScreenPropsFor<"setActiveSection">;

function InstagramIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        fill="currentColor"
        d="M7.8 2h8.4A5.8 5.8 0 0 1 22 7.8v8.4a5.8 5.8 0 0 1-5.8 5.8H7.8A5.8 5.8 0 0 1 2 16.2V7.8A5.8 5.8 0 0 1 7.8 2Zm0 2A3.8 3.8 0 0 0 4 7.8v8.4A3.8 3.8 0 0 0 7.8 20h8.4a3.8 3.8 0 0 0 3.8-3.8V7.8A3.8 3.8 0 0 0 16.2 4H7.8Zm8.95 2.35a.9.9 0 1 1 0 1.8.9.9 0 0 1 0-1.8ZM12 7.15A4.85 4.85 0 1 1 12 16.85 4.85 4.85 0 0 1 12 7.15Zm0 2A2.85 2.85 0 1 0 12 14.85 2.85 2.85 0 0 0 12 9.15Z"
      />
    </svg>
  );
}

function LinkedinIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        fill="currentColor"
        d="M6.94 8.9H3.4V20h3.54V8.9ZM5.17 4a2.06 2.06 0 1 0 0 4.12A2.06 2.06 0 0 0 5.17 4Zm8.05 4.9H9.83V20h3.54v-5.5c0-1.45.27-2.86 2.08-2.86 1.78 0 1.8 1.67 1.8 2.95V20h3.54v-6.1c0-3-0.65-5.3-4.15-5.3-1.68 0-2.8.92-3.27 1.8h-.05V8.9Z"
      />
    </svg>
  );
}

function GithubIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path
        fill="currentColor"
        d="M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.2-3.37-1.2-.45-1.16-1.1-1.47-1.1-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.9 1.52 2.34 1.08 2.91.83.09-.65.35-1.08.63-1.33-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02A9.55 9.55 0 0 1 12 6.98c.85 0 1.7.11 2.5.34 1.9-1.29 2.74-1.02 2.74-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.86v2.76c0 .27.18.58.69.48A10 10 0 0 0 12 2Z"
      />
    </svg>
  );
}

const featureCards = [
  {
    icon: ShieldCheck,
    title: "Diagnóstico conservador",
    text: "Auditorias read-only, health check, snapshots e relatórios sanitizados para entender o ambiente antes de alterar qualquer coisa.",
  },
  {
    icon: Wrench,
    title: "Operação e manutenção",
    text: "Backups, diário de manutenção, histórico de Z-offset, CAN, calibração e acompanhamento por impressora cadastrada.",
  },
  {
    icon: Cpu,
    title: "Firmware em evolução",
    text: "O foco inicial é simplificar atualização e planejamento de firmware de MCU, EBB e placas relacionadas. O fluxo ainda está em implementação e teste.",
  },
  {
    icon: Globe2,
    title: "Caminho para nuvem",
    text: "A visão futura é uma versão online em que o usuário instala apenas um agente local, conectado por token único a uma API em nuvem.",
  },
];

const brandOptions = [
  { src: "/brand/printora-logo-horizontal-color.png", title: "Logo horizontal", detail: "Uso geral em páginas, README e apresentações.", tone: "light" },
  { src: "/brand/printora-logo-horizontal-dark-bg.png", title: "Logo para fundo escuro", detail: "Versão com contraste melhor para interfaces escuras." },
  { src: "/brand/printora-icon-app-color.png", title: "Ícone de app", detail: "Aplicativo, favicon, atalhos e instaladores." },
  { src: "/brand/printora-icon-symbol-color.png", title: "Símbolo", detail: "Uso compacto quando a marca já está contextualizada.", tone: "light" },
];

export function AboutScreen({ setActiveSection }: AboutScreenProps) {
  return (
    <>
      <section className="panel panel-section panel-about about-hero">
        <div className="about-hero-copy">
          <span className="about-kicker">Open source local para Klipper/Moonraker</span>
          <h2>Printora nasceu para tornar manutenção, diagnóstico e firmware mais simples, seguros e verificáveis.</h2>
          <p>
            Esta versão é sem custo e está em teste. O objetivo é entregar uma ferramenta local, conservadora e clara para quem precisa cuidar de
            impressoras 3D sem depender de tentativa cega, comandos perigosos ou documentação espalhada.
          </p>
          <div className="about-actions">
            <a className="social-button linkedin" href="https://www.linkedin.com/in/brenomayder/" target="_blank" rel="noreferrer">
              <LinkedinIcon />
              LinkedIn
            </a>
            <a className="social-button instagram" href="https://www.instagram.com/brenomayder" target="_blank" rel="noreferrer">
              <InstagramIcon />
              Instagram
            </a>
            <a className="social-button github" href="https://github.com/mayder/printora" target="_blank" rel="noreferrer">
              <GithubIcon />
              Projeto no GitHub
            </a>
          </div>
        </div>
        <aside className="about-profile">
          <img src="/brand/breno-mayder-profile.png" alt="Breno Mayder" />
          <div>
            <span>Idealizador</span>
            <strong>Breno Mayder</strong>
            <p>Software Architect com mais de 16 anos de experiência em desenvolvimento web, mobile, banco de dados e arquitetura de software.</p>
          </div>
        </aside>
      </section>

      <section className="panel panel-section panel-about about-story">
        <div className="panel-heading">
          <div>
            <h2>Por Que Fiz Este Projeto</h2>
            <p>
              O Printora vem da necessidade de transformar manutenção de impressoras Klipper em um fluxo mais objetivo: ler o estado real, registrar
              histórico, gerar evidências e reduzir risco antes de mexer em firmware, configuração ou operação.
            </p>
          </div>
        </div>
        <div className="about-story-grid">
          <div>
            <Sparkles size={22} />
            <strong>Experiência aplicada</strong>
            <p>
              Minha trajetória passa por PHP, C#, Dart/Flutter, Yii2, .NET MVC, MySQL, SQL Server, Oracle, sistemas web e aplicativos móveis. Essa
              base técnica orienta o Printora para simplicidade operacional, separação clara de responsabilidades e cuidado com dados locais.
            </p>
          </div>
          <div>
            <Code2 size={22} />
            <strong>Produto em evolução</strong>
            <p>
              Hoje o foco é uso local e seguro. No futuro, pretendo estudar uma versão online com agente instalado no ambiente do usuário, comunicação
              autenticada por token único e API em nuvem para acesso externo controlado.
            </p>
          </div>
          <div>
            <Languages size={22} />
            <strong>Próximo idioma</strong>
            <p>
              A interface está em português nesta fase inicial. Em breve, o sistema também deverá ter uma versão em inglês para facilitar uso e
              colaboração fora do Brasil.
            </p>
          </div>
        </div>
      </section>

      <section className="panel panel-section panel-about about-features">
        <div className="panel-heading">
          <div>
            <h2>Funcionalidades Em Destaque</h2>
            <p>As áreas atuais priorizam diagnóstico, histórico e operação segura antes de ações críticas.</p>
          </div>
        </div>
        <div className="about-feature-grid">
          {featureCards.map((feature) => {
            const Icon = feature.icon;
            return (
              <article key={feature.title} className="about-feature-card">
                <span>
                  <Icon size={20} />
                </span>
                <strong>{feature.title}</strong>
                <p>{feature.text}</p>
              </article>
            );
          })}
        </div>
      </section>

      <section className="panel panel-section panel-about about-brand">
        <div className="panel-heading">
          <div>
            <h2>Marca Printora</h2>
            <p>Algumas versões da identidade visual disponíveis no projeto para documentação, divulgação e uso em atalhos.</p>
          </div>
        </div>
        <div className="about-brand-grid">
          {brandOptions.map((option) => (
            <article key={option.title} className={`about-brand-card ${option.tone === "light" ? "light-preview" : ""}`}>
              <div>
                <img src={option.src} alt={option.title} />
              </div>
              <strong>{option.title}</strong>
              <p>{option.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="panel panel-section panel-about about-license-cta">
        <div>
          <h2>Licença E Responsabilidade</h2>
          <p>
            Quero que o Printora seja open source, mas também claro sobre limites: o software é fornecido sem garantia, e operações em impressoras,
            firmware e infraestrutura exigem revisão do usuário.
          </p>
        </div>
        <button type="button" className="primary-button" onClick={() => setActiveSection("license")}>
          <ShieldCheck size={16} />
          Ver licença
        </button>
      </section>
    </>
  );
}
