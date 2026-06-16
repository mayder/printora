import React from "react";
import { Pencil, Printer as PrinterIcon, SlidersHorizontal, Trash2 } from "lucide-react";
import { Badge, Metric } from "../components/common";
import { AgentsScreen } from "./AgentsScreen";
import { FirmwareScreen } from "./FirmwareScreen";
import { MaintenanceScreen } from "./MaintenanceScreen";
import { MonitoringScreen } from "./MonitoringScreen";
import { ReportsScreen } from "./ReportsScreen";
import { TestsScreen } from "./TestsScreen";
import { UpdatesScreen } from "./UpdatesScreen";
import { socialApi } from "../services/socialApi";
import type { PrinterDetailTab, PrintoraScreenProps } from "../hooks/usePrintoraApp";
import type { CatalogSummary, Community, PrinterRecord, TechnicalPrinterConfig } from "../types";

type PrinterDetailScreenProps = PrintoraScreenProps;

const printerTabs: Array<{ key: PrinterDetailTab; label: string }> = [
  { key: "summary", label: "Resumo" },
  { key: "operation", label: "Operação" },
  { key: "updates", label: "Atualizações" },
  { key: "tests", label: "Calibração" },
  { key: "firmware", label: "Firmware" },
  { key: "maintenance", label: "Manutenção" },
  { key: "reports", label: "Diagnóstico" },
  { key: "agents", label: "Agentes" },
];

