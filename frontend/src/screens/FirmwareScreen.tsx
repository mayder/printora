import { Badge } from "../components/common";
import type { FirmwareBoardRecord, FirmwareHardwareItem } from "../types";
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
  | "createFirmwareFlashDryRun"
  | "firmwareBoardCanInterface"
  | "firmwareBoardCanUuid"
  | "firmwareBoardConfigFile"
  | "firmwareBoardName"
  | "firmwareBoardNotes"
  | "firmwareBoardPresetId"
  | "firmwareBoards"
  | "firmwareBuildRuns"
  | "firmwareFlashRuns"
  | "firmwareHardwareInventory"
  | "formatConnectionType"
  | "loadFirmwareHardwareInventory"
  | "loading"
  | "refreshUpdateStatus"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setFirmwareBoardCanInterface"
  | "setFirmwareBoardCanUuid"
  | "setFirmwareBoardConfigFile"
  | "setFirmwareBoardName"
  | "setFirmwareBoardNotes"
  | "setFirmwareBoardPresetId"
  | "status"
  | "updateStatus"
  | "validateFirmwareBuildPreflight"
  | "validateFirmwareFlashPreflight"
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
    createFirmwareFlashDryRun,
    firmwareBoardCanInterface,
    firmwareBoardCanUuid,
    firmwareBoardConfigFile,
    firmwareBoardName,
    firmwareBoardNotes,
    firmwareBoardPresetId,
    firmwareBoards,
    firmwareBuildRuns,
    firmwareFlashRuns,
    firmwareHardwareInventory,
    formatConnectionType,
    loadFirmwareHardwareInventory,
    loading,
    refreshUpdateStatus,
    selectedPrinter,
    selectedPrinterId,
    setFirmwareBoardCanInterface,
    setFirmwareBoardCanUuid,
    setFirmwareBoardConfigFile,
    setFirmwareBoardName,
    setFirmwareBoardNotes,
    setFirmwareBoardPresetId,
    status,
    updateStatus,
    validateFirmwareBuildPreflight,
    validateFirmwareFlashPreflight,
  } = props;

  const inventoryItems = firmwareHardwareInventory?.items ?? [];
  const registeredItems = inventoryItems.filter((item) => item.status === "registered");
  const detectedItems = inventoryItems.filter((item) => item.status === "detected");
  const firmwareTargets = inventoryItems.length ? inventoryItems : firmwareBoards.map(boardToHardwareItem);
  const updatePendingCount = updateStatus?.components.filter((component) => component.can_update).length ?? 0;
  const activeBoard = firmwareBoards[0] ?? null;
  const latestBuild = activeBoard ? firmwareBuildRuns.find((run) => run.board_id === activeBoard.id) : null;
  const latestFlash = activeBoard ? firmwareFlashRuns.find((run) => run.board_id === activeBoard.id) : null;
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
    void Promise.allSettled([loadFirmwareHardwareInventory(selectedPrinterId), refreshUpdateStatus()]);
  }

  function useDetectedItem(item: FirmwareHardwareItem) {
    const presetId = item.matched_preset_ids[0] ?? firmwareBoardPresetId;
    const preset = boardPresets.find((candidate) => candidate.id === presetId);
    setFirmwareBoardName(item.name);
    setFirmwareBoardPresetId(presetId);
    setFirmwareBoardCanUuid(item.can_uuid ?? "");
    setFirmwareBoardCanInterface(item.can_interface ?? "can0");
    setFirmwareBoardConfigFile(`firmware/${presetId || "placa"}.config`);
    setFirmwareBoardNotes(preset?.name ? `Detectado pelo Klipper; modelo sugerido: ${preset.name}.` : "Detectado pelo Klipper; confirmar modelo físico.");
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
          <Badge icon={AlertTriangle} label="Atualizações" value={updatePendingCount} />
          <Badge icon={CheckCircle2} label="Placas detectadas" value={detectedItems.length} />
          <Badge icon={History} label="Placas prontas" value={registeredItems.length} />
        </div>

        <section className="firmware-focus-grid">
          <div className="firmware-card primary-flow">
            <div className="firmware-card-heading">
              <div>
                <strong>Fluxo principal</strong>
                <span>{activeBoard ? activeBoard.name : "Associe uma placa detectada para liberar build e flash"}</span>
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
                <div className="firmware-step-row">
                  <button type="button" className="secondary-button" onClick={() => void validateFirmwareBuildPreflight(activeBoard.id)} disabled={loading}>
                    <CheckCircle2 size={15} />
                    Validar build
                  </button>
                  <button type="button" className="primary-button" onClick={() => void createFirmwareBuildDryRun(activeBoard.id)} disabled={loading}>
                    <Play size={15} />
                    Gerar build
                  </button>
                  <button type="button" className="secondary-button" onClick={() => void validateFirmwareFlashPreflight(activeBoard.id)} disabled={loading}>
                    <ShieldCheck size={15} />
                    Validar flash
                  </button>
                  <button type="button" className="primary-button" onClick={() => void createFirmwareFlashDryRun(activeBoard.id)} disabled={loading}>
                    <Zap size={15} />
                    Preparar flash
                  </button>
                </div>
                <small className="muted">
                  Último build: {latestBuild ? `${latestBuild.status} · ${latestBuild.created_at}` : "nenhum"} · último flash:{" "}
                  {latestFlash ? `${latestFlash.status} · ${latestFlash.created_at}` : "nenhum"}
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
                <span>{firmwareHardwareInventory?.catalog_source.name ?? "Esoterical CANBus Guide"}</span>
              </div>
              <span className="status-pill up_to_date">{firmwareHardwareInventory?.catalog_counts.hardware_with_guides ?? boardPresets.length} guias</span>
            </div>
            <div className="firmware-catalog-summary">
              <span>Adaptadores CAN, mainboards bridge, toolheads, atualização e troubleshooting.</span>
              <a href="https://canbus.esoterical.online/" target="_blank" rel="noreferrer">
                Abrir referência
              </a>
            </div>
          </div>
        </section>

        <section className="firmware-board-section">
          <div className="firmware-section-heading">
            <div>
              <h3>Placas detectadas nesta impressora</h3>
              <p className="muted">{firmwareHardwareInventory?.summary ?? "Clique em verificar placas para ler MCUs e configfile via Moonraker."}</p>
            </div>
          </div>
          <div className="firmware-board-cards">
            {firmwareTargets.length === 0 ? <p className="muted">Nenhuma MCU de firmware foi lida ainda.</p> : null}
            {firmwareTargets.map((item) => (
              <FirmwareTargetCard
                key={item.id}
                item={item}
                board={item.registered_board_id ? firmwareBoards.find((board) => board.id === item.registered_board_id) : null}
                loading={loading}
                onBuild={(boardId) => void createFirmwareBuildDryRun(boardId)}
                onBuildPreflight={(boardId) => void validateFirmwareBuildPreflight(boardId)}
                onFlash={(boardId) => void createFirmwareFlashDryRun(boardId)}
                onFlashPreflight={(boardId) => void validateFirmwareFlashPreflight(boardId)}
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
  onBuild,
  onBuildPreflight,
  onFlash,
  onFlashPreflight,
  onUseDetected,
}: {
  board: FirmwareBoardRecord | null | undefined;
  item: FirmwareHardwareItem;
  loading: boolean;
  onBuild: (boardId: number) => void;
  onBuildPreflight: (boardId: number) => void;
  onFlash: (boardId: number) => void;
  onFlashPreflight: (boardId: number) => void;
  onUseDetected: () => void;
}) {
  return (
    <div className={`firmware-board-card ${item.status}`}>
      <div>
        <strong>{item.name}</strong>
        <span>{formatRole(item.role)} · {formatConnection(item.connection)}</span>
      </div>
      <div className="firmware-board-meta">
        <small>MCU: {item.mcu_name ?? "-"}</small>
        <small>Versão: {item.current_version ?? "-"}</small>
        <small>UUID: {item.can_uuid ?? "-"}</small>
      </div>
      <div className="firmware-target-detail">
        <small>{item.detail}</small>
        {item.guide_url ? (
          <a href={item.guide_url} target="_blank" rel="noreferrer">
            Guia da placa
          </a>
        ) : null}
      </div>
      <div className="firmware-step-row">
        {board ? (
          <>
            <button type="button" className="secondary-button" onClick={() => onBuildPreflight(board.id)} disabled={loading}>
              Validar build
            </button>
            <button type="button" className="primary-button" onClick={() => onBuild(board.id)} disabled={loading}>
              Build
            </button>
            <button type="button" className="secondary-button" onClick={() => onFlashPreflight(board.id)} disabled={loading}>
              Validar flash
            </button>
            <button type="button" className="primary-button" onClick={() => onFlash(board.id)} disabled={loading}>
              Preparar flash
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
    guide_url: null,
    action_label: "Gerar build",
    detail: `Placa cadastrada com preset ${board.preset_id}.`,
  };
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
