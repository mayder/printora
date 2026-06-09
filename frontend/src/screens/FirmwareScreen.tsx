import { Badge } from "../components/common";
import { formatDateTime } from "../utils/formatters";
import type {
  BoardPreset,
  FirmwareBoardRecord,
  FirmwareBuildPreflight,
  FirmwareBuildRunRecord,
  FirmwareConfigPreview,
  FirmwareHardwareItem,
} from "../types";
import type { ScreenPropsFor } from "./ScreenProps";

type FirmwareScreenProps = ScreenPropsFor<
  | "AlertTriangle"
  | "CheckCircle2"
  | "History"
  | "Play"
  | "RefreshCw"
  | "ShieldCheck"
  | "Zap"
  | "boardPresets"
  | "createFirmwareBoard"
  | "createFirmwareBuildDryRun"
  | "error"
  | "executeFirmwareBuildLocal"
  | "firmwareCatalogSummary"
  | "firmwareBoardCanInterface"
  | "firmwareBoardCanUuid"
  | "firmwareBoardConfigFile"
  | "firmwareBoardName"
  | "firmwareBoardNotes"
  | "firmwareBoardPresetId"
  | "firmwareBoards"
  | "firmwareBuildConfirmation"
  | "firmwareBuildPreflight"
  | "firmwareBuildRuns"
  | "firmwareConfigPreview"
  | "firmwareHardwareInventory"
  | "firmwareInventoryError"
  | "firmwareKlipperPath"
  | "firmwareOutputRoot"
  | "formatConnectionType"
  | "generateFirmwareConfigPreview"
  | "loadFirmwareCatalogSummary"
  | "loadFirmwareHardwareInventory"
  | "loading"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setFirmwareBoardCanInterface"
  | "setFirmwareBoardCanUuid"
  | "setFirmwareBoardConfigFile"
  | "setFirmwareBoardName"
  | "setFirmwareBoardNotes"
  | "setFirmwareBoardPresetId"
  | "setFirmwareBuildConfirmation"
  | "setFirmwareKlipperPath"
  | "setFirmwareOutputRoot"
  | "status"
  | "validateFirmwareBuildPreflight"
>;