export function PrinterDetailScreen(props: PrinterDetailScreenProps) {
  const {
    ArrowLeft,
    Database,
    Gauge,
    Printer,
    Radio,
    RefreshCw,
    Settings,
    ShieldCheck,
    captureSnapshot,
    countPendingUpdates,
    formatChecklistDataState,
    formatDecision,
    formatHours,
    formatSshStatus,
    formatUnknown,
    handleAlertCenterAction,
    health,
    lastReadingLabel,
    loadAgentSupport,
    loadFleetAgentPairings,
    loadPrinterPairing,
    loadPrinterHealth,
    loadPrinters,
    loadSelectedPrinterStatus,
    loading,
    moonrakerOnline,
    operationState,
    primaryRiskItem,
    printerDetailTab,
    riskClass,
    riskLabel,
    selectedPrinter,
    selectedPrinterId,
    setActiveSection,
    setAlertCenterOpen,
    setPrinterDetailTab,
    snapshots,
    totalPrintHours,
    updateStatus,
    alertBlockerCount,
    alertWarningCount,
  } = props;

  if (!selectedPrinter || !selectedPrinterId) {
    return (
      <article className="panel wide panel-section panel-printers">
        <div className="panel-heading">
          <div>
            <h2>Nenhuma impressora selecionada</h2>
            <p className="muted">Abra uma impressora pela lista para acessar operação, diagnóstico, manutenção e agentes.</p>
          </div>
          <button type="button" className="primary-button" onClick={() => setActiveSection("printers")}>
            <Printer size={16} />
            Ver impressoras
          </button>
        </div>
      </article>
    );
  }

  async function refreshSelectedPrinterAgentStatus() {
    if (!selectedPrinterId) {
      return;
    }
    await Promise.allSettled([
      loadPrinters(),
      loadFleetAgentPairings([selectedPrinterId]),
      loadPrinterPairing(selectedPrinterId),
      loadAgentSupport(selectedPrinterId),
    ]);
  }

  const activeContent = (() => {
    switch (printerDetailTab) {
      case "operation":
        return <MonitoringScreen {...props} />;
      case "updates":
        return <UpdatesScreen {...props} />;
      case "tests":
        return <TestsScreen {...props} />;
      case "firmware":
        return <FirmwareScreen {...props} />;
      case "maintenance":
        return <MaintenanceScreen {...props} />;
      case "reports":
        return <ReportsScreen {...props} />;
      case "agents":
        return <AgentsScreen {...props} embeddedPrinterContext />;
      default:
        return (
          <article className="panel wide panel-section panel-overview">
            <div className="overview-hero">
              <div className="overview-status-card">
                <span className={`status-pill ${moonrakerOnline ? "online" : "offline"}`}>
                  <span />
                  Moonraker {moonrakerOnline ? "online" : "offline"}
                </span>
                <h2>{selectedPrinter.name}</h2>
                <p>{selectedPrinter.moonraker_url}</p>
                <div className="overview-status-grid">
                  <Metric label="Estado" value={formatUnknown(operationState)} />
                  <Metric label="Horas impressas" value={typeof totalPrintHours === "number" ? formatHours(totalPrintHours) : "-"} />
                  <Metric label="Última leitura" value={lastReadingLabel} />
                  <Metric label="Origem" value={health?.data_state ? formatChecklistDataState(health.data_state) : "-"} />
                  <Metric label="Updates" value={String(countPendingUpdates(updateStatus))} />
                  <Metric label="SSH" value={formatSshStatus(selectedPrinter)} />
                </div>
              </div>
              <div className={`overview-risk-card ${riskClass}`}>
                <span>Risco atual</span>
                <strong>{riskLabel}</strong>
                <p>{health?.summary ?? "Sem health check carregado para esta impressora."}</p>
                {primaryRiskItem ? (
                  <div className="overview-risk-main">
                    <span>{primaryRiskItem.severity === "blocker" ? "Bloqueio principal" : "Alerta principal"}</span>
                    <strong>{primaryRiskItem.title}</strong>
                    <p>{primaryRiskItem.reason}</p>
                    <button type="button" className="secondary-button compact" onClick={() => void handleAlertCenterAction(primaryRiskItem)} disabled={loading}>
                      {primaryRiskItem.actionLabel}
                    </button>
                  </div>
                ) : null}
                <div className="overview-risk-counts">
                  <span>{alertBlockerCount} bloqueio(s)</span>
                  <span>{alertWarningCount} alerta(s)</span>
                  <span>{snapshots.length} snapshot(s)</span>
                </div>
                {props.alertCount > 0 ? (
                  <button type="button" className="ghost-button compact" onClick={() => setAlertCenterOpen(true)}>
                    Ver todos os alertas
                  </button>
                ) : null}
              </div>
            </div>
            <div className="overview-quick-actions" aria-label="Ações rápidas da impressora">
              <button type="button" className="secondary-button" onClick={() => void captureSnapshot()} disabled={loading}>
                <Database size={15} />
                Capturar snapshot
              </button>
              <button type="button" className="secondary-button" onClick={() => void loadPrinterHealth(selectedPrinterId)} disabled={loading}>
                <ShieldCheck size={15} />
                Health check
              </button>
              <button type="button" className="secondary-button" onClick={() => void loadSelectedPrinterStatus()} disabled={loading}>
                <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
                Atualizar status
              </button>
            </div>
            <PrinterPublicPanel printer={selectedPrinter} loading={loading} loadPrinters={loadPrinters} showToast={props.showToast} />
            <PrinterTechnicalConfigPanel printer={selectedPrinter} loading={loading} showToast={props.showToast} />
          </article>
        );
    }
  })();

  return (
    <>
      <article className="panel wide printer-detail-header">
        <div className="panel-heading">
          <div>
            <button type="button" className="ghost-button compact" onClick={() => setActiveSection("printers")}>
              <ArrowLeft size={15} />
              Impressoras
            </button>
            <h2>{selectedPrinter.name}</h2>
            <p className="muted">{selectedPrinter.cloud_model || "Modelo não informado"} · {selectedPrinter.location || "sem localização"}</p>
          </div>
          <div className="overview-strip">
            <Badge icon={Gauge} label="Decisão" value={formatDecision(health?.decision)} />
            <div className="badge-with-action">
              <Badge icon={Radio} label="Agente" value={selectedPrinter.cloud_status} />
              {selectedPrinter.cloud_status !== "online" ? (
                <button
                  type="button"
                  className="icon-button status-refresh-button"
                  onClick={() => void refreshSelectedPrinterAgentStatus()}
                  disabled={loading}
                  title="Atualizar status do agente"
                  aria-label={`Atualizar status do agente ${selectedPrinter.name}`}
                >
                  <RefreshCw className={loading ? "button-busy-icon" : undefined} size={14} />
                </button>
              ) : null}
            </div>
            <Badge icon={Settings} label="Auditoria" value={selectedPrinter.host_audit_mode} />
          </div>
        </div>
        <div className="detail-tabbar" role="tablist" aria-label="Navegação da impressora">
          {printerTabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              role="tab"
              className={printerDetailTab === tab.key ? "active" : ""}
              aria-selected={printerDetailTab === tab.key}
              onClick={() => setPrinterDetailTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </article>
      {activeContent}
    </>
  );
}

interface TechnicalConfigDraft {
  title: string;
  visibility: "private" | "community" | "public";
  community_slug: string;
  mods: string;
  components: string;
  calibrations: string;
  notes: string;
}

function PrinterTechnicalConfigPanel({ printer, loading, showToast }: { printer: PrinterRecord; loading: boolean; showToast: PrintoraScreenProps["showToast"] }) {
  const emptyDraft: TechnicalConfigDraft = {
    title: `${printer.name} - configuração pública`,
    visibility: "private",
    community_slug: "",
    mods: (printer.public_mods || []).join(", "),
    components: "",
    calibrations: "",
    notes: "",
  };
  const [configs, setConfigs] = React.useState<TechnicalPrinterConfig[]>([]);
  const [communities, setCommunities] = React.useState<Community[]>([]);
  const [draft, setDraft] = React.useState<TechnicalConfigDraft>(emptyDraft);
  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadConfigs = React.useCallback(async () => {
    try {
      const allConfigs = await socialApi.myTechnicalConfigs();
      setConfigs(allConfigs.filter((config) => config.printer_id === printer.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Configurações técnicas indisponíveis");
    }
  }, [printer.id]);

  React.useEffect(() => {
    setDraft({
      title: `${printer.name} - configuração pública`,
      visibility: "private",
      community_slug: "",
      mods: (printer.public_mods || []).join(", "),
      components: "",
      calibrations: "",
      notes: "",
    });
    setEditingId(null);
    setError(null);
    void loadConfigs();
  }, [loadConfigs, printer]);

  React.useEffect(() => {
    let active = true;
    async function loadCommunities() {
      if (!printer.catalog_variant_id) {
        setCommunities([]);
        return;
      }
      try {
        const catalog = await socialApi.catalog();
        const variant = catalog.manufacturers
          .flatMap((manufacturer) => manufacturer.models)
          .flatMap((model) => model.variants)
          .find((item) => item.id === printer.catalog_variant_id);
        if (!variant) {
          if (active) setCommunities([]);
          return;
        }
        const payload = await socialApi.communities({ variant: variant.slug });
        if (active) setCommunities(payload);
      } catch {
        if (active) setCommunities([]);
      }
    }
    void loadCommunities();
    return () => {
      active = false;
    };
  }, [printer.catalog_variant_id]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (draft.visibility === "community" && !draft.community_slug) {
      showToast({ tone: "danger", title: "Selecione a comunidade técnica" });
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const payload = {
        printer_id: printer.id,
        catalog_variant_id: printer.catalog_variant_id,
        community_slug: draft.visibility === "community" ? draft.community_slug : null,
        title: draft.title,
        visibility: draft.visibility,
        mods: parseList(draft.mods),
        components: parseKeyValueLines(draft.components),
        calibrations: parseKeyValueLines(draft.calibrations),
        notes: draft.notes,
      };
      if (editingId) {
        await socialApi.updateTechnicalConfig(editingId, payload);
      } else {
        await socialApi.createTechnicalConfig(payload);
      }
      await loadConfigs();
      setEditingId(null);
      setDraft(emptyDraft);
      showToast({ tone: "success", title: editingId ? "Configuração atualizada" : "Configuração criada" });
    } catch (err) {
      const detail = err instanceof Error ? err.message : undefined;
      setError(detail || "Falha ao salvar configuração técnica");
      showToast({ tone: "danger", title: "Falha ao salvar configuração técnica", detail });
    } finally {
      setBusy(false);
    }
  }

  function edit(config: TechnicalPrinterConfig) {
    setEditingId(config.id);
    setDraft({
      title: config.title,
      visibility: config.visibility,
      community_slug: config.community_slug || "",
      mods: config.mods.join(", "),
      components: formatKeyValueLines(config.components),
      calibrations: formatKeyValueLines(config.calibrations),
      notes: config.notes,
    });
  }

  async function archive(configId: number) {
    setBusy(true);
    setError(null);
    try {
      await socialApi.archiveTechnicalConfig(configId);
      await loadConfigs();
      if (editingId === configId) {
        setEditingId(null);
        setDraft(emptyDraft);
      }
      showToast({ tone: "success", title: "Configuração arquivada" });
    } catch (err) {
      const detail = err instanceof Error ? err.message : undefined;
      setError(detail || "Falha ao arquivar configuração técnica");
      showToast({ tone: "danger", title: "Falha ao arquivar configuração", detail });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="printer-public-panel printer-technical-panel">
      <div className="panel-heading">
        <div>
          <span className="account-eyebrow">Configurações técnicas</span>
          <h3>Perfis compartilháveis da impressora</h3>
          <p className="muted">Cadastre mods, componentes e calibrações para comparação social. Não inclua host, IP, Moonraker, SSH, token, caminho local ou credencial.</p>
        </div>
        <Badge icon={SlidersHorizontal} label="Perfis" value={String(configs.length)} />
      </div>

      <div className="printer-technical-layout">
        <div className="printer-technical-list">
          {configs.map((config) => (
            <section key={config.id} className="printer-technical-card">
              <div>
                <strong>{config.title}</strong>
                <span>{config.visibility === "community" ? config.community_name || "Comunidade" : config.visibility === "public" ? "Público" : "Privado"}</span>
              </div>
              {config.mods.length ? <small>Mods: {config.mods.join(", ")}</small> : null}
              <small>Componentes: {Object.keys(config.components).length}</small>
              <small>Calibrações: {Object.keys(config.calibrations).length}</small>
              <div className="overview-quick-actions">
                <button type="button" className="secondary-button compact" onClick={() => edit(config)} disabled={busy || loading}>
                  <Pencil size={14} />
                  Editar
                </button>
                <button type="button" className="ghost-button compact" onClick={() => void archive(config.id)} disabled={busy || loading}>
                  <Trash2 size={14} />
                  Arquivar
                </button>
              </div>
            </section>
          ))}
          {configs.length === 0 ? <p className="muted">Nenhuma configuração técnica cadastrada para esta impressora.</p> : null}
        </div>

        <form className="printer-technical-form" onSubmit={(event) => void submit(event)}>
          <label>
            Título
            <input value={draft.title} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} maxLength={120} required />
          </label>
          <label>
            Visibilidade
            <select value={draft.visibility} onChange={(event) => setDraft((current) => ({ ...current, visibility: event.target.value as TechnicalConfigDraft["visibility"] }))}>
              <option value="private">Privado</option>
              <option value="community">Comunidade</option>
              <option value="public">Público</option>
            </select>
          </label>
          <label>
            Comunidade
            <select value={draft.community_slug} onChange={(event) => setDraft((current) => ({ ...current, community_slug: event.target.value }))} disabled={draft.visibility !== "community"}>
              <option value="">Selecione</option>
              {communities.map((community) => (
                <option key={community.slug} value={community.slug}>{community.name}</option>
              ))}
            </select>
          </label>
          <label>
            Mods
            <input value={draft.mods} onChange={(event) => setDraft((current) => ({ ...current, mods: event.target.value }))} placeholder="Tap, Nevermore" />
          </label>
          <label>
            Componentes
            <textarea value={draft.components} onChange={(event) => setDraft((current) => ({ ...current, components: event.target.value }))} rows={4} placeholder={"hotend=Revo Voron\nextrusor=Clockwork 2"} />
          </label>
          <label>
            Calibrações
            <textarea value={draft.calibrations} onChange={(event) => setDraft((current) => ({ ...current, calibrations: event.target.value }))} rows={4} placeholder={"z_offset=-0.420\npressure_advance=0.035"} />
          </label>
          <label className="printer-public-wide">
            Observações públicas
            <textarea value={draft.notes} onChange={(event) => setDraft((current) => ({ ...current, notes: event.target.value }))} rows={3} maxLength={2000} />
          </label>
          {error ? <p className="form-error">{error}</p> : null}
          <div className="overview-quick-actions">
            <button type="submit" className="primary-button" disabled={busy || loading}>{editingId ? "Salvar edição" : "Criar perfil"}</button>
            {editingId ? (
              <button type="button" className="secondary-button" onClick={() => { setEditingId(null); setDraft(emptyDraft); }} disabled={busy}>
                Cancelar edição
              </button>
            ) : null}
          </div>
        </form>
      </div>
    </section>
  );
}

function parseList(value: string): string[] {
  return value.split(",").map((item) => item.trim()).filter(Boolean);
}

function parseKeyValueLines(value: string): Record<string, string> {
  return Object.fromEntries(
    value
      .split("\n")
      .map((line) => line.trim())
      .filter(Boolean)
      .map((line) => {
        const [key, ...rest] = line.split("=");
        return [key.trim(), rest.join("=").trim()];
      })
      .filter(([key, item]) => key && item),
  );
}

function formatKeyValueLines(value: Record<string, string>): string {
  return Object.entries(value).map(([key, item]) => `${key}=${item}`).join("\n");
}

interface PrinterPublicPanelProps {
  printer: PrinterRecord;
  loading: boolean;
  loadPrinters: () => Promise<void>;
  showToast: PrintoraScreenProps["showToast"];
}

function PrinterPublicPanel({ printer, loading, loadPrinters, showToast }: PrinterPublicPanelProps) {
  const [catalog, setCatalog] = React.useState<CatalogSummary | null>(null);
  const [variantId, setVariantId] = React.useState(printer.catalog_variant_id ? String(printer.catalog_variant_id) : "");
  const [publicName, setPublicName] = React.useState(printer.public_name || printer.name);
  const [description, setDescription] = React.useState(printer.public_description || "");
  const [mods, setMods] = React.useState((printer.public_mods || []).join(", "));
  const [images, setImages] = React.useState((printer.public_images || []).join("\n"));
  const [saving, setSaving] = React.useState(false);

  React.useEffect(() => {
    setVariantId(printer.catalog_variant_id ? String(printer.catalog_variant_id) : "");
    setPublicName(printer.public_name || printer.name);
    setDescription(printer.public_description || "");
    setMods((printer.public_mods || []).join(", "));
    setImages((printer.public_images || []).join("\n"));
  }, [printer]);

  React.useEffect(() => {
    let active = true;
    socialApi.catalog().then((payload) => {
      if (active) setCatalog(payload);
    }).catch((err) => {
      showToast({ tone: "danger", title: "Falha ao carregar catálogo", detail: err instanceof Error ? err.message : undefined });
    });
    return () => {
      active = false;
    };
  }, [showToast]);

  const variants = React.useMemo(() => {
    if (!catalog) return [];
    return catalog.manufacturers.flatMap((manufacturer) =>
      manufacturer.models.flatMap((model) =>
        model.variants.map((variant) => ({
          ...variant,
          label: `${manufacturer.name} / ${model.name} / ${variant.name}`,
          disabled: variant.trust_state === "blocked" || variant.trust_state === "obsolete",
        })),
      ),
    );
  }, [catalog]);
  const selectedVariant = variants.find((variant) => String(variant.id) === variantId);
  const imageList = images.split(/\n|,/).map((item) => item.trim()).filter(Boolean);
  const imageError = imageList.find((imageUrl) => !/^https:\/\/[^/\s]+\.[^/\s]+/i.test(imageUrl));
  const publicUrl = `${window.location.origin}/p/${printer.id}`;
  const stateLabel = !printer.public_profile_enabled
    ? "Privada"
    : selectedVariant?.disabled
      ? "Indisponível por variante"
      : printer.catalog_variant_id
        ? "Pública"
        : "Pendente de variante";

  async function save(publicEnabled: boolean) {
    if (publicEnabled && !variantId) {
      showToast({ tone: "danger", title: "Selecione uma variante canônica" });
      return;
    }
    if (publicEnabled && imageError) {
      showToast({ tone: "danger", title: "Imagem pública inválida", detail: "Use URLs HTTPS públicas, sem localhost ou IP privado." });
      return;
    }
    setSaving(true);
    try {
      await socialApi.updatePrinterPublic(printer.id, {
        public_profile_enabled: publicEnabled,
        catalog_variant_id: publicEnabled ? Number(variantId) : null,
        public_name: publicName || printer.name,
        public_description: description || null,
        public_mods: mods.split(",").map((item) => item.trim()).filter(Boolean),
        public_images: imageList,
      });
      await loadPrinters();
      showToast({ tone: "success", title: publicEnabled ? "Impressora publicada" : "Impressora tornou-se privada" });
    } catch (err) {
      showToast({ tone: "danger", title: "Falha ao atualizar publicação", detail: err instanceof Error ? err.message : undefined });
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="printer-public-panel">
      <div className="panel-heading">
        <div>
          <span className="account-eyebrow">Publicação da impressora</span>
          <h3>Perfil público da impressora real</h3>
          <p className="muted">Ficam públicos nome, descrição, fabricante, modelo, variante, volume, cinemática, mods e imagens. Moonraker, IP, SSH, agente, tokens, organização e permissões nunca entram no contrato público.</p>
        </div>
        <Badge icon={PrinterIcon} label="Estado" value={stateLabel} />
      </div>
      <div className="printer-public-grid">
        <label>
          Nome público
          <input value={publicName} onChange={(event) => setPublicName(event.target.value)} maxLength={120} />
        </label>
        <label>
          Variante canônica
          <select value={variantId} onChange={(event) => setVariantId(event.target.value)}>
            <option value="">Selecione a variante</option>
            {variants.map((variant) => (
              <option key={variant.id} value={variant.id} disabled={variant.disabled}>
                {variant.label}{variant.disabled ? " indisponível" : ""}
              </option>
            ))}
          </select>
        </label>
        <label className="printer-public-wide">
          Descrição pública
          <textarea value={description} onChange={(event) => setDescription(event.target.value)} maxLength={500} rows={3} />
        </label>
        <label>
          Mods públicos
          <input value={mods} onChange={(event) => setMods(event.target.value)} placeholder="Tap, Nevermore" maxLength={500} />
        </label>
        <label>
          Imagens públicas HTTPS
          <textarea value={images} onChange={(event) => setImages(event.target.value)} rows={3} placeholder="https://..." />
          {imageError ? <small className="form-error">URL inválida: {imageError}</small> : null}
        </label>
      </div>
      <div className="printer-public-preview">
        <div>
          <strong>{publicName || printer.name}</strong>
          <span>{selectedVariant?.label || "Variante pendente"}</span>
          {description ? <p>{description}</p> : null}
          {mods ? <small>Mods: {mods}</small> : null}
          {printer.public_profile_enabled ? <a href={publicUrl} target="_blank" rel="noreferrer">{publicUrl}</a> : null}
        </div>
        <div className="printer-public-images">
          {imageList.slice(0, 6).map((imageUrl) => <img key={imageUrl} src={imageUrl} alt="" />)}
        </div>
      </div>
      <div className="overview-quick-actions">
        <button type="button" className="primary-button" disabled={loading || saving || Boolean(imageError)} onClick={() => void save(true)}>
          Publicar
        </button>
        <button type="button" className="secondary-button" disabled={loading || saving || !printer.public_profile_enabled} onClick={() => void save(false)}>
          Tornar privada
        </button>
      </div>
    </section>
  );
}
