import React from "react";
import {
  ArrowLeft,
  Check,
  ChevronRight,
  LayoutGrid,
  ListFilter,
  Pencil,
  RefreshCw,
  Rows3,
  Search,
  TableProperties,
} from "lucide-react";
import { DesignStatePanel } from "../components/design-system/DesignStatePanel";
import { useDesignSystemLab } from "../hooks/domains/useDesignSystemLab";
import type {
  DesignCapability,
  DesignCollectionMode,
  DesignDensity,
  DesignState,
} from "../types/designSystem";
import "../styles/design-system.css";


const DENSITY_LABELS: Record<DesignDensity, string> = {
  workshop: "Oficina",
  reading: "Leitura",
  administration: "Administração",
};

export function DesignSystemScreen() {
  const lab = useDesignSystemLab();
  const [query, setQuery] = React.useState("");
  const selected = lab.catalog?.capabilities.find((item) => item.slug === lab.route.slug) ?? null;

  if (lab.loading && !lab.catalog) {
    return <DesignStatePanel state="loading" />;
  }
  if (lab.error && !lab.catalog) {
    return <DesignStatePanel state={lab.offline ? "offline" : "error"} onAction={() => void lab.loadCatalog()} />;
  }
  if (!lab.catalog?.permissions.can_view) {
    return <DesignStatePanel state="forbidden" />;
  }

  return (
    <div className="design-system-screen" data-testid="design-system-screen">
      <header className="ds-heading">
        <div>
          <span className="eyebrow">Contrato visual v{lab.catalog.contract_version}</span>
          <h2>Design system do Printora</h2>
          <p>Referência executável para operação, comunidade e administração, sem alterar impressoras ou dados do servidor.</p>
        </div>
        <label className="ds-density-control">
          Densidade
          <select
            value={lab.draft.density}
            onChange={(event) => lab.updateDraft({ density: event.target.value as DesignDensity })}
          >
            {Object.entries(DENSITY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
      </header>

      <div className="ds-context-bar" role="status">
        <span className={`status-pill ${lab.offline ? "warning" : "active"}`}>
          {lab.offline ? "Catálogo offline" : "Catálogo conectado"}
        </span>
        <span>Rascunho local · revisão {lab.draft.revision}</span>
        <span>Publicação global bloqueada</span>
      </div>

      {lab.saveStatus === "conflict" ? (
        <DesignStatePanel state="conflict" onAction={lab.loadCurrentDraft} />
      ) : null}
      {selected && lab.route.mode === "detail" ? (
        <CapabilityDetail capability={selected} onBack={() => lab.navigate(selected.route)} onEdit={() => lab.navigate(selected.route, "edit")} />
      ) : selected && lab.route.mode === "edit" ? (
        <CapabilityEditor capability={selected} lab={lab} />
      ) : (
        <CapabilityList
          capabilities={lab.catalog.capabilities}
          query={query}
          selectedSlug={lab.route.slug}
          onQueryChange={setQuery}
          onOpen={(capability) => lab.navigate(capability.route)}
          onDetail={(capability) => lab.navigate(capability.route, "detail")}
          onEdit={(capability) => lab.navigate(capability.route, "edit")}
        />
      )}
    </div>
  );
}

function CapabilityList({
  capabilities,
  query,
  selectedSlug,
  onQueryChange,
  onOpen,
  onDetail,
  onEdit,
}: {
  capabilities: DesignCapability[];
  query: string;
  selectedSlug: string | null;
  onQueryChange: (value: string) => void;
  onOpen: (item: DesignCapability) => void;
  onDetail: (item: DesignCapability) => void;
  onEdit: (item: DesignCapability) => void;
}) {
  const normalized = query.trim().toLocaleLowerCase("pt-BR");
  const filtered = capabilities.filter((item) => {
    if (selectedSlug && item.slug !== selectedSlug) return false;
    return !normalized || `${item.title} ${item.summary} ${item.capability_id}`.toLocaleLowerCase("pt-BR").includes(normalized);
  });
  return (
    <>
      <section className="ds-toolbar" aria-label="Filtros do catálogo">
        <label>
          <Search size={16} aria-hidden="true" />
          <span className="sr-only">Buscar capacidade</span>
          <input value={query} onChange={(event) => onQueryChange(event.target.value)} placeholder="Buscar por nome ou capacidade" />
        </label>
        <span><ListFilter size={15} /> {filtered.length} de {capabilities.length} famílias</span>
      </section>
      {filtered.length === 0 ? (
        <DesignStatePanel state="empty" onAction={() => onQueryChange("")} />
      ) : (
        <section className="ds-capability-grid" aria-label="Capacidades do design system">
          {filtered.map((item) => (
            <article key={item.capability_id} className="ds-capability-card">
              <div className="ds-capability-meta">
                <span>{item.capability_id}</span>
                <span>{item.screen_id}</span>
              </div>
              <h3>{item.title}</h3>
              <p>{item.summary}</p>
              <div className="ds-card-actions">
                {selectedSlug ? (
                  <button type="button" className="ghost-button" onClick={() => onOpen(item)}>
                    Lista <Rows3 size={15} />
                  </button>
                ) : null}
                <button type="button" className="secondary-button" onClick={() => onDetail(item)}>
                  Detalhe <ChevronRight size={15} />
                </button>
                <button type="button" className="primary-button" onClick={() => onEdit(item)}>
                  Experimentar <Pencil size={15} />
                </button>
              </div>
            </article>
          ))}
        </section>
      )}
    </>
  );
}

function CapabilityDetail({
  capability,
  onBack,
  onEdit,
}: {
  capability: DesignCapability;
  onBack: () => void;
  onEdit: () => void;
}) {
  return (
    <section className="ds-detail">
      <header>
        <button type="button" className="ghost-button" onClick={onBack}><ArrowLeft size={16} /> Voltar à lista</button>
        <button type="button" className="primary-button" onClick={onEdit}><Pencil size={16} /> Abrir editor</button>
      </header>
      <div className="ds-detail-title">
        <span>{capability.capability_id} · {capability.screen_id}</span>
        <h3>{capability.title}</h3>
        <p>{capability.summary}</p>
      </div>
      <dl className="ds-contract-grid">
        <div><dt>Permissão</dt><dd>Leitura autenticada; personalização apenas local.</dd></div>
        <div><dt>Persistência</dt><dd>Catálogo versionado em código; nenhum dado canônico novo.</dd></div>
        <div><dt>Rollback</dt><dd>Release N-1, sem SQL ou limpeza.</dd></div>
        <div><dt>Estados</dt><dd>{capability.supported_states.join(", ")}</dd></div>
      </dl>
      <CapabilityPreview capability={capability} />
      <section className="ds-traceability">
        <h4>Evidências atribuídas</h4>
        <div>{capability.com_ids.map((item) => <span key={item}>{item}</span>)}</div>
      </section>
    </section>
  );
}

function CapabilityEditor({
  capability,
  lab,
}: {
  capability: DesignCapability;
  lab: ReturnType<typeof useDesignSystemLab>;
}) {
  const saveLabel = lab.saveStatus === "saved" ? "Rascunho salvo" : lab.saveStatus === "unchanged" ? "Sem alterações" : "Salvar rascunho";
  return (
    <section className="ds-editor">
      <header>
        <button type="button" className="ghost-button" onClick={() => lab.navigate(capability.route, "detail")}>
          <ArrowLeft size={16} /> Voltar ao detalhe
        </button>
        <span>{capability.capability_id} · edição local</span>
      </header>
      <form onSubmit={(event) => { event.preventDefault(); lab.saveDraft(); }}>
        <fieldset>
          <legend>1. Contexto</legend>
          <label>Nome da referência
            <input
              value={lab.draft.project_name}
              maxLength={120}
              onChange={(event) => lab.updateDraft({ project_name: event.target.value })}
              placeholder="Ex.: fluxo de revisão da oficina"
            />
          </label>
          <label>Público e necessidade
            <textarea
              value={lab.draft.audience}
              maxLength={240}
              onChange={(event) => lab.updateDraft({ audience: event.target.value })}
              placeholder="Quem usa e em qual contexto?"
            />
          </label>
        </fieldset>
        <fieldset>
          <legend>2. Apresentação</legend>
          <CollectionMode value={lab.draft.collection_mode} onChange={(collection_mode) => lab.updateDraft({ collection_mode })} />
          <label>Estado simulado
            <select value={lab.draft.simulated_state} onChange={(event) => lab.updateDraft({ simulated_state: event.target.value as DesignState })}>
              {capability.supported_states.map((state) => <option key={state} value={state}>{state}</option>)}
            </select>
          </label>
          <label className="ds-check">
            <input type="checkbox" checked={lab.draft.reduce_motion} onChange={(event) => lab.updateDraft({ reduce_motion: event.target.checked })} />
            Reduzir movimento nesta experiência
          </label>
        </fieldset>
        <fieldset>
          <legend>3. Revisão</legend>
          <label>Notas de revisão
            <textarea
              value={lab.draft.review_notes}
              maxLength={2_000}
              onChange={(event) => lab.updateDraft({ review_notes: event.target.value })}
              placeholder="Registre foco, contraste, overflow e recuperação."
            />
          </label>
          <DesignStatePanel state={lab.draft.simulated_state} />
        </fieldset>
        <aside className="ds-review" aria-label="Resumo antes de salvar">
          <h4>Resumo</h4>
          <p><strong>{lab.draft.project_name || "Referência sem nome"}</strong></p>
          <p>Densidade {DENSITY_LABELS[lab.draft.density].toLocaleLowerCase("pt-BR")}; coleção {lab.draft.collection_mode}; estado {lab.draft.simulated_state}.</p>
          <p>Nenhuma alteração será publicada no servidor.</p>
        </aside>
        <div className="ds-editor-actions">
          <button
            type="button"
            className="secondary-button"
            onClick={() => {
              if (window.confirm("Restaurar os valores documentados deste rascunho local?")) lab.restoreDefaults();
            }}
          >
            <RefreshCw size={16} /> Restaurar padrão
          </button>
          <button type="submit" className="primary-button"><Check size={16} /> {saveLabel}</button>
        </div>
      </form>
    </section>
  );
}

function CollectionMode({
  value,
  onChange,
}: {
  value: DesignCollectionMode;
  onChange: (value: DesignCollectionMode) => void;
}) {
  const options: Array<{ value: DesignCollectionMode; label: string; icon: typeof LayoutGrid }> = [
    { value: "cards", label: "Cards", icon: LayoutGrid },
    { value: "table", label: "Tabela", icon: TableProperties },
    { value: "gallery", label: "Galeria", icon: Rows3 },
  ];
  return (
    <div className="ds-segmented" role="group" aria-label="Apresentação da coleção">
      {options.map((option) => {
        const Icon = option.icon;
        return (
          <button key={option.value} type="button" className={value === option.value ? "active" : ""} aria-pressed={value === option.value} onClick={() => onChange(option.value)}>
            <Icon size={15} /> {option.label}
          </button>
        );
      })}
    </div>
  );
}

function CapabilityPreview({ capability }: { capability: DesignCapability }) {
  if (capability.tokens.length > 0) {
    return (
      <div className="ds-token-table" role="table" aria-label="Tokens semânticos">
        {capability.tokens.map((token) => (
          <div key={token.name} role="row"><code role="cell">{token.name}</code><strong role="cell">{token.value}</strong><span role="cell">{token.purpose}</span></div>
        ))}
      </div>
    );
  }
  if (capability.capability_id === "CAP-18-03") {
    return <ResponsivePreview />;
  }
  if (capability.capability_id === "CAP-18-06") {
    return <div className="ds-state-matrix">{capability.supported_states.map((state) => <DesignStatePanel key={state} state={state} />)}</div>;
  }
  return (
    <div className="ds-hierarchy-preview">
      <span className="eyebrow">Contexto compartilhado</span>
      <h4>Uma ação principal inequívoca</h4>
      <p>O conteúdo mantém origem, atualização e recuperação visíveis.</p>
      <button type="button" className="primary-button">Ação principal</button>
    </div>
  );
}

function ResponsivePreview() {
  const items = ["Projeto aberto", "Revisão técnica", "Pronto para oficina"];
  return (
    <div className="ds-responsive-preview">
      <div className="ds-preview-cards">{items.map((item) => <article key={item}><strong>{item}</strong><span>Conteúdo preservado</span></article>)}</div>
      <div className="ds-preview-table" role="table">{items.map((item) => <div key={item} role="row"><strong role="cell">{item}</strong><span role="cell">Disponível</span></div>)}</div>
      <div className="ds-preview-gallery">{items.map((item) => <figure key={item}><div aria-hidden="true" /><figcaption>{item}</figcaption></figure>)}</div>
    </div>
  );
}