export function FirmwareScreen(props: FirmwareScreenProps) {
  const {
    AlertTriangle,
    CheckCircle2,
    History,
    Play,
    RefreshCw,
    ShieldCheck,
    Zap,
    boardPresets,
    createFirmwareBoard,
    createFirmwareBuildDryRun,
    error,
    executeFirmwareBuildLocal,
    firmwareCatalogSummary,
    firmwareBoardCanInterface,
    firmwareBoardCanUuid,
    firmwareBoardConfigFile,
    firmwareBoardName,
    firmwareBoardNotes,
    firmwareBoardPresetId,
    firmwareBoards,
    firmwareBuildConfirmation,
    firmwareBuildPreflight,
    firmwareBuildRuns,
    firmwareConfigPreview,
    firmwareHardwareInventory,
    firmwareInventoryError,
    firmwareKlipperPath,
    firmwareOutputRoot,
    formatConnectionType,
    generateFirmwareConfigPreview,
    loadFirmwareCatalogSummary,
    loadFirmwareHardwareInventory,
    loading,
    selectedPrinter,
    selectedPrinterId,
    setFirmwareBoardCanInterface,
    setFirmwareBoardCanUuid,
    setFirmwareBoardConfigFile,
    setFirmwareBoardName,
    setFirmwareBoardNotes,
    setFirmwareBoardPresetId,
    setFirmwareBuildConfirmation,
    setFirmwareKlipperPath,
    setFirmwareOutputRoot,
    status,
    validateFirmwareBuildPreflight,
  } = props;

  const inventoryItems = firmwareHardwareInventory?.items ?? [];
  const inventoryUnavailable = firmwareHardwareInventory?.source === "agent_unavailable";
  const inventoryErrorMessage = firmwareInventoryError ?? (inventoryUnavailable ? firmwareHardwareInventory?.summary ?? null : null) ?? error;
  const registeredItems = inventoryItems.filter((item) => item.status === "registered");
  const detectedItems = inventoryItems.filter((item) => item.status === "detected");
  const firmwareTargets = inventoryItems.length ? inventoryItems : firmwareBoards.map(boardToHardwareItem);
  const catalogCounts = firmwareHardwareInventory?.catalog_counts ?? firmwareCatalogSummary?.catalog_counts ?? {};
  const catalogMissing = firmwareHardwareInventory?.catalog_hardware_without_local_preset ?? firmwareCatalogSummary?.hardware_without_local_preset ?? {};
  const hardwareWithGuides = catalogCounts.hardware_with_guides ?? boardPresets.length;
  const hardwareWithPreset = catalogCounts.hardware_with_local_preset ?? 0;
  const hardwareWithoutPreset = catalogCounts.hardware_without_local_preset ?? 0;
  const activeBoard = firmwareBoards[0] ?? null;
  const latestBuild = activeBoard ? firmwareBuildRuns.find((run) => run.board_id === activeBoard.id) : null;
  const activePreset = activeBoard ? boardPresets.find((preset) => preset.id === activeBoard.preset_id) ?? null : null;
  const suggestedPresetIds = unique([
    ...detectedItems.flatMap((item) => item.matched_preset_ids),
    ...registeredItems.flatMap((item) => item.matched_preset_ids),
    firmwareBoardPresetId,
  ]);
  const presetOptions = orderPresetsBySuggestion(boardPresets, suggestedPresetIds);

  function refreshFirmwareContext() {
    if (!selectedPrinterId) {
      return;
    }
    void Promise.allSettled([loadFirmwareCatalogSummary(), loadFirmwareHardwareInventory(selectedPrinterId)]);
  }

  function useDetectedItem(item: FirmwareHardwareItem) {
    const presetId = item.matched_preset_ids[0] ?? firmwareBoardPresetId;
    const preset = boardPresets.find((candidate) => candidate.id === presetId);
    setFirmwareBoardName(item.name);
    setFirmwareBoardPresetId(presetId);
    setFirmwareBoardCanUuid(item.can_uuid ?? "");
    setFirmwareBoardCanInterface(item.can_interface ?? "can0");
    setFirmwareBoardConfigFile(`firmware/${presetId || "placa"}.config`);
    const reference = item.catalog_references[0];
    const referenceLabel = reference ? ` Referência: ${reference.label}.` : "";
    const presetNote = preset?.name ? `Modelo sugerido: ${preset.name}.` : "Sem preset local sugerido; confirmar modelo físico.";
    setFirmwareBoardNotes(`Detectado pelo Klipper. ${presetNote}${referenceLabel}`.trim());
  }

  return (
    <>
      <article className="panel wide panel-section panel-firmware firmware-workspace">
        <div className="panel-heading firmware-hero">
          <div>
            <span className="eyebrow">Firmware da impressora ativa</span>
            <h2>{selectedPrinter?.name ?? "Impressora selecionada"}</h2>
            <p className="muted">
              Inventário das MCUs que o Klipper expõe para esta impressora. O catálogo local segue o guia Esoterical CANBus.
            </p>
          </div>
          <div className="panel-actions">
            <button type="button" className="secondary-button" onClick={refreshFirmwareContext} disabled={!selectedPrinterId || loading}>
              <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
              Verificar placas
            </button>
          </div>
        </div>

        <div className="firmware-status-grid">
          <Badge icon={ShieldCheck} label="Conexão" value={status?.connected ? "online" : "sem leitura"} />
          <Badge icon={Zap} label="Klipper" value={status?.printer?.software_version ?? "-"} />
          <Badge icon={RefreshCw} label="Moonraker" value={status?.server?.moonraker_version ?? "-"} />
          <Badge icon={CheckCircle2} label="Placas detectadas" value={detectedItems.length} />
          <Badge icon={History} label="Placas prontas" value={registeredItems.length} />
        </div>

        {loading && !firmwareHardwareInventory && !firmwareInventoryError ? (
          <div className="firmware-state-banner loading">
            <RefreshCw className="button-busy-icon" size={16} />
            <div>
              <strong>Lendo inventário da impressora</strong>
              <span>Consultando MCUs, placas cadastradas e referências locais do catálogo.</span>
            </div>
          </div>
        ) : null}

        {inventoryErrorMessage ? (
          <div className="firmware-state-banner warning">
            <AlertTriangle size={16} />
            <div>
              <strong>Falha na leitura de firmware</strong>
              <span>{formatFirmwareError(inventoryErrorMessage)}</span>
            </div>
          </div>
        ) : null}

        <section className="firmware-focus-grid">
          <div className="firmware-card primary-flow">
            <div className="firmware-card-heading">
              <div>
                <strong>Fluxo principal</strong>
                <span>{activeBoard ? activeBoard.name : "Associe uma placa detectada para liberar geração de config e build seguro"}</span>
              </div>
              <span className={`status-pill ${activeBoard ? "up_to_date" : "warning"}`}>{activeBoard ? "pronto" : "associar"}</span>
            </div>
            {activeBoard ? (
              <>
                <div className="firmware-board-summary">
                  <span>{activeBoard.mcu}</span>
                  <span>{formatConnectionType(activeBoard.connection_type)}</span>
                  <span>{activeBoard.can_uuid ?? activeBoard.config_file}</span>
                </div>
                <PresetStatus preset={activePreset} />
                <div className="firmware-step-row">
                  <button
                    type="button"
                    className="secondary-button"
                    onClick={() => activePreset && void generateFirmwareConfigPreview(activePreset.id)}
                    disabled={loading || !activePreset || activePreset.build_config_status !== "complete"}
                  >
                    <CheckCircle2 size={15} />
                    Ver .config
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void validateFirmwareBuildPreflight(activeBoard.id)} disabled={loading}>
                    <CheckCircle2 size={15} />
                    Validar build
                  </button>
                  <button type="button" className="primary-button" onClick={() => void createFirmwareBuildDryRun(activeBoard.id)} disabled={loading}>
                    <Play size={15} />
                    Preparar build
                  </button>
                </div>
                <small className="muted">
                  Último build: {latestBuild ? `${latestBuild.status} · ${formatDateTime(latestBuild.created_at)}` : "nenhum"}.
                  {latestBuild?.binary_output_path ? ` Artefato: ${latestBuild.binary_output_path}` : ""}
                </small>
              </>
            ) : (
              <div className="firmware-empty-state">
                <strong>MCUs detectadas precisam ser associadas ao modelo físico.</strong>
                <p>O Klipper mostra a MCU e o UUID, mas não informa se ela é Octopus, EBB36 ou outra placa. Escolha o modelo uma vez e o fluxo fica simples.</p>
              </div>
            )}
          </div>

          <div className="firmware-card">
            <div className="firmware-card-heading">
              <div>
                <strong>Catálogo local</strong>
                <span>{firmwareHardwareInventory?.catalog_source.name ?? firmwareCatalogSummary?.source.name ?? "Esoterical CANBus Guide"}</span>
              </div>
              <span className="status-pill up_to_date">{hardwareWithGuides} guias</span>
            </div>
            <div className="firmware-catalog-summary">
              <div className="firmware-catalog-metrics">
                <span>{hardwareWithPreset} com preset local</span>
                <span>{hardwareWithoutPreset} sem preset</span>
                <span>{firmwareCatalogSummary?.manifest_total_pages ?? firmwareHardwareInventory?.catalog_counts.hardware_with_guides ?? "-"} páginas mapeadas</span>
              </div>
              <span>Usado para sugerir modelo físico e link técnico nos cards da impressora ativa.</span>
              <a href={firmwareCatalogSummary?.source.url ?? "https://canbus.esoterical.online/"} target="_blank" rel="noreferrer">
                Abrir referência
              </a>
            </div>
          </div>
        </section>

        <section className="firmware-focus-grid">
          <div className="firmware-card">
            <div className="firmware-card-heading">
              <div>
                <strong>Build local controlado</strong>
                <span>O backend mantém o bloqueio por modo e exige confirmação textual antes de executar.</span>
              </div>
              <span className="status-pill warning">sem flash</span>
            </div>
            <div className="firmware-build-controls compact">
              <label>
                Klipper local
                <input value={firmwareKlipperPath} onChange={(event) => setFirmwareKlipperPath(event.target.value)} placeholder="~/klipper" />
              </label>
              <label>
                Artefatos
                <input value={firmwareOutputRoot} onChange={(event) => setFirmwareOutputRoot(event.target.value)} placeholder="~/.local/share/printora/firmware_builds" />
              </label>
              <label>
                Confirmação
                <input
                  value={firmwareBuildConfirmation}
                  onChange={(event) => setFirmwareBuildConfirmation(event.target.value)}
                  placeholder="EXECUTE_LOCAL_BUILD_NO_FLASH"
                />
              </label>
              <button type="button" className="secondary-button" onClick={() => activeBoard && void executeFirmwareBuildLocal(activeBoard.id)} disabled={!activeBoard || loading}>
                <ShieldCheck size={15} />
                Executar build local
              </button>
            </div>
            {firmwareBuildPreflight ? <BuildPreflightSummary preflight={firmwareBuildPreflight} /> : null}
          </div>
          <ConfigPreviewCard preview={firmwareConfigPreview} />
        </section>

        <section className="firmware-board-section">
          <div className="firmware-section-heading">
            <div>
              <h3>Placas detectadas nesta impressora</h3>
              <p className="muted">{firmwareHardwareInventory?.summary ?? "Clique em verificar placas para ler MCUs e configfile via Moonraker."}</p>
            </div>
            <span className="firmware-compact-counter">{firmwareTargets.length} alvo(s)</span>
          </div>
          <div className="firmware-board-cards">
            {firmwareTargets.length === 0 && !loading ? (
              <div className="firmware-empty-state">
                <strong>Nenhuma MCU lida ainda.</strong>
                <p>Use Verificar placas para buscar a lista de MCUs no Klipper. O catálogo local entra depois como sugestão e referência técnica.</p>
              </div>
            ) : null}
            {firmwareTargets.map((item) => (
              <FirmwareTargetCard
                key={item.id}
                item={item}
                board={item.registered_board_id ? firmwareBoards.find((board) => board.id === item.registered_board_id) : null}
                loading={loading}
                latestBuild={
                  item.registered_board_id ? firmwareBuildRuns.find((run) => run.board_id === item.registered_board_id) ?? null : null
                }
                missingCatalog={catalogMissing}
                preset={resolveTargetPreset(item, firmwareBoards, boardPresets)}
                onBuild={(boardId) => void createFirmwareBuildDryRun(boardId)}
                onBuildPreflight={(boardId) => void validateFirmwareBuildPreflight(boardId)}
                onConfigPreview={(presetId) => void generateFirmwareConfigPreview(presetId)}
                onUseDetected={() => useDetectedItem(item)}
              />
            ))}
          </div>
        </section>

        <details className="collapsible-panel firmware-control-panel" open>
          <summary>Associar placa detectada</summary>
          <form className="firmware-board-form guided" onSubmit={(event) => void createFirmwareBoard(event)}>
            <label>
              Nome na impressora
              <input aria-label="Nome da placa" value={firmwareBoardName} onChange={(event) => setFirmwareBoardName(event.target.value)} placeholder="EBB T0" />
            </label>
            <label>
              Modelo físico
              <select
                aria-label="Preset da placa"
                value={firmwareBoardPresetId}
                onChange={(event) => {
                  setFirmwareBoardPresetId(event.target.value);
                  setFirmwareBoardConfigFile(`firmware/${event.target.value}.config`);
                }}
              >
                {presetOptions.map((preset) => (
                  <option key={preset.id} value={preset.id}>
                    {preset.vendor} · {preset.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              UUID CAN
              <input aria-label="UUID CAN" value={firmwareBoardCanUuid} onChange={(event) => setFirmwareBoardCanUuid(event.target.value)} placeholder="UUID CAN" />
            </label>
            <label>
              Interface
              <input aria-label="Interface CAN" value={firmwareBoardCanInterface} onChange={(event) => setFirmwareBoardCanInterface(event.target.value)} placeholder="can0" />
            </label>
            <label>
              Config do build
              <input
                aria-label="Arquivo .config"
                value={firmwareBoardConfigFile}
                onChange={(event) => setFirmwareBoardConfigFile(event.target.value)}
                placeholder="firmware/ebb_t0.config"
              />
            </label>
            <label>
              Observação
              <textarea
                aria-label="Notas da placa"
                value={firmwareBoardNotes}
                onChange={(event) => setFirmwareBoardNotes(event.target.value)}
                placeholder="Ex.: EBB36 no toolhead, Katapult já instalado"
              />
            </label>
            <button type="submit" className="primary-button" disabled={!selectedPrinterId || loading || boardPresets.length === 0}>
              Associar
            </button>
          </form>
        </details>
      </article>
    </>
  );
}

function FirmwareTargetCard({
  board,
  item,
  loading,
  latestBuild,
  missingCatalog,
  preset,
  onBuild,
  onBuildPreflight,
  onConfigPreview,
  onUseDetected,
}: {
  board: FirmwareBoardRecord | null | undefined;
  item: FirmwareHardwareItem;
  loading: boolean;
  latestBuild: FirmwareBuildRunRecord | null;
  missingCatalog: Record<string, string[]>;
  preset: BoardPreset | null;
  onBuild: (boardId: number) => void;
  onBuildPreflight: (boardId: number) => void;
  onConfigPreview: (presetId: string) => void;
  onUseDetected: () => void;
}) {
  const references = item.catalog_references ?? [];
  const primaryReference = references[0] ?? null;
  const hasLocalPreset = item.matched_preset_ids.length > 0 || references.some((reference) => reference.preset_ids.length > 0);
  const missingLabel = primaryReference?.label ?? item.name;
  const missingInCatalog = Object.values(missingCatalog).some((values) => values.includes(missingLabel));

  return (
    <div className={`firmware-board-card ${item.status}`}>
      <div className="firmware-board-title">
        <div>
          <strong>{item.name}</strong>
          <span>{formatRole(item.role)} · {formatConnection(item.connection)}</span>
        </div>
        <span className={`status-pill ${hasLocalPreset ? "up_to_date" : "warning"}`}>{hasLocalPreset ? "preset local" : "sem preset"}</span>
      </div>
      <div className="firmware-board-meta">
        <small>MCU: {item.mcu_name ?? "-"}</small>
        <small>Versão: {item.current_version ?? "-"}</small>
        <small>UUID: {item.can_uuid ?? "-"}</small>
      </div>
      <div className="firmware-target-detail">
        <small>{item.detail}</small>
        {references.length > 0 ? (
          <div className="firmware-reference-list">
            {references.slice(0, 3).map((reference) => (
              <div className="firmware-reference-row" key={reference.id}>
                <div>
                  <strong>{reference.label}</strong>
                  <span>
                    {formatRole(reference.role)} · {formatConnection(reference.connection)}
                  </span>
                </div>
                <div className="firmware-reference-actions">
                  <span className={`status-pill ${reference.preset_ids.length ? "up_to_date" : "warning"}`}>
                    {reference.preset_ids.length ? "preset" : "sem preset"}
                  </span>
                  <a href={reference.guide_url} target="_blank" rel="noreferrer">
                    Guia
                  </a>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <small>Sem referência específica no catálogo local para esta MCU.</small>
        )}
        {!hasLocalPreset && missingInCatalog ? <small>Existe referência técnica, mas ainda falta preset local para associar diretamente.</small> : null}
        {board ? <PresetStatus preset={preset} /> : null}
        {latestBuild ? <BuildArtifactSummary run={latestBuild} /> : null}
      </div>
      <div className="firmware-step-row">
        {board ? (
          <>
            <button
              type="button"
              className="secondary-button"
              onClick={() => preset && onConfigPreview(preset.id)}
              disabled={loading || !preset || preset.build_config_status !== "complete"}
            >
              .config
            </button>
            <button type="button" className="secondary-button" onClick={() => onBuildPreflight(board.id)} disabled={loading}>
              Validar build
            </button>
            <button type="button" className="primary-button" onClick={() => onBuild(board.id)} disabled={loading}>
              Dry-run build
            </button>
          </>
        ) : (
          <button type="button" className="primary-button" onClick={onUseDetected} disabled={loading}>
            Associar modelo
          </button>
        )}
      </div>
    </div>
  );
}

function boardToHardwareItem(board: FirmwareBoardRecord): FirmwareHardwareItem {
  return {
    id: `board-${board.id}`,
    name: board.name,
    role: board.connection_type === "usb_can_bridge" ? "mainboard" : board.connection_type === "can" ? "toolhead" : "unknown",
    status: "registered",
    source: "printora_firmware_boards",
    connection: board.connection_type,
    mcu_name: board.mcu,
    current_version: null,
    can_uuid: board.can_uuid,
    can_interface: board.can_interface,
    registered_board_id: board.id,
    matched_catalog_ids: [],
    matched_preset_ids: [board.preset_id],
    catalog_references: [],
    guide_url: null,
    action_label: "Gerar build",
    detail: `Placa cadastrada com preset ${board.preset_id}.`,
  };
}

function PresetStatus({ preset }: { preset: BoardPreset | null }) {
  if (!preset) {
    return (
      <div className="firmware-preset-status warning">
        <strong>Preset não carregado</strong>
        <span>Atualize os presets antes de gerar `.config` ou preparar build.</span>
      </div>
    );
  }
  const missing = preset.build_config_validation.missing_fields;
  const invalid = preset.build_config_validation.invalid_fields;
  const detail = preset.build_config_status === "complete"
    ? `${preset.build_config.processor_model} · ${preset.build_config.communication_interface} · ${preset.build_output}`
    : [...missing, ...invalid].join(", ") || "build config incompleto";
  return (
    <div className={`firmware-preset-status ${preset.build_config_status === "complete" ? "ok" : "warning"}`}>
      <strong>{preset.build_config_status === "complete" ? "Preset completo" : "Faltando dados"}</strong>
      <span>{detail}</span>
    </div>
  );
}

function ConfigPreviewCard({ preview }: { preview: FirmwareConfigPreview | null }) {
  return (
    <div className="firmware-card">
      <div className="firmware-card-heading">
        <div>
          <strong>.config gerado</strong>
          <span>{preview ? `${preview.preset_id} · ${preview.lines.length} linhas` : "Gere a prévia a partir de uma placa cadastrada com preset completo."}</span>
        </div>
        <span className={`status-pill ${preview ? "up_to_date" : "warning"}`}>{preview ? "preview" : "vazio"}</span>
      </div>
      {preview ? (
        <pre className="firmware-config-preview">{preview.content}</pre>
      ) : (
        <small className="muted">A geração é feita pelo backend e não salva arquivo no Klipper.</small>
      )}
    </div>
  );
}

function BuildPreflightSummary({ preflight }: { preflight: FirmwareBuildPreflight }) {
  return (
    <div className="firmware-check-list">
      <strong>Preflight: {preflight.message}</strong>
      {preflight.checks.slice(0, 5).map((check) => (
        <span key={check.key} className={`firmware-check ${check.status}`}>
          {check.label}: {check.status}
        </span>
      ))}
    </div>
  );
}

function BuildArtifactSummary({ run }: { run: FirmwareBuildRunRecord }) {
  const completed = run.status === "build_success";
  return (
    <div className={`firmware-artifact-summary ${completed ? "ok" : "warning"}`}>
      <strong>{completed ? "Build concluído" : `Build: ${run.status}`}</strong>
      <span>{run.binary_output_path}</span>
      {run.log_path ? <span>Log: {run.log_path}</span> : null}
    </div>
  );
}

function resolveTargetPreset(
  item: FirmwareHardwareItem,
  boards: FirmwareBoardRecord[],
  presets: BoardPreset[],
) {
  const boardPresetId = item.registered_board_id
    ? boards.find((board) => board.id === item.registered_board_id)?.preset_id
    : null;
  const presetId = boardPresetId ?? item.matched_preset_ids[0] ?? item.catalog_references[0]?.preset_ids[0] ?? null;
  return presets.find((preset) => preset.id === presetId) ?? null;
}

function unique(values: string[]) {
  return Array.from(new Set(values.filter(Boolean)));
}

function orderPresetsBySuggestion(presets: FirmwareScreenProps["boardPresets"], suggestedIds: string[]) {
  const suggested = new Set(suggestedIds);
  return [...presets].sort((left, right) => {
    const leftSuggested = suggested.has(left.id);
    const rightSuggested = suggested.has(right.id);
    if (leftSuggested !== rightSuggested) {
      return leftSuggested ? -1 : 1;
    }
    return `${left.vendor} ${left.name}`.localeCompare(`${right.vendor} ${right.name}`);
  });
}

function formatRole(role: FirmwareHardwareItem["role"]) {
  const labels: Record<FirmwareHardwareItem["role"], string> = {
    can_adapter: "Adaptador CAN",
    mainboard: "Placa principal",
    toolhead: "Toolhead",
    unknown: "MCU",
  };
  return labels[role];
}

function formatConnection(connection: FirmwareHardwareItem["connection"]) {
  const labels: Record<FirmwareHardwareItem["connection"], string> = {
    can: "CAN",
    dedicated_usb_can: "USB-CAN",
    unknown: "conexão não identificada",
    usb: "USB",
    usb_can_bridge: "bridge USB-CAN",
  };
  return labels[connection];
}

function formatFirmwareError(value: string | null) {
  if (!value) {
    return "Não foi possível ler o inventário de firmware desta impressora.";
  }
  if (/<html[\s>]/i.test(value) || /cloudflare/i.test(value) || /bad gateway/i.test(value)) {
    return "A API do Printora retornou 502 ao consultar o inventário de firmware. Tente novamente em alguns segundos; se repetir, o agente ou o backend não respondeu dentro do prazo.";
  }
  try {
    const parsed = JSON.parse(value) as { detail?: string };
    const detail = parsed.detail ?? value;
    if (/<html[\s>]/i.test(detail) || /cloudflare/i.test(detail) || /bad gateway/i.test(detail)) {
      return "A API do Printora retornou 502 ao consultar o inventário de firmware. Tente novamente em alguns segundos; se repetir, o agente ou o backend não respondeu dentro do prazo.";
    }
    return detail;
  } catch {
    return value;
  }
}
