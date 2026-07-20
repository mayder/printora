import React from "react";
import { Pencil, Printer as PrinterIcon, SlidersHorizontal, Trash2, X } from "lucide-react";
import { Badge, Metric } from "../components/common";
import { AgentsScreen } from "./AgentsScreen";
import { FirmwareScreen } from "./FirmwareScreen";
import { GcodeFilesScreen } from "./GcodeFilesScreen";
import { MaintenanceScreen } from "./MaintenanceScreen";
import { MonitoringScreen } from "./MonitoringScreen";
import { ReportsScreen } from "./ReportsScreen";
import { TestsScreen } from "./TestsScreen";
import { UpdatesScreen } from "./UpdatesScreen";
import { socialApi } from "../services/socialApi";
import type { PrinterDetailTab, PrintoraScreenProps } from "../hooks/usePrintoraApp";
import type { CatalogSummary, Community, MaterialProfile, PrinterRecord, TechnicalPrinterConfig } from "../types";

type PrinterDetailScreenProps = PrintoraScreenProps;

const printerTabs: Array<{ key: PrinterDetailTab; label: string }> = [
  { key: "summary", label: "Resumo" },
  { key: "operation", label: "Operação" },
  { key: "gcode-files", label: "Arquivos G-code" },
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
      case "gcode-files":
        return <GcodeFilesScreen {...props} />;
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
            <div className="printer-profile-grid">
              <PrinterPublicPanel printer={selectedPrinter} loading={loading} loadPrinters={loadPrinters} showToast={props.showToast} />
              <PrinterTechnicalConfigPanel printer={selectedPrinter} loading={loading} showToast={props.showToast} />
              <PrinterMaterialProfilePanel printer={selectedPrinter} loading={loading} showToast={props.showToast} />
            </div>
          </article>
        );
    }
  })();

  return (
    <>
      <article className="panel wide printer-detail-header">
        <div className="panel-heading">
          <div>
            <button type="button" className="ghost-button compact" onClick={() => setActiveSection("printers")} aria-label="Voltar para impressoras">
              <ArrowLeft size={15} />
              Voltar para impressoras
            </button>
            <h2>{selectedPrinter.name}</h2>
            <p className="muted">{selectedPrinter.cloud_model || "Modelo não informado"} · {selectedPrinter.location || "sem localização"}</p>
          </div>
          <div className="overview-strip printer-detail-strip">
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
  const [formOpen, setFormOpen] = React.useState(false);
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
    setFormOpen(false);
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
      setFormOpen(false);
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
    setFormOpen(true);
  }

  function startCreate() {
    setEditingId(null);
    setDraft(emptyDraft);
    setFormOpen(true);
  }

  function closeForm() {
    setEditingId(null);
    setDraft(emptyDraft);
    setFormOpen(false);
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
        setFormOpen(false);
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
          <h3>Configurações técnicas compartilháveis</h3>
          <p className="muted">Cadastre combinações de mods, componentes e calibrações para comparação social. Não inclua host, IP, Moonraker, SSH, token, caminho local ou credencial.</p>
        </div>
        <Badge icon={SlidersHorizontal} label="Configs" value={String(configs.length)} />
      </div>

      <div className="printer-technical-layout summary-only">
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
          <button type="button" className="secondary-button" onClick={startCreate} disabled={busy || loading}>
            <SlidersHorizontal size={15} />
            Criar configuração técnica
          </button>
        </div>

        {formOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={editingId ? "Editar configuração técnica" : "Criar configuração técnica"}>
            <div className="modal-card printer-technical-modal-card">
              <div className="modal-header">
                <div>
                  <h2><SlidersHorizontal size={18} />{editingId ? "Editar configuração técnica" : "Criar configuração técnica"}</h2>
                  <p>Cadastre somente dados compartilháveis. Não inclua host, IP, SSH, token, caminho local ou credencial.</p>
                </div>
                <button type="button" className="ghost-button" onClick={closeForm} disabled={busy} aria-label="Fechar configuração técnica">
                  <X size={16} />
                </button>
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
                {error ? <p className="form-error printer-public-wide">{error}</p> : null}
                <div className="modal-footer printer-public-wide">
                  <button type="button" className="ghost-button" onClick={closeForm} disabled={busy}>
                    Cancelar
                  </button>
                  <button type="submit" className="primary-button" disabled={busy || loading}>
                    {editingId ? "Salvar configuração" : "Criar configuração técnica"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}
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

interface MaterialDraft {
  title: string;
  visibility: "private" | "community" | "public";
  community_slug: string;
  material_brand: string;
  material_type: string;
  nozzle_diameter_mm: string;
  bed_temperature_c: string;
  nozzle_temperature_c: string;
  flow_percent: string;
  version_label: string;
  compatibility: string;
  layer_height_mm: string;
  speed_mm_s: string;
  infill_percent: string;
  supports_enabled: boolean;
  goal: "quality" | "strength" | "speed" | "prototype";
  settings: string;
  notes: string;
}

function PrinterMaterialProfilePanel({ printer, loading, showToast }: { printer: PrinterRecord; loading: boolean; showToast: PrintoraScreenProps["showToast"] }) {
  const emptyDraft: MaterialDraft = {
    title: `${printer.name} - perfil ABS`,
    visibility: "private",
    community_slug: "",
    material_brand: "",
    material_type: "ABS",
    nozzle_diameter_mm: "0.4",
    bed_temperature_c: "110",
    nozzle_temperature_c: "245",
    flow_percent: "98",
    version_label: "v1",
    compatibility: "material=ABS\nnozzle=0.4mm",
    layer_height_mm: "0.2",
    speed_mm_s: "180",
    infill_percent: "25",
    supports_enabled: false,
    goal: "quality",
    settings: "",
    notes: "",
  };
  const [profiles, setProfiles] = React.useState<MaterialProfile[]>([]);
  const [communities, setCommunities] = React.useState<Community[]>([]);
  const [draft, setDraft] = React.useState<MaterialDraft>(emptyDraft);
  const [editingId, setEditingId] = React.useState<number | null>(null);
  const [formOpen, setFormOpen] = React.useState(false);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const loadProfiles = React.useCallback(async () => {
    try {
      const allProfiles = await socialApi.myMaterialProfiles();
      setProfiles(allProfiles.filter((profile) => profile.printer_id === printer.id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Perfis de material indisponíveis");
    }
  }, [printer.id]);

  React.useEffect(() => {
    setDraft(emptyDraft);
    setEditingId(null);
    setFormOpen(false);
    setError(null);
    void loadProfiles();
  }, [loadProfiles, printer.id]);

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
        material_brand: draft.material_brand,
        material_type: draft.material_type,
        nozzle_diameter_mm: optionalNumber(draft.nozzle_diameter_mm),
        bed_temperature_c: optionalInteger(draft.bed_temperature_c),
        nozzle_temperature_c: optionalInteger(draft.nozzle_temperature_c),
        flow_percent: optionalNumber(draft.flow_percent),
        version_label: draft.version_label || "v1",
        compatibility: parseKeyValueLines(draft.compatibility),
        notes: draft.notes,
        slicing: {
          layer_height_mm: optionalNumber(draft.layer_height_mm),
          speed_mm_s: optionalInteger(draft.speed_mm_s),
          infill_percent: optionalInteger(draft.infill_percent),
          supports_enabled: draft.supports_enabled,
          goal: draft.goal,
          settings: parseKeyValueLines(draft.settings),
        },
      };
      if (editingId) {
        await socialApi.updateMaterialProfile(editingId, payload);
      } else {
        await socialApi.createMaterialProfile(payload);
      }
      await loadProfiles();
      setEditingId(null);
      setDraft(emptyDraft);
      setFormOpen(false);
      showToast({ tone: "success", title: editingId ? "Perfil atualizado" : "Perfil criado" });
    } catch (err) {
      const detail = err instanceof Error ? err.message : undefined;
      setError(detail || "Falha ao salvar perfil de material");
      showToast({ tone: "danger", title: "Falha ao salvar perfil", detail });
    } finally {
      setBusy(false);
    }
  }

  function edit(profile: MaterialProfile) {
    setEditingId(profile.id);
    setDraft({
      title: profile.title,
      visibility: profile.visibility,
      community_slug: profile.community_slug || "",
      material_brand: profile.material_brand,
      material_type: profile.material_type,
      nozzle_diameter_mm: profile.nozzle_diameter_mm?.toString() || "",
      bed_temperature_c: profile.bed_temperature_c?.toString() || "",
      nozzle_temperature_c: profile.nozzle_temperature_c?.toString() || "",
      flow_percent: profile.flow_percent?.toString() || "",
      version_label: profile.version_label,
      compatibility: formatKeyValueLines(profile.compatibility),
      layer_height_mm: profile.slicing.layer_height_mm?.toString() || "",
      speed_mm_s: profile.slicing.speed_mm_s?.toString() || "",
      infill_percent: profile.slicing.infill_percent?.toString() || "",
      supports_enabled: profile.slicing.supports_enabled,
      goal: profile.slicing.goal,
      settings: formatKeyValueLines(Object.fromEntries(Object.entries(profile.slicing.settings).map(([key, value]) => [key, String(value)]))),
      notes: profile.notes,
    });
    setFormOpen(true);
  }

  function startCreate() {
    setEditingId(null);
    setDraft(emptyDraft);
    setFormOpen(true);
  }

  function closeForm() {
    setEditingId(null);
    setDraft(emptyDraft);
    setFormOpen(false);
  }

  async function archive(profileId: number) {
    setBusy(true);
    try {
      await socialApi.archiveMaterialProfile(profileId);
      await loadProfiles();
      if (editingId === profileId) {
        setEditingId(null);
        setDraft(emptyDraft);
        setFormOpen(false);
      }
      showToast({ tone: "success", title: "Perfil arquivado" });
    } catch (err) {
      showToast({ tone: "danger", title: "Falha ao arquivar perfil", detail: err instanceof Error ? err.message : undefined });
    } finally {
      setBusy(false);
    }
  }

  async function exportProfile(profileId: number) {
    try {
      const payload = await socialApi.exportMaterialProfile(profileId);
      await navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      showToast({ tone: "success", title: "Perfil exportado", detail: "JSON copiado para a área de transferência." });
    } catch (err) {
      showToast({ tone: "danger", title: "Falha ao exportar perfil", detail: err instanceof Error ? err.message : undefined });
    }
  }

  return (
    <section className="printer-public-panel printer-technical-panel">
      <div className="panel-heading">
        <div>
          <span className="account-eyebrow">Material e fatiamento</span>
          <h3>Perfis de material e fatiamento</h3>
          <p className="muted">Registre material, temperaturas, nozzle e parâmetros de fatiamento para compartilhar compatibilidade. O perfil nunca é aplicado automaticamente na impressora.</p>
        </div>
        <Badge icon={SlidersHorizontal} label="Materiais" value={String(profiles.length)} />
      </div>

      <div className="printer-technical-layout summary-only">
        <div className="printer-technical-list">
          {profiles.map((profile) => (
            <section key={profile.id} className="printer-technical-card">
              <div>
                <strong>{profile.title}</strong>
                <span>{[profile.material_brand, profile.material_type, profile.nozzle_diameter_mm ? `${profile.nozzle_diameter_mm}mm` : null, profile.version_label].filter(Boolean).join(" / ")}</span>
              </div>
              <small>{profile.visibility === "community" ? profile.community_name || "Comunidade" : profile.visibility}</small>
              <small>{profile.nozzle_temperature_c || "-"}C nozzle · {profile.bed_temperature_c || "-"}C mesa · {profile.slicing.layer_height_mm || "-"}mm camada</small>
              <div className="overview-quick-actions">
                <button type="button" className="secondary-button compact" onClick={() => edit(profile)} disabled={busy || loading}><Pencil size={14} />Editar</button>
                <button type="button" className="secondary-button compact" onClick={() => void exportProfile(profile.id)} disabled={busy || loading}>Exportar</button>
                <button type="button" className="ghost-button compact" onClick={() => void archive(profile.id)} disabled={busy || loading}><Trash2 size={14} />Arquivar</button>
              </div>
            </section>
          ))}
          {profiles.length === 0 ? <p className="muted">Nenhum perfil de material ou fatiamento cadastrado para esta impressora.</p> : null}
          <button type="button" className="secondary-button" onClick={startCreate} disabled={busy || loading}>
            <SlidersHorizontal size={15} />
            Criar perfil de material
          </button>
        </div>

        {formOpen ? (
          <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label={editingId ? "Editar perfil de material" : "Criar perfil de material"}>
            <div className="modal-card printer-technical-modal-card">
              <div className="modal-header">
                <div>
                  <h2><SlidersHorizontal size={18} />{editingId ? "Editar perfil de material" : "Criar perfil de material"}</h2>
                  <p>Registre parâmetros compartilháveis. O perfil não aplica configuração automaticamente na impressora.</p>
                </div>
                <button type="button" className="ghost-button" onClick={closeForm} disabled={busy} aria-label="Fechar perfil de material">
                  <X size={16} />
                </button>
              </div>
              <form className="printer-technical-form" onSubmit={(event) => void submit(event)}>
                <label>Título<input value={draft.title} onChange={(event) => setDraft((current) => ({ ...current, title: event.target.value }))} required /></label>
                <label>Visibilidade<select value={draft.visibility} onChange={(event) => setDraft((current) => ({ ...current, visibility: event.target.value as MaterialDraft["visibility"] }))}><option value="private">Privado</option><option value="community">Comunidade</option><option value="public">Público</option></select></label>
                <label>Comunidade<select value={draft.community_slug} disabled={draft.visibility !== "community"} onChange={(event) => setDraft((current) => ({ ...current, community_slug: event.target.value }))}><option value="">Selecione</option>{communities.map((community) => <option key={community.slug} value={community.slug}>{community.name}</option>)}</select></label>
                <label>Marca<input value={draft.material_brand} onChange={(event) => setDraft((current) => ({ ...current, material_brand: event.target.value }))} /></label>
                <label>Material<input value={draft.material_type} onChange={(event) => setDraft((current) => ({ ...current, material_type: event.target.value }))} required /></label>
                <label>Nozzle mm<input value={draft.nozzle_diameter_mm} onChange={(event) => setDraft((current) => ({ ...current, nozzle_diameter_mm: event.target.value }))} inputMode="decimal" /></label>
                <label>Nozzle C<input value={draft.nozzle_temperature_c} onChange={(event) => setDraft((current) => ({ ...current, nozzle_temperature_c: event.target.value }))} inputMode="numeric" /></label>
                <label>Mesa C<input value={draft.bed_temperature_c} onChange={(event) => setDraft((current) => ({ ...current, bed_temperature_c: event.target.value }))} inputMode="numeric" /></label>
                <label>Fluxo %<input value={draft.flow_percent} onChange={(event) => setDraft((current) => ({ ...current, flow_percent: event.target.value }))} inputMode="decimal" /></label>
                <label>Versão<input value={draft.version_label} onChange={(event) => setDraft((current) => ({ ...current, version_label: event.target.value }))} /></label>
                <label>Altura camada<input value={draft.layer_height_mm} onChange={(event) => setDraft((current) => ({ ...current, layer_height_mm: event.target.value }))} inputMode="decimal" /></label>
                <label>Velocidade mm/s<input value={draft.speed_mm_s} onChange={(event) => setDraft((current) => ({ ...current, speed_mm_s: event.target.value }))} inputMode="numeric" /></label>
                <label>Infill %<input value={draft.infill_percent} onChange={(event) => setDraft((current) => ({ ...current, infill_percent: event.target.value }))} inputMode="numeric" /></label>
                <label>Objetivo<select value={draft.goal} onChange={(event) => setDraft((current) => ({ ...current, goal: event.target.value as MaterialDraft["goal"] }))}><option value="quality">Qualidade</option><option value="strength">Resistência</option><option value="speed">Velocidade</option><option value="prototype">Protótipo</option></select></label>
                <label className="toggle-row"><input type="checkbox" checked={draft.supports_enabled} onChange={(event) => setDraft((current) => ({ ...current, supports_enabled: event.target.checked }))} />Suporte</label>
                <label className="printer-public-wide">Compatibilidade<textarea value={draft.compatibility} onChange={(event) => setDraft((current) => ({ ...current, compatibility: event.target.value }))} rows={3} /></label>
                <label className="printer-public-wide">Configurações livres<textarea value={draft.settings} onChange={(event) => setDraft((current) => ({ ...current, settings: event.target.value }))} rows={3} placeholder={"wall_loops=4\nbridge_speed=40"} /></label>
                <label className="printer-public-wide">Observações<textarea value={draft.notes} onChange={(event) => setDraft((current) => ({ ...current, notes: event.target.value }))} rows={3} /></label>
                {error ? <p className="form-error printer-public-wide">{error}</p> : null}
                <div className="modal-footer printer-public-wide">
                  <button type="button" className="ghost-button" onClick={closeForm} disabled={busy}>
                    Cancelar
                  </button>
                  <button type="submit" className="primary-button" disabled={busy || loading}>
                    {editingId ? "Salvar perfil de material" : "Criar perfil de material"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function optionalNumber(value: string): number | null {
  const parsed = Number(value.replace(",", "."));
  return Number.isFinite(parsed) && value.trim() ? parsed : null;
}

function optionalInteger(value: string): number | null {
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && value.trim() ? parsed : null;
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
  const [editing, setEditing] = React.useState(false);
  const [saving, setSaving] = React.useState(false);

  function resetDraft() {
    setVariantId(printer.catalog_variant_id ? String(printer.catalog_variant_id) : "");
    setPublicName(printer.public_name || printer.name);
    setDescription(printer.public_description || "");
    setMods((printer.public_mods || []).join(", "));
    setImages((printer.public_images || []).join("\n"));
  }

  React.useEffect(() => {
    resetDraft();
    setEditing(false);
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
      setEditing(false);
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
          <h3>Perfil público da impressora</h3>
          <p className="muted">Ficam públicos nome, descrição, fabricante, modelo, variante, volume, cinemática, mods e imagens. Moonraker, IP, SSH, agente, tokens, organização e permissões nunca entram no contrato público.</p>
        </div>
        <Badge icon={PrinterIcon} label="Estado" value={stateLabel} />
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
        <button type="button" className="secondary-button" disabled={loading || saving} onClick={() => setEditing(true)}>
          <Pencil size={15} />
          Editar perfil público
        </button>
        {printer.public_profile_enabled ? (
          <button type="button" className="secondary-button" disabled={loading || saving} onClick={() => void save(false)}>
            Tornar privada
          </button>
        ) : null}
      </div>

      {editing ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Editar perfil público da impressora">
          <div className="modal-card printer-public-modal-card">
            <div className="modal-header">
              <div>
                <h2><PrinterIcon size={18} />Editar perfil público</h2>
                <p>Defina apenas os dados que podem aparecer no perfil público da impressora.</p>
              </div>
              <button
                type="button"
                className="ghost-button"
                onClick={() => {
                  resetDraft();
                  setEditing(false);
                }}
                disabled={saving}
                aria-label="Fechar perfil público"
              >
                <X size={16} />
              </button>
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
            <div className="modal-footer">
              <button type="button" className="ghost-button" disabled={saving} onClick={() => { resetDraft(); setEditing(false); }}>
                Cancelar
              </button>
              <button type="button" className="secondary-button" disabled={loading || saving || !printer.public_profile_enabled} onClick={() => void save(false)}>
                Tornar privada
              </button>
              <button type="button" className="primary-button" disabled={loading || saving || Boolean(imageError)} onClick={() => void save(true)}>
                Publicar
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </section>
  );
}
