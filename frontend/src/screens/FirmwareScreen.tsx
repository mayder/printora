import { Badge } from "../components/common";
import type { FirmwareBoardRecord, FirmwareBuildPreflight, FirmwareFlashPreflight, PluginAuditItem } from "../types";
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
  | "executeFirmwareBuildLocal"
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
  | "firmwareFilter"
  | "firmwareFlashBinaryPath"
  | "firmwareFlashConfirmation"
  | "firmwareFlashPreflight"
  | "firmwareFlashRuns"
  | "firmwareKlipperPath"
  | "firmwareOutputRoot"
  | "firmwareRecoveryPlan"
  | "formatBoolean"
  | "formatConnectionType"
  | "loadFirmwareRecoveryPlan"
  | "loadPluginAudit"
  | "loading"
  | "pluginAudit"
  | "refreshUpdateStatus"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setFirmwareBoardCanInterface"
  | "setFirmwareBoardCanUuid"
  | "setFirmwareBoardConfigFile"
  | "setFirmwareBoardName"
  | "setFirmwareBoardNotes"
  | "setFirmwareBoardPresetId"
  | "setFirmwareBuildConfirmation"
  | "setFirmwareFilter"
  | "setFirmwareFlashBinaryPath"
  | "setFirmwareFlashConfirmation"
  | "setFirmwareKlipperPath"
  | "setFirmwareOutputRoot"
  | "status"
  | "updateStatus"
  | "validateFirmwareBuildPreflight"
  | "validateFirmwareFlashGate"
  | "validateFirmwareFlashPreflight"
  | "visibleFirmwareBoards"
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
    executeFirmwareBuildLocal,
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
    firmwareFilter,
    firmwareFlashBinaryPath,
    firmwareFlashConfirmation,
    firmwareFlashPreflight,
    firmwareFlashRuns,
    firmwareKlipperPath,
    firmwareOutputRoot,
    firmwareRecoveryPlan,
    formatBoolean,
    formatConnectionType,
    loadFirmwareRecoveryPlan,
    loadPluginAudit,
    loading,
    pluginAudit,
    refreshUpdateStatus,
    selectedPrinter,
    selectedPrinterId,
    setFirmwareBoardCanInterface,
    setFirmwareBoardCanUuid,
    setFirmwareBoardConfigFile,
    setFirmwareBoardName,
    setFirmwareBoardNotes,
    setFirmwareBoardPresetId,
    setFirmwareBuildConfirmation,
    setFirmwareFilter,
    setFirmwareFlashBinaryPath,
    setFirmwareFlashConfirmation,
    setFirmwareKlipperPath,
    setFirmwareOutputRoot,
    status,
    updateStatus,
    validateFirmwareBuildPreflight,
    validateFirmwareFlashGate,
    validateFirmwareFlashPreflight,
    visibleFirmwareBoards,
  } = props;

  const detectedComponents = pluginAudit?.items.filter((item) => item.detected) ?? [];
  const updatePendingCount = updateStatus?.components.filter((component) => component.can_update).length ?? 0;
  const dirtyDetectedCount = detectedComponents.filter((item) => item.dirty).length;
  const registeredCanCount = firmwareBoards.filter((board) => board.connection_type === "can" || board.connection_type === "usb_can_bridge").length;
  const activeBoard = visibleFirmwareBoards[0] ?? firmwareBoards[0] ?? null;
  const latestBuild = activeBoard ? firmwareBuildRuns.find((run) => run.board_id === activeBoard.id) : null;
  const latestFlash = activeBoard ? firmwareFlashRuns.find((run) => run.board_id === activeBoard.id) : null;

  function refreshFirmwareContext() {
    if (!selectedPrinterId) {
      return;
    }
    void Promise.allSettled([loadPluginAudit(selectedPrinterId), refreshUpdateStatus()]);
  }

  return (
    <>
      <article className="panel wide panel-section panel-firmware firmware-workspace">
        <div className="panel-heading firmware-hero">
          <div>
            <span className="eyebrow">Firmware da impressora ativa</span>
            <h2>{selectedPrinter?.name ?? "Impressora selecionada"}</h2>
            <p className="muted">
              Mostra somente o que foi detectado ou cadastrado para esta impressora. Catálogo e parâmetros técnicos ficam em modo avançado.
            </p>
          </div>
          <div className="panel-actions">
            <button type="button" className="secondary-button" onClick={refreshFirmwareContext} disabled={!selectedPrinterId || loading}>
              <RefreshCw size={15} />
              Verificar
            </button>
          </div>
        </div>

        <div className="firmware-status-grid">
          <Badge icon={ShieldCheck} label="Conexão" value={status?.connected ? "online" : "sem leitura"} />
          <Badge icon={Zap} label="Klipper" value={status?.printer?.software_version ?? "-"} />
          <Badge icon={RefreshCw} label="Moonraker" value={status?.server?.moonraker_version ?? "-"} />
          <Badge icon={AlertTriangle} label="Atualizações" value={updatePendingCount} />
          <Badge icon={CheckCircle2} label="Placas" value={firmwareBoards.length} />
          <Badge icon={History} label="Componentes" value={detectedComponents.length} />
        </div>

        <section className="firmware-focus-grid">
          <div className="firmware-card primary-flow">
            <div className="firmware-card-heading">
              <div>
                <strong>Fluxo principal</strong>
                <span>{activeBoard ? activeBoard.name : "Nenhuma placa cadastrada"}</span>
              </div>
              <span className={`status-pill ${activeBoard ? "up_to_date" : "warning"}`}>{activeBoard ? "pronto" : "configurar"}</span>
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
                <strong>O Printora ainda não tem a placa desta impressora.</strong>
                <p>Cadastre somente a placa real instalada. Use a lista avançada apenas para escolher o modelo correto.</p>
              </div>
            )}
          </div>

          <div className="firmware-card">
            <div className="firmware-card-heading">
              <div>
                <strong>Componentes detectados</strong>
                <span>Leitura do Update Manager da impressora</span>
              </div>
              <span className={`status-pill ${dirtyDetectedCount ? "warning" : "up_to_date"}`}>
                {dirtyDetectedCount ? `${dirtyDetectedCount} alterado(s)` : "limpo"}
              </span>
            </div>
            <div className="firmware-component-list">
              {detectedComponents.length === 0 ? <p className="muted">Nenhum componente extra detectado no último snapshot.</p> : null}
              {detectedComponents.slice(0, 6).map((item) => (
                <DetectedComponentRow key={item.name} item={item} />
              ))}
              {detectedComponents.length > 6 ? <small className="muted">+{detectedComponents.length - 6} componente(s) em modo avançado.</small> : null}
            </div>
          </div>
        </section>

        <section className="firmware-board-section">
          <div className="firmware-section-heading">
            <div>
              <h3>Placas desta impressora</h3>
              <p className="muted">{registeredCanCount} placa(s) CAN/bridge cadastrada(s). Não exibimos presets que não pertencem à impressora.</p>
            </div>
            <div className="dense-toolbar firmware-filter-toolbar" aria-label="Filtros de firmware">
              <button type="button" className={firmwareFilter === "all" ? "active" : ""} onClick={() => setFirmwareFilter("all")}>
                Todas
              </button>
              <button type="button" className={firmwareFilter === "can" ? "active" : ""} onClick={() => setFirmwareFilter("can")}>
                CAN
              </button>
              <button type="button" className={firmwareFilter === "usb" ? "active" : ""} onClick={() => setFirmwareFilter("usb")}>
                USB
              </button>
              <span>{visibleFirmwareBoards.length} visíveis</span>
            </div>
          </div>
          <div className="firmware-board-cards">
            {visibleFirmwareBoards.length === 0 ? <p className="muted">Nenhuma placa cadastrada para este filtro.</p> : null}
            {visibleFirmwareBoards.map((board) => (
              <FirmwareBoardCard
                key={board.id}
                board={board}
                formatConnectionType={formatConnectionType}
                loading={loading}
                onBuild={() => void createFirmwareBuildDryRun(board.id)}
                onBuildPreflight={() => void validateFirmwareBuildPreflight(board.id)}
                onFlash={() => void createFirmwareFlashDryRun(board.id)}
                onFlashPreflight={() => void validateFirmwareFlashPreflight(board.id)}
                onRecovery={() => void loadFirmwareRecoveryPlan(board.id)}
              />
            ))}
          </div>
        </section>

        <FirmwareResultPanel buildPreflight={firmwareBuildPreflight} flashPreflight={firmwareFlashPreflight} />

        <details className="collapsible-panel firmware-control-panel">
          <summary>Ajustes avançados</summary>
          <form className="firmware-board-form" onSubmit={(event) => void createFirmwareBoard(event)}>
            <input aria-label="Nome da placa" value={firmwareBoardName} onChange={(event) => setFirmwareBoardName(event.target.value)} placeholder="EBB T0" />
            <select
              aria-label="Preset da placa"
              value={firmwareBoardPresetId}
              onChange={(event) => {
                setFirmwareBoardPresetId(event.target.value);
                setFirmwareBoardConfigFile(`firmware/${event.target.value}.config`);
              }}
            >
              {boardPresets.map((preset) => (
                <option key={preset.id} value={preset.id}>
                  {preset.vendor} · {preset.name}
                </option>
              ))}
            </select>
            <input aria-label="UUID CAN" value={firmwareBoardCanUuid} onChange={(event) => setFirmwareBoardCanUuid(event.target.value)} placeholder="UUID CAN" />
            <input
              aria-label="Interface CAN"
              value={firmwareBoardCanInterface}
              onChange={(event) => setFirmwareBoardCanInterface(event.target.value)}
              placeholder="can0"
            />
            <input
              aria-label="Arquivo .config"
              value={firmwareBoardConfigFile}
              onChange={(event) => setFirmwareBoardConfigFile(event.target.value)}
              placeholder="firmware/ebb_t0.config"
            />
            <textarea
              aria-label="Notas da placa"
              value={firmwareBoardNotes}
              onChange={(event) => setFirmwareBoardNotes(event.target.value)}
              placeholder="Ex.: toolhead CAN, Katapult já instalado"
            />
            <button type="submit" disabled={!selectedPrinterId || loading || boardPresets.length === 0}>
              Cadastrar
            </button>
          </form>

          <div className="firmware-build-controls">
            <input
              aria-label="Caminho do Klipper"
              value={firmwareKlipperPath}
              onChange={(event) => setFirmwareKlipperPath(event.target.value)}
              placeholder="~/klipper"
            />
            <input
              aria-label="Diretório raiz dos builds"
              value={firmwareOutputRoot}
              onChange={(event) => setFirmwareOutputRoot(event.target.value)}
              placeholder="~/printer_data/firmware_builds"
            />
            <input
              aria-label="Binário para dry-run de flash"
              value={firmwareFlashBinaryPath}
              onChange={(event) => setFirmwareFlashBinaryPath(event.target.value)}
              placeholder="binário opcional para dry-run de flash"
            />
          </div>
        </details>

        <details className="collapsible-panel firmware-control-panel">
          <summary>Execução local bloqueada</summary>
          <div className="firmware-build-controls">
            <input
              aria-label="Confirmação do build local"
              value={firmwareBuildConfirmation}
              onChange={(event) => setFirmwareBuildConfirmation(event.target.value)}
              placeholder="EXECUTE_LOCAL_BUILD_NO_FLASH"
            />
            <input
              aria-label="Confirmação do gate de flash"
              value={firmwareFlashConfirmation}
              onChange={(event) => setFirmwareFlashConfirmation(event.target.value)}
              placeholder="BLOCK_REAL_FLASH"
            />
            <button
              type="button"
              onClick={() => activeBoard && void executeFirmwareBuildLocal(activeBoard.id)}
              disabled={!activeBoard || loading || firmwareBuildConfirmation !== "EXECUTE_LOCAL_BUILD_NO_FLASH"}
            >
              Executar build local
            </button>
            <button
              type="button"
              onClick={() => activeBoard && void validateFirmwareFlashGate(activeBoard.id)}
              disabled={!activeBoard || loading || firmwareFlashConfirmation !== "BLOCK_REAL_FLASH"}
            >
              Validar gate flash
            </button>
          </div>
        </details>

        <details className="collapsible-panel firmware-history-panel">
          <summary>Histórico e recuperação</summary>
          <FirmwareRecoveryPlanPanel recoveryPlan={firmwareRecoveryPlan} formatBoolean={formatBoolean} />
          <FirmwareHistory title="Builds" emptyText="Nenhum build registrado." runs={firmwareBuildRuns} />
          <FirmwareHistory title="Flash" emptyText="Nenhum flash registrado." runs={firmwareFlashRuns} />
        </details>
      </article>
    </>
  );
}

