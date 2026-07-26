import React from "react";
import { Accessibility, ArrowLeft, Download, RefreshCw, Search } from "lucide-react";
import { AccessibilityPreferencesForm } from "../components/accessibility/AccessibilityPreferencesForm";
import { useAccessibilityCenter } from "../hooks/domains/useAccessibilityCenter";
import { downloadTactileArtifact } from "../services/accessibilityTactile";
import type { AccessibilityCapability } from "../types/accessibility";
import "../styles/accessibility.css";


export function AccessibilityScreen() {
  const center = useAccessibilityCenter();
  const [query, setQuery] = React.useState("");

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

  const normalized = query.trim().toLocaleLowerCase("pt-BR");
  const filtered = center.catalog.capabilities.filter((capability) =>
    `${capability.title} ${capability.capability_id} ${capability.screen_id}`
      .toLocaleLowerCase("pt-BR")
      .includes(normalized),
  );
  return (
    <section className="accessibility-screen" data-testid="accessibility-screen">
      <Header offline={center.offline} revision={center.preferences.revision} />
      <div className="a11y-toolbar">
        <label>
          <span className="sr-only">Buscar por nome ou capacidade</span>
          <Search size={16} aria-hidden="true" />
          <input
            type="search"
            placeholder="Buscar por nome ou capacidade"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <strong>{filtered.length} de 8 famílias</strong>
      </div>
      {filtered.length === 0 ? (
        <div className="a11y-state">
          <h3>Nenhum item encontrado</h3>
          <p>A busca não altera suas preferências.</p>
          <button type="button" onClick={() => setQuery("")}>Limpar filtros</button>
        </div>
      ) : (
        <div className="a11y-grid">
          {filtered.map((capability) => (
            <article className="a11y-card" key={capability.capability_id}>
              <div className="a11y-card-heading">
                <span>{capability.capability_id}</span>
                <span>{capability.screen_id}</span>
              </div>
              <h3>{capability.title}</h3>
              <p>{capability.summary}</p>
              <small>{capability.com_ids[0]}–{capability.com_ids.at(-1)}</small>
              <button
                type="button"
                className="primary-button"
                aria-label={`Detalhe de ${capability.title}`}
                onClick={() => center.navigate(capability.route, "detail")}
              >
                Ver detalhe
              </button>
            </article>
          ))}
        </div>
      )}
      <div className="a11y-live" aria-live="polite" aria-atomic="true">
        {center.saveStatus === "saved" ? "Preferências sincronizadas." : ""}
      </div>
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
  return (
    <section className="accessibility-screen" data-testid="accessibility-screen">
      <BackButton onClick={() => center.navigate(capability.route)} />
      <header className="a11y-detail-header">
        <span className="a11y-eyebrow">{capability.capability_id} · {capability.screen_id}</span>
        <h2>{capability.title}</h2>
        <p>{capability.summary}</p>
      </header>
      <div className="a11y-detail-grid">
        <article>
          <h3>Evidências atribuídas</h3>
          <ul>{capability.evidence.map((item) => <li key={item}>{item}</li>)}</ul>
          <p><strong>Contrato:</strong> versão 1.x, autenticado e isolado por usuário.</p>
          <p><strong>Rollback:</strong> release N-1 preserva preferências e não executa limpeza.</p>
        </article>
        <article aria-labelledby="media-alternatives-title">
          <h3 id="media-alternatives-title">Alternativas equivalentes</h3>
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
        Abrir editor de preferências
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
        <span className="a11y-eyebrow">Preferências pessoais · revisão {center.preferences?.revision ?? 0}</span>
        <h2>{capability.title}</h2>
        <p>O formulário aplica uma prévia local e sincroniza somente após salvar.</p>
      </header>
      <AccessibilityPreferencesForm
        values={center.draft}
        saving={center.saving}
        offline={center.offline}
        onChange={center.updateDraft}
        onSave={() => void center.save()}
      />
      <div
        className="a11y-live"
        role="status"
        aria-live={center.draft.screen_reader_announcements ? "polite" : "off"}
        aria-atomic="true"
      >
        {center.saveStatus === "saved" ? "Preferências sincronizadas." : null}
        {center.saveStatus === "conflict"
          ? "Conflito: recarregue as preferências antes de salvar novamente."
          : null}
        {center.error ? `Falha: ${center.error}` : null}
      </div>
    </section>
  );
}

function Header({ offline, revision }: { offline: boolean; revision: number }) {
  return (
    <header className="a11y-hero">
      <div>
        <span className="a11y-eyebrow"><Accessibility size={16} /> Participação equivalente</span>
        <h2>Central de acessibilidade</h2>
        <p>Configure visual, movimento, navegação, mídia, compreensão e alternativas 3D.</p>
      </div>
      <div className="a11y-sync-status" role="status">
        <strong>{offline ? "Offline" : "Sincronizado"}</strong>
        <span>Revisão {revision}</span>
      </div>
    </header>
  );
}

function BackButton({ onClick }: { onClick: () => void }) {
  return (
    <button type="button" className="secondary-button" onClick={onClick}>
      <ArrowLeft size={16} /> Voltar
    </button>
  );
}
