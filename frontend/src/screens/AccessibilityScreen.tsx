import React from "react";
import { Accessibility, ArrowLeft, Download, RefreshCw } from "lucide-react";
import { AccessibilityPreferencesForm } from "../components/accessibility/AccessibilityPreferencesForm";
import { useAccessibilityCenter } from "../hooks/domains/useAccessibilityCenter";
import { downloadTactileArtifact } from "../services/accessibilityTactile";
import type { AccessibilityCapability } from "../types/accessibility";
import "../styles/accessibility.css";

type CapabilityPresentation = {
  title: string;
  summary: string;
  benefits: string[];
};

const capabilityPresentations: Record<string, CapabilityPresentation> = {
  "conformidade-continua-com-wcag-e-testes-com-usuarios": {
    title: "Usar o Printora com confiança",
    summary: "As telas são verificadas para funcionar com diferentes necessidades e formas de uso.",
    benefits: [
      "Textos e controles com contraste adequado",
      "Telas verificadas com leitores e ferramentas de apoio",
      "Validação com pessoas que usam recursos de acessibilidade",
    ],
  },
  "navegacao-integral-por-teclado-switch-e-voz": {
    title: "Navegar sem usar o mouse",
    summary: "Use teclado, comandos de voz ou dispositivos adaptados para acessar todas as ações.",
    benefits: ["Ordem clara ao pressionar Tab", "Botões fáceis de alcançar", "Ações que não dependem de gestos"],
  },
  "leitor-de-tela-com-semantica-e-anuncios-de-estado": {
    title: "Ouvir o que acontece na tela",
    summary: "Leitores de tela informam onde você está, o que pode fazer e o resultado de cada ação.",
    benefits: ["Áreas da página identificadas", "Botões e campos com nomes claros", "Avisos de sucesso e erro lidos em voz alta"],
  },
  "contraste-zoom-reducao-de-movimento-e-temas-adaptativos": {
    title: "Melhorar a leitura e o conforto visual",
    summary: "Ajuste cores, tamanho do texto e movimentos sem perder informações ou ações.",
    benefits: ["Contraste mais forte", "Texto ampliado", "Animações reduzidas"],
  },
  "legendas-transcricoes-e-audiodescricao-para-midia": {
    title: "Acompanhar vídeos e áudios",
    summary: "Use legendas, textos e audiodescrição para compreender conteúdos de mídia.",
    benefits: ["Legendas disponíveis", "Conteúdo em texto", "Descrição do que aparece na imagem"],
  },
  "linguagem-simples-e-modo-de-baixa-carga-cognitiva": {
    title: "Simplificar textos e telas",
    summary: "Reduza a quantidade de informação por vez e use instruções mais diretas.",
    benefits: ["Frases mais diretas", "Etapas menores", "Orientação clara quando algo dá errado"],
  },
  "visualizacao-3d-com-alternativa-textual-e-tatil-exportavel": {
    title: "Entender modelos 3D de outras formas",
    summary: "Consulte uma descrição em texto ou gere uma versão tátil quando a imagem 3D não for suficiente.",
    benefits: ["Descrição da forma", "Tamanho e posição explicados", "Arquivo para leitura tátil"],
  },
  "central-de-preferencias-acessiveis-sincronizada": {
    title: "Manter suas escolhas em outros dispositivos",
    summary: "As preferências salvas acompanham sua conta quando você troca de computador ou celular.",
    benefits: ["Preferências ligadas à sua conta", "Sincronização entre dispositivos", "Aviso antes de substituir mudanças recentes"],
  },
};

function presentCapability(capability: AccessibilityCapability): CapabilityPresentation {
  return capabilityPresentations[capability.slug] ?? {
    title: capability.title,
    summary: capability.summary,
    benefits: capability.evidence,
  };
}


export function AccessibilityScreen() {
  const center = useAccessibilityCenter();

  if (center.loading) {
    return (
      <section className="accessibility-screen a11y-state" aria-live="polite">
        <span className="a11y-eyebrow">Acessibilidade</span>
        <h2>Carregando preferências e critérios</h2>
      </section>
    );
  }
  if (center.error && !center.catalog) {
    return (
      <section className="accessibility-screen a11y-state" role="alert">
        <span className="a11y-eyebrow">Falha recuperável</span>
        <h2>Não foi possível abrir a central</h2>
        <p>{center.error}</p>
        <button type="button" className="primary-button" onClick={() => void center.load()}>
          <RefreshCw size={16} /> Tentar novamente
        </button>
      </section>
    );
  }
  if (!center.catalog || !center.draft || !center.preferences) {
    return (
      <section className="accessibility-screen a11y-state">
        <h2>Nenhuma configuração disponível</h2>
        <button type="button" onClick={() => void center.load()}>Recarregar</button>
      </section>
    );
  }

  const selected = center.catalog.capabilities.find(
    (capability) => capability.slug === center.route.slug,
  );
  if (selected && center.route.mode === "detail") {
    return <CapabilityDetail capability={selected} center={center} />;
  }
  if (selected && center.route.mode === "edit") {
    return <CapabilityEditor capability={selected} center={center} />;
  }

  return (
    <section className="accessibility-screen" data-testid="accessibility-screen">
      <Header offline={center.offline} />
      <section className="a11y-settings" aria-labelledby="accessibility-settings-title">
        <div className="a11y-section-heading">
          <h3 id="accessibility-settings-title">Escolha como quer usar o Printora</h3>
          <p>Você pode alterar estas opções a qualquer momento. As mudanças acompanham sua conta.</p>
        </div>
        <AccessibilityPreferencesForm
          values={center.draft}
          saving={center.saving}
          offline={center.offline}
          onChange={center.updateDraft}
          onSave={() => void center.save()}
        />
      </section>
      <details className="a11y-resources">
        <summary>Conheça os recursos de acessibilidade</summary>
        <p>Veja como o Printora ajuda em diferentes formas de navegação, leitura e compreensão.</p>
        <div className="a11y-grid">
          {center.catalog.capabilities.map((capability) => {
            const presentation = presentCapability(capability);
            return (
              <article className="a11y-card" key={capability.slug}>
                <h3>{presentation.title}</h3>
                <p>{presentation.summary}</p>
                <button
                  type="button"
                  className="secondary-button"
                  aria-label={`Saiba mais sobre ${presentation.title}`}
                  onClick={() => center.navigate(capability.route, "detail")}
                >
                  Saiba mais
                </button>
              </article>
            );
          })}
        </div>
      </details>
      <SaveFeedback center={center} />
    </section>
  );
}