function DetectedComponentRow({ item }: { item: PluginAuditItem }) {
  const behind = item.commits_behind && item.commits_behind > 0 ? `${item.commits_behind} atrás` : "atual";
  return (
    <div className={`firmware-component-row ${item.dirty ? "warning" : ""}`}>
      <div>
        <strong>{item.title}</strong>
        <span>{item.version ?? "versão não informada"}</span>
      </div>
      <small>{item.dirty ? "alterado localmente" : behind}</small>
    </div>
  );
}

function FirmwareBoardCard({
  board,
  formatConnectionType,
  loading,
  onBuild,
  onBuildPreflight,
  onFlash,
  onFlashPreflight,
  onRecovery,
}: {
  board: FirmwareBoardRecord;
  formatConnectionType: (connectionType: FirmwareBoardRecord["connection_type"]) => string;
  loading: boolean;
  onBuild: () => void;
  onBuildPreflight: () => void;
  onFlash: () => void;
  onFlashPreflight: () => void;
  onRecovery: () => void;
}) {
  return (
    <div className="firmware-board-card">
      <div>
        <strong>{board.name}</strong>
        <span>{formatConnectionType(board.connection_type)}</span>
      </div>
      <div className="firmware-board-meta">
        <small>MCU: {board.mcu}</small>
        <small>UUID: {board.can_uuid ?? "-"}</small>
        <small>Config: {board.config_file}</small>
      </div>
      <div className="firmware-step-row">
        <button type="button" className="secondary-button" onClick={onBuildPreflight} disabled={loading}>
          Validar
        </button>
        <button type="button" className="primary-button" onClick={onBuild} disabled={loading}>
          Build
        </button>
        <button type="button" className="secondary-button" onClick={onFlashPreflight} disabled={loading}>
          Flash
        </button>
        <button type="button" className="secondary-button" onClick={onRecovery} disabled={loading}>
          Recuperar
        </button>
        <button type="button" className="primary-button" onClick={onFlash} disabled={loading}>
          Preparar
        </button>
      </div>
    </div>
  );
}