type Center = ReturnType<typeof useAccessibilityCenter>;

function CapabilityDetail({
  capability,
  center,
}: {
  capability: AccessibilityCapability;
  center: Center;
}) {
  const presentation = presentCapability(capability);
  return (
    <section className="accessibility-screen" data-testid="accessibility-screen">
      <BackButton onClick={() => center.navigate(capability.route)} />
      <header className="a11y-detail-header">
        <span className="a11y-eyebrow">Recurso de acessibilidade</span>
        <h2>{presentation.title}</h2>
        <p>{presentation.summary}</p>
      </header>
      <div className="a11y-detail-grid">
        <article>
          <h3>Como este recurso ajuda</h3>
          <ul>{presentation.benefits.map((item) => <li key={item}>{item}</li>)}</ul>
        </article>
        <article aria-labelledby="media-alternatives-title">
          <h3 id="media-alternatives-title">Exemplo acessível</h3>
          <figure>
            <div className="a11y-media-sample" role="img" aria-label="Peça retangular com botão circular no canto inferior direito">
              <span aria-hidden="true">3D</span>
            </div>
            <figcaption>
              Peça retangular horizontal; linhas de conteúdo à esquerda e ação circular no canto inferior direito.
            </figcaption>
          </figure>
          <details>
            <summary>Transcrição e audiodescrição</summary>
            <p>A amostra apresenta primeiro o contorno, depois duas linhas e por fim a ação circular.</p>
          </details>
          <button
            type="button"
            onClick={() => downloadTactileArtifact(center.draft?.tactile_format ?? "svg")}
          >
            <Download size={16} /> Exportar alternativa tátil
          </button>
        </article>
      </div>
      <button
        type="button"
        className="primary-button"
        onClick={() => center.navigate(capability.route, "edit")}
      >
        Ajustar minhas preferências
      </button>
    </section>
  );
}

function CapabilityEditor({
  capability,
  center,
}: {
  capability: AccessibilityCapability;
  center: Center;
}) {
  if (!center.draft) return null;
  return (
    <section className="accessibility-screen" data-testid="accessibility-screen">
      <BackButton onClick={() => center.navigate(capability.route, "detail")} />
      <header className="a11y-detail-header">
        <span className="a11y-eyebrow">Preferências pessoais</span>
        <h2>Ajustar acessibilidade</h2>
        <p>Escolha as opções que deixam o Printora mais confortável para você.</p>
      </header>
      <AccessibilityPreferencesForm
        values={center.draft}
        saving={center.saving}
        offline={center.offline}
        onChange={center.updateDraft}
        onSave={() => void center.save()}
      />
      <SaveFeedback center={center} />
    </section>
  );
}

function Header({ offline }: { offline: boolean }) {
  return (
    <header className="a11y-hero">
      <div>
        <span className="a11y-eyebrow"><Accessibility size={16} /> Preferências pessoais</span>
        <h2>Acessibilidade</h2>
        <p>Adapte a aparência, a navegação e o conteúdo às suas necessidades.</p>
      </div>
      <div className="a11y-sync-status" role="status">
        <strong>{offline ? "Sem conexão" : "Preferências sincronizadas"}</strong>
        <span>{offline ? "Você poderá salvar quando a conexão voltar." : "Válidas em seus dispositivos."}</span>
      </div>
    </header>
  );
}

function SaveFeedback({ center }: { center: Center }) {
  return (
    <div
      className="a11y-live"
      role="status"
      aria-live={center.draft?.screen_reader_announcements ? "polite" : "off"}
      aria-atomic="true"
    >
      {center.saveStatus === "saved" ? "Preferências sincronizadas." : null}
      {center.saveStatus === "conflict"
        ? "Suas preferências foram alteradas em outro dispositivo. Recarregue a página antes de salvar."
        : null}
      {center.error ? `Não foi possível concluir: ${center.error}` : null}
    </div>
  );
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" className="secondary-button" onClick={onClick}>
      <ArrowLeft size={16} /> Voltar
    </button>
  );
}