function FirmwareResultPanel({
  buildPreflight,
  flashPreflight,
}: {
  buildPreflight: FirmwareBuildPreflight | null;
  flashPreflight: FirmwareFlashPreflight | null;
}) {
  if (!buildPreflight && !flashPreflight) {
    return null;
  }
  return (
    <section className="firmware-result-grid">
      {buildPreflight ? (
        <div className={`firmware-result-card ${buildPreflight.blocked ? "warning" : "ok"}`}>
          <strong>Validação do build · {buildPreflight.board_name}</strong>
          <span>{buildPreflight.message}</span>
          <div className="firmware-check-list">
            {buildPreflight.checks.map((item) => (
              <small key={item.key}>
                {item.label}: {item.status}
              </small>
            ))}
          </div>
        </div>
      ) : null}
      {flashPreflight ? (
        <div className={`firmware-result-card ${flashPreflight.blocked ? "warning" : "ok"}`}>
          <strong>Validação do flash · {flashPreflight.board_name}</strong>
          <span>{flashPreflight.message}</span>
          <div className="firmware-check-list">
            {flashPreflight.checks.map((item) => (
              <small key={item.key}>
                {item.label}: {item.status}
              </small>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  );
}

function FirmwareRecoveryPlanPanel({
  recoveryPlan,
  formatBoolean,
}: {
  recoveryPlan: FirmwareScreenProps["firmwareRecoveryPlan"];
  formatBoolean: FirmwareScreenProps["formatBoolean"];
}) {
  if (!recoveryPlan) {
    return null;
  }
  return (
    <details className="firmware-run-row" open>
      <summary>
        Recuperação · {recoveryPlan.board_name} · bloqueado: {formatBoolean(recoveryPlan.blocked)}
      </summary>
      <div className="firmware-run-detail">
        <strong>Pré-condições</strong>
        <ol>
          {recoveryPlan.prerequisites.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
        <strong>Recuperação</strong>
        <ol>
          {recoveryPlan.recovery_steps.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
        <strong>Validação</strong>
        <ol>
          {recoveryPlan.validation_steps.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ol>
      </div>
    </details>
  );
}

function FirmwareHistory({
  emptyText,
  runs,
  title,
}: {
  emptyText: string;
  runs: Array<{
    id: number;
    board_id: number;
    status: string;
    created_at: string;
    checklist: string[];
    commands: string[];
    message: string;
  }>;
  title: string;
}) {
  return (
    <div className="firmware-run-list">
      <strong>{title}</strong>
      {runs.length === 0 ? <p className="muted">{emptyText}</p> : null}
      {runs.slice(0, 5).map((run) => (
        <details key={`${title}-${run.id}`} className="firmware-run-row">
          <summary>
            #{run.id} · placa #{run.board_id} · {run.status} · {run.created_at}
          </summary>
          <div className="firmware-run-detail">
            <strong>Checklist</strong>
            <ol>
              {run.checklist.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ol>
            <strong>Comandos planejados</strong>
            <pre>{run.commands.join("\n")}</pre>
            <small>{run.message}</small>
          </div>
        </details>
      ))}
    </div>
  );
}
