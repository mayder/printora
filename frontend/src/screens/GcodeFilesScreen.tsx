import React from "react";
import {
  Copy,
  Database,
  Download,
  Eye,
  FileText,
  Files,
  Folder,
  HardDrive,
  History,
  Image,
  MoveRight,
  Pencil,
  Play,
  RefreshCw,
  Save,
  Search,
  Square,
  SquareCheckBig,
  Thermometer,
  Trash2,
  X,
} from "lucide-react";
import { operationApi } from "../services/operationApi";
import type { GcodeFileActionName, GcodeFileActionState, GcodeFileDetailResponse, GcodeFilesResponse, OperationGcodeFile } from "../types";
import type { PrintoraScreenProps } from "../hooks/usePrintoraApp";
import { GcodePrintViewer } from "../components/monitoring/GcodePrintViewer";
import type { GcodePreviewMode } from "../components/monitoring/gcodePreview";

type SortKey = "modified" | "name" | "size" | "estimated_time" | "slicer";
type MetadataFilter = "all" | "with_metadata" | "without_metadata";
const GCODE_FILES_PAGE_SIZE = 50;
const GcodeToolsPanel = React.lazy(() => import("../components/gcode/GcodeToolsPanel").then((module) => ({ default: module.GcodeToolsPanel })));

export function GcodeFilesScreen({ confirmAction, selectedPrinter, selectedPrinterId, showToast }: PrintoraScreenProps) {
  const [payload, setPayload] = React.useState<GcodeFilesResponse | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [detail, setDetail] = React.useState<GcodeFileDetailResponse | null>(null);
  const [detailLoading, setDetailLoading] = React.useState(false);
  const [actionBusy, setActionBusy] = React.useState<GcodeFileActionName | null>(null);
  const [confirmationDraft, setConfirmationDraft] = React.useState("");
  const [targetDraft, setTargetDraft] = React.useState("");
  const [previewOpen, setPreviewOpen] = React.useState(false);
  const [previewMode, setPreviewMode] = React.useState<GcodePreviewMode>("full");
  const [previewLayer, setPreviewLayer] = React.useState(1);
  const [editorText, setEditorText] = React.useState<string | null>(null);
  const [editorLoading, setEditorLoading] = React.useState(false);
  const [query, setQuery] = React.useState("");
  const [directory, setDirectory] = React.useState("all");
  const [metadataFilter, setMetadataFilter] = React.useState<MetadataFilter>("all");
  const [sortKey, setSortKey] = React.useState<SortKey>("modified");
  const [selection, setSelection] = React.useState<Set<string>>(() => new Set());
  const showToastRef = React.useRef(showToast);
  const payloadRef = React.useRef<GcodeFilesResponse | null>(null);
  const requestSequenceRef = React.useRef(0);

  React.useEffect(() => {
    showToastRef.current = showToast;
  }, [showToast]);

  const loadFiles = React.useCallback(
    async (options?: { refresh?: boolean; append?: boolean; signal?: AbortSignal }) => {
      if (!selectedPrinterId) return;
      const sequence = requestSequenceRef.current + 1;
      requestSequenceRef.current = sequence;
      setLoading(true);
      try {
        const result = await operationApi.gcodeFiles(selectedPrinterId, {
          refresh: options?.refresh,
          limit: GCODE_FILES_PAGE_SIZE,
          offset: options?.append ? payloadRef.current?.files.length ?? 0 : 0,
          directory: directory === "all" ? "" : directory,
          query,
          sort: sortKey === "name" || sortKey === "size" ? sortKey : "modified",
          direction: sortKey === "name" ? "asc" : "desc",
          signal: options?.signal,
        });
        if (sequence !== requestSequenceRef.current) return;
        setPayload((current) => {
          const next = options?.append && current
            ? { ...result, files: mergeGcodeFiles(current.files, result.files), offset: 0 }
            : result;
          payloadRef.current = next;
          return next;
        });
        if (!options?.append) setSelection(new Set());
        if (result.data_state === "offline" || result.data_state === "error" || result.data_state === "unsupported") {
          showToastRef.current({ tone: "warning", title: "Arquivos G-code indisponíveis", detail: result.error || result.summary });
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        if (sequence !== requestSequenceRef.current) return;
        const detail = err instanceof Error ? err.message : "Falha ao carregar arquivos G-code";
        payloadRef.current = null;
        setPayload(null);
        showToastRef.current({ tone: "danger", title: "Falha ao carregar G-code", detail });
      } finally {
        if (sequence === requestSequenceRef.current) setLoading(false);
      }
    },
    [directory, query, selectedPrinterId, sortKey],
  );

  React.useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => {
      void loadFiles({ signal: controller.signal });
    }, query ? 250 : 0);
    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, [loadFiles]);

  const files = React.useMemo(
    () => filterAndSortFiles(payload?.files ?? [], query, directory, metadataFilter, sortKey),
    [directory, metadataFilter, payload?.files, query, sortKey],
  );
  const directories = payload?.directories ?? [];
  const selectedCount = files.filter((file) => selection.has(file.path ?? file.filename)).length;
  const allVisibleSelected = files.length > 0 && selectedCount === files.length;

  function toggleAllVisible() {
    setSelection((current) => {
      const next = new Set(current);
      if (allVisibleSelected) {
        files.forEach((file) => next.delete(file.path ?? file.filename));
      } else {
        files.forEach((file) => next.add(file.path ?? file.filename));
      }
      return next;
    });
  }

  function toggleFile(file: OperationGcodeFile) {
    const key = file.path ?? file.filename;
    setSelection((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  async function openDetail(file: OperationGcodeFile) {
    if (!selectedPrinterId) return;
    const filename = file.path ?? file.filename;
    setDetailLoading(true);
    setPreviewOpen(false);
    setEditorText(null);
    setConfirmationDraft("");
    setTargetDraft(defaultCopyName(filename));
    setPreviewMode("full");
    setPreviewLayer(Math.max(1, Math.min(20, file.layer_count ?? 1)));
    try {
      setDetail(await operationApi.gcodeFileDetail(selectedPrinterId, filename));
    } catch (err) {
      showToast({ tone: "danger", title: "Falha ao abrir detalhe", detail: err instanceof Error ? err.message : "Detalhe indisponível" });
    } finally {
      setDetailLoading(false);
    }
  }

  async function runReadOnlyAction(action: GcodeFileActionName) {
    if (!selectedPrinterId || !detail) return;
    const filename = detail.file.path ?? detail.file.filename;
    if (action === "copy_path") {
      await navigator.clipboard?.writeText(filename);
      showToast({ tone: "success", title: "Caminho copiado", detail: filename });
      return;
    }
    if (action === "history") {
      showToast({ tone: "info", title: "Histórico carregado", detail: detail.history.length ? `${detail.history.length} evento(s) recente(s).` : "Nenhum evento recente para este arquivo." });
      return;
    }
    if (action === "preview") {
      setPreviewOpen(true);
      setPreviewMode("full");
      return;
    }
    setActionBusy(action);
    try {
      const cached = await operationApi.ensureGcodeCache(selectedPrinterId, filename);
      const text = await operationApi.gcodeCacheText(selectedPrinterId, cached.cache_key);
      downloadTextFile(displayGcodeFileName(filename), text);
      showToast({ tone: "success", title: "Download preparado", detail: displayGcodeFileName(filename) });
    } catch (err) {
      showToast({ tone: "danger", title: action === "download" ? "Falha ao baixar" : "Falha ao abrir prévia", detail: err instanceof Error ? err.message : "Ação indisponível" });
    } finally {
      setActionBusy(null);
    }
  }

  async function runMutableAction(action: GcodeFileActionState) {
    if (!selectedPrinterId || !detail || action.read_only) return;
    const filename = detail.file.path ?? detail.file.filename;
    const target = action.requires_target ? targetDraft.trim() : "";
    const expected = actionConfirmationPhrase(action.action, filename, target);
    if (confirmationDraft.trim() !== expected) {
      showToast({ tone: "warning", title: "Confirmação inválida", detail: `Digite exatamente: ${expected}` });
      return;
    }
    const confirmed = await confirmAction({
      tone: action.destructive ? "danger" : "warning",
      title: action.label,
      detail: `${action.label} ${displayGcodeFileName(filename)}.`,
      evidence: expected,
      confirmLabel: action.label,
    });
    if (!confirmed) return;
    setActionBusy(action.action);
    try {
      const result = await operationApi.gcodeFileAction(selectedPrinterId, {
        action: action.action,
        filename,
        target_filename: target || null,
        confirmation_phrase: confirmationDraft,
      });
      if (result.status === "executed") {
        showToast({ tone: "success", title: "Ação concluída", detail: result.summary });
        await loadFiles({ refresh: true });
        if (action.action === "delete") {
          setDetail(null);
          setPreviewOpen(false);
          setConfirmationDraft("");
          return;
        }
        setDetail(await operationApi.gcodeFileDetail(selectedPrinterId, result.target_filename || result.filename));
        setConfirmationDraft("");
        return;
      }
      showToast({ tone: "warning", title: "Ação bloqueada", detail: result.blockers.join(" ") || result.summary });
    } catch (err) {
      showToast({ tone: "danger", title: "Falha na ação", detail: err instanceof Error ? err.message : "Ação não confirmada" });
    } finally {
      setActionBusy(null);
    }
  }

  async function rescanMetadata() {
    if (!selectedPrinterId || !detail) return;
    const filename = detail.file.path ?? detail.file.filename;
    setActionBusy("history");
    try {
      const result = await operationApi.manageGcodeFiles(selectedPrinterId, { action: "metadata_scan", filename });
      if (result.status !== "executed") {
        showToast({ tone: "warning", title: "Metadados não atualizados", detail: result.blockers.join(" ") || result.summary });
        return;
      }
      await loadFiles({ refresh: true });
      setDetail(await operationApi.gcodeFileDetail(selectedPrinterId, filename));
      showToast({ tone: "success", title: "Metadados atualizados", detail: displayGcodeFileName(filename) });
    } catch (error) {
      showToast({ tone: "danger", title: "Falha ao atualizar metadados", detail: error instanceof Error ? error.message : "Ação não concluída." });
    } finally {
      setActionBusy(null);
    }
  }

  async function openEditor() {
    if (!selectedPrinterId || !detail) return;
    const filename = detail.file.path ?? detail.file.filename;
    if ((detail.file.size ?? 0) > 5 * 1024 * 1024) {
      showToast({ tone: "warning", title: "Arquivo grande demais para edição", detail: "Baixe, edite localmente e envie novamente. O editor aceita até 5 MB." });
      return;
    }
    setEditorLoading(true);
    try {
      const cached = await operationApi.ensureGcodeCache(selectedPrinterId, filename);
      setEditorText(await operationApi.gcodeCacheText(selectedPrinterId, cached.cache_key));
    } catch (error) {
      showToast({ tone: "danger", title: "Falha ao abrir editor", detail: error instanceof Error ? error.message : "Arquivo indisponível." });
    } finally {
      setEditorLoading(false);
    }
  }

  async function saveEditor() {
    if (!selectedPrinterId || !detail || editorText === null) return;
    const filename = detail.file.path ?? detail.file.filename;
    const confirmation = `SOBRESCREVER ${filename}`;
    const confirmed = await confirmAction({
      tone: "warning",
      title: "Salvar G-code",
      detail: `Sobrescrever ${displayGcodeFileName(filename)} com o conteúdo editado.`,
      evidence: confirmation,
      confirmLabel: "Salvar",
    });
    if (!confirmed) return;
    setEditorLoading(true);
    try {
      const result = await operationApi.uploadGcodeFile(
        selectedPrinterId,
        new Blob([editorText], { type: "text/plain;charset=utf-8" }),
        { filename, overwrite: true, confirmationPhrase: confirmation },
      );
      if (result.status !== "uploaded") {
        showToast({ tone: "warning", title: "Arquivo não salvo", detail: result.blockers.join(" ") || result.summary });
        return;
      }
      await loadFiles({ refresh: true });
      setDetail(await operationApi.gcodeFileDetail(selectedPrinterId, filename));
      showToast({ tone: "success", title: "G-code salvo", detail: displayGcodeFileName(filename) });
    } catch (error) {
      showToast({ tone: "danger", title: "Falha ao salvar G-code", detail: error instanceof Error ? error.message : "Arquivo não salvo." });
    } finally {
      setEditorLoading(false);
    }
  }

  async function preheatFromFile() {
    if (!selectedPrinterId || !detail) return;
    const hotend = Math.round(detail.file.first_layer_extr_temp ?? 0);
    const bed = Math.round(detail.file.first_layer_bed_temp ?? 0);
    if (!hotend && !bed) {
      showToast({ tone: "warning", title: "Temperaturas indisponíveis", detail: "Atualize os metadados do arquivo antes de pré-aquecer." });
      return;
    }
    const confirmation = `PRE-AQUECER ${hotend}C / ${bed}C`;
    const confirmed = await confirmAction({
      tone: "warning",
      title: "Pré-aquecer pela primeira camada",
      detail: `Hotend ${hotend} °C e mesa ${bed} °C.`,
      evidence: confirmation,
      confirmLabel: "Pré-aquecer",
    });
    if (!confirmed) return;
    setActionBusy("history");
    try {
      const result = await operationApi.manageGcodeFiles(selectedPrinterId, {
        action: "preheat",
        hotend_temperature: hotend,
        bed_temperature: bed,
        confirmation_phrase: confirmation,
      });
      showToast({
        tone: result.status === "executed" ? "success" : "warning",
        title: result.status === "executed" ? "Pré-aquecimento enviado" : "Pré-aquecimento bloqueado",
        detail: result.blockers.join(" ") || result.summary,
      });
    } catch (error) {
      showToast({ tone: "danger", title: "Falha ao pré-aquecer", detail: error instanceof Error ? error.message : "Comando não confirmado." });
    } finally {
      setActionBusy(null);
    }
  }

  if (!selectedPrinter || !selectedPrinterId) {
    return (
      <article className="panel wide panel-section gcode-files-screen">
        <EmptyState title="Nenhuma impressora aberta" detail="Abra uma impressora para consultar os G-codes do Moonraker." />
      </article>
    );
  }

  return (
    <article className="panel wide panel-section gcode-files-screen">
      <div className="gcode-files-topbar">
        <div>
          <h2>Arquivos G-code</h2>
          <p className="muted">{payload?.summary ?? `Arquivos de ${selectedPrinter.name}`}</p>
        </div>
        <button type="button" className="secondary-button" onClick={() => void loadFiles({ refresh: true })} disabled={loading}>
          <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
          Atualizar
        </button>
      </div>

      <div className="gcode-files-metrics">
        <Metric icon={FileText} label="Arquivos" value={String(payload?.total ?? payload?.files.length ?? 0)} />
        <Metric icon={Folder} label="Pastas" value={String(directories.length)} />
        <Metric icon={SquareCheckBig} label="Selecionados" value={String(selectedCount)} />
        <Metric icon={HardDrive} label="Livre" value={formatBytes(payload?.storage?.free)} detail={formatStorageDetail(payload)} />
      </div>

      <React.Suspense fallback={<EmptyState title="Carregando gerenciador" detail="Preparando upload, pastas e fila de impressão." />}>
        <GcodeToolsPanel
          confirmAction={confirmAction}
          currentDirectory={directory}
          directories={directories.map((item) => item.path)}
          onChanged={async () => {
            setSelection(new Set());
            await loadFiles({ refresh: true });
          }}
          printerId={selectedPrinterId}
          selectedFiles={[...selection]}
          showToast={showToast}
        />
      </React.Suspense>

      <div className="gcode-files-controls">
        <label className="gcode-search-field">
          <Search size={15} />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar arquivo, pasta, material ou slicer" />
        </label>
        <select aria-label="Filtrar pasta" value={directory} onChange={(event) => setDirectory(event.target.value)}>
          <option value="all">Todas as pastas</option>
          {directories.map((item) => (
            <option key={item.path} value={item.path}>
              {item.path}
            </option>
          ))}
        </select>
        <select aria-label="Filtrar metadados" value={metadataFilter} onChange={(event) => setMetadataFilter(event.target.value as MetadataFilter)}>
          <option value="all">Todos</option>
          <option value="with_metadata">Com metadados</option>
          <option value="without_metadata">Sem metadados</option>
        </select>
        <select aria-label="Ordenar arquivos" value={sortKey} onChange={(event) => setSortKey(event.target.value as SortKey)}>
          <option value="modified">Atualização</option>
          <option value="name">Nome</option>
          <option value="size">Tamanho</option>
          <option value="estimated_time">Tempo</option>
          <option value="slicer">Slicer</option>
        </select>
      </div>

      {payload?.data_state === "offline" || payload?.data_state === "error" || payload?.data_state === "unsupported" ? (
        <div className="monitor-note gcode-files-state">
          <Database size={17} />
          <span>{payload.error || payload.summary}</span>
        </div>
      ) : null}

      {loading && !payload ? <EmptyState title="Carregando arquivos" detail="Consultando a lista atual do agente." /> : null}
      {!loading && payload && files.length === 0 ? <EmptyState title="Nenhum G-code encontrado" detail="Ajuste a busca ou atualize a leitura do Moonraker." /> : null}

      {files.length ? (
        <div className="gcode-files-table-wrap">
          <table className="gcode-files-full-table">
            <thead>
              <tr>
                <th>
                  <button type="button" className="icon-button" onClick={toggleAllVisible} aria-label={allVisibleSelected ? "Limpar seleção" : "Selecionar arquivos visíveis"}>
                    {allVisibleSelected ? <SquareCheckBig size={15} /> : <Square size={15} />}
                  </button>
                </th>
                <th>Arquivo</th>
                <th>Atualizado</th>
                <th>Tamanho</th>
                <th>Objeto</th>
                <th>Camada</th>
                <th>Bico</th>
                <th>Filamento</th>
                <th>Tempo</th>
                <th>Temperaturas</th>
                <th>Slicer</th>
                <th>Última impressão</th>
              </tr>
            </thead>
            <tbody>
              {files.map((file) => {
                const key = file.path ?? file.filename;
                return (
                  <tr key={key} className={selection.has(key) ? "is-selected" : ""}>
                    <td>
                      <button type="button" className="icon-button" onClick={() => toggleFile(file)} aria-label={selection.has(key) ? `Remover ${file.name ?? file.filename} da seleção` : `Selecionar ${file.name ?? file.filename}`}>
                        {selection.has(key) ? <SquareCheckBig size={15} /> : <Square size={15} />}
                      </button>
                    </td>
                    <td>
                      <div className="gcode-file-name-cell">
                        <Thumbnail file={file} />
                        <div>
                          <button type="button" className="gcode-file-open-button" title={key} onClick={() => void openDetail(file)}>
                            {file.name || displayGcodeFileName(file.filename)}
                          </button>
                          <span title={key}>{file.directory || "raiz"}</span>
                        </div>
                      </div>
                    </td>
                    <td>{formatUnixDate(file.modified)}</td>
                    <td>{formatBytes(file.size)}</td>
                    <td>{formatMillimeters(file.object_height)}</td>
                    <td>{formatLayer(file)}</td>
                    <td>{formatMillimeters(file.nozzle_diameter)}</td>
                    <td>{formatGcodeFileFilament(file)}</td>
                    <td>{formatDuration(file.estimated_time)}</td>
                    <td>{formatTemperatures(file)}</td>
                    <td>{formatSlicer(file.slicer, file.slicer_version)}</td>
                    <td>{formatLastPrint(file)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
      {payload?.has_more ? (
        <div className="gcode-files-load-more">
          <button type="button" className="secondary-button" onClick={() => void loadFiles({ append: true })} disabled={loading}>
            <RefreshCw className={loading ? "button-busy-icon" : undefined} size={15} />
            {loading ? "Carregando" : `Carregar mais (${payload.files.length} de ${payload.total})`}
          </button>
        </div>
      ) : null}
      {detail || detailLoading ? (
        <GcodeFileDetailDrawer
          actionBusy={actionBusy}
          confirmationDraft={confirmationDraft}
          detail={detail}
          detailLoading={detailLoading}
          editorLoading={editorLoading}
          editorText={editorText}
          onClose={() => {
            setDetail(null);
            setPreviewOpen(false);
            setEditorText(null);
            setConfirmationDraft("");
          }}
          onConfirmationChange={setConfirmationDraft}
          onEditorChange={setEditorText}
          onMutableAction={(action) => void runMutableAction(action)}
          onOpenEditor={() => void openEditor()}
          onPreheat={() => void preheatFromFile()}
          onReadOnlyAction={(action) => void runReadOnlyAction(action)}
          onRescanMetadata={() => void rescanMetadata()}
          onSaveEditor={() => void saveEditor()}
          onPreviewLayerChange={setPreviewLayer}
          onPreviewModeChange={setPreviewMode}
          onTargetChange={setTargetDraft}
          previewLayer={previewLayer}
          previewMode={previewMode}
          previewOpen={previewOpen}
          targetDraft={targetDraft}
        />
      ) : null}
    </article>
  );
}

function mergeGcodeFiles(current: OperationGcodeFile[], incoming: OperationGcodeFile[]) {
  const byPath = new Map(current.map((file) => [file.path ?? file.filename, file]));
  incoming.forEach((file) => byPath.set(file.path ?? file.filename, file));
  return [...byPath.values()];
}

function Metric({ icon: Icon, label, value, detail }: { icon: React.ComponentType<{ size?: number }>; label: string; value: string; detail?: string }) {
  return (
    <div className="gcode-files-metric">
      <Icon size={17} />
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

function Thumbnail({ file }: { file: OperationGcodeFile }) {
  const thumbnail = file.thumbnail;
  if (thumbnail?.data_uri) {
    return <img src={thumbnail.data_uri} alt="" className="gcode-file-thumbnail" loading="lazy" />;
  }
  return (
    <span className="gcode-file-thumbnail gcode-file-thumbnail-fallback" aria-hidden="true">
      <Image size={17} />
    </span>
  );
}

function EmptyState({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="gcode-files-empty-state">
      <Database size={20} />
      <div>
        <strong>{title}</strong>
        <span>{detail}</span>
      </div>
    </div>
  );
}

function GcodeFileDetailDrawer({
  actionBusy,
  confirmationDraft,
  detail,
  detailLoading,
  editorLoading,
  editorText,
  onClose,
  onConfirmationChange,
  onEditorChange,
  onMutableAction,
  onOpenEditor,
  onPreheat,
  onPreviewLayerChange,
  onPreviewModeChange,
  onReadOnlyAction,
  onRescanMetadata,
  onSaveEditor,
  onTargetChange,
  previewLayer,
  previewMode,
  previewOpen,
  targetDraft,
}: {
  actionBusy: GcodeFileActionName | null;
  confirmationDraft: string;
  detail: GcodeFileDetailResponse | null;
  detailLoading: boolean;
  editorLoading: boolean;
  editorText: string | null;
  onClose: () => void;
  onConfirmationChange: (value: string) => void;
  onEditorChange: (value: string | null) => void;
  onMutableAction: (action: GcodeFileActionState) => void;
  onOpenEditor: () => void;
  onPreheat: () => void;
  onPreviewLayerChange: (value: number) => void;
  onPreviewModeChange: (value: GcodePreviewMode) => void;
  onReadOnlyAction: (action: GcodeFileActionName) => void;
  onRescanMetadata: () => void;
  onSaveEditor: () => void;
  onTargetChange: (value: string) => void;
  previewLayer: number;
  previewMode: GcodePreviewMode;
  previewOpen: boolean;
  targetDraft: string;
}) {
  const file = detail?.file;
  const readOnlyActions = (detail?.actions ?? []).filter((action) => action.read_only);
  const mutableActions = (detail?.actions ?? []).filter((action) => !action.read_only);
  const sourceName = file ? file.path ?? file.filename : "";
  return (
    <div className="gcode-file-drawer-backdrop" role="dialog" aria-modal="true" aria-label="Detalhe do G-code">
      <aside className="gcode-file-drawer">
        <div className="gcode-file-drawer-header">
          <div>
            <h3>{file ? file.name || displayGcodeFileName(file.filename) : "Arquivo G-code"}</h3>
            <p className="muted">{detailLoading ? "Carregando detalhe" : sourceName || detail?.summary}</p>
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            <X size={16} />
            Fechar
          </button>
        </div>

        {detailLoading && !detail ? <EmptyState title="Carregando detalhe" detail="Consultando arquivo, histórico e estado atual da impressora." /> : null}

        {detail && file ? (
          <>
            <section className="gcode-file-detail-hero">
              <Thumbnail file={file} />
              <div className="gcode-file-detail-facts">
                <Metric icon={HardDrive} label="Tamanho" value={formatBytes(file.size)} />
                <Metric icon={FileText} label="Camadas" value={formatLayer(file)} />
                <Metric icon={History} label="Última impressão" value={formatLastPrint(file)} />
              </div>
            </section>

            <section className="gcode-file-detail-grid">
              <DetailItem label="Slicer" value={formatSlicer(file.slicer, file.slicer_version)} />
              <DetailItem label="Objeto" value={formatMillimeters(file.object_height)} />
              <DetailItem label="Bico" value={formatMillimeters(file.nozzle_diameter)} />
              <DetailItem label="Filamento" value={formatGcodeFileFilament(file)} />
              <DetailItem label="Tempo estimado" value={formatDuration(file.estimated_time)} />
              <DetailItem label="Temperaturas" value={formatTemperatures(file)} />
            </section>

            <section className="gcode-file-actions">
              <h4>Ações rápidas</h4>
              <div className="gcode-file-action-row">
                {readOnlyActions.map((action) => (
                  <button key={action.action} type="button" className="secondary-button" onClick={() => onReadOnlyAction(action.action)} disabled={!action.enabled || actionBusy !== null}>
                    <ActionIcon action={action.action} />
                    {actionBusy === action.action ? "Aguarde" : action.label}
                  </button>
                ))}
                <button type="button" className="secondary-button" onClick={onRescanMetadata} disabled={actionBusy !== null}>
                  <RefreshCw size={15} />
                  Atualizar metadados
                </button>
                <button type="button" className="secondary-button" onClick={onOpenEditor} disabled={actionBusy !== null || editorLoading}>
                  <Pencil size={15} />
                  {editorLoading ? "Abrindo editor" : "Editar G-code"}
                </button>
                <button type="button" className="secondary-button" onClick={onPreheat} disabled={actionBusy !== null}>
                  <Thermometer size={15} />
                  Pré-aquecer
                </button>
              </div>
            </section>

            {editorText !== null ? (
              <section className="gcode-file-editor">
                <div>
                  <h4>Editor G-code</h4>
                  <button type="button" className="ghost-button" onClick={() => onEditorChange(null)} disabled={editorLoading}>
                    <X size={14} />
                    Fechar editor
                  </button>
                </div>
                <textarea value={editorText} onChange={(event) => onEditorChange(event.target.value)} spellCheck={false} aria-label="Conteúdo do G-code" />
                <button type="button" className="primary-button" onClick={onSaveEditor} disabled={editorLoading}>
                  <Save size={15} />
                  {editorLoading ? "Salvando" : "Salvar e sobrescrever"}
                </button>
              </section>
            ) : null}

            {previewOpen ? (
              <section className="gcode-file-preview gcode-file-preview-3d">
                <div className="gcode-file-preview-controls">
                  <h4>Prévia 3D</h4>
                  <div className="gcode-file-preview-modes" role="group" aria-label="Modo de prévia">
                    {(["full", "until_layer", "current_layer"] as const).map((mode) => (
                      <button key={mode} type="button" className={previewMode === mode ? "segmented-button active" : "segmented-button"} onClick={() => onPreviewModeChange(mode)}>
                        {previewModeLabel(mode)}
                      </button>
                    ))}
                  </div>
                  <label>
                    <span>Camada</span>
                    <input
                      type="number"
                      min={1}
                      max={Math.max(1, file.layer_count ?? 9999)}
                      value={previewLayer}
                      onChange={(event) => onPreviewLayerChange(normalizePreviewLayer(event.target.value, file.layer_count))}
                      disabled={previewMode === "full"}
                    />
                  </label>
                </div>
                <GcodePrintViewer
                  printerId={detail.printer_id}
                  filename={sourceName}
                  mode={previewMode}
                  selectedLayer={previewLayer}
                  currentLayer={previewLayer}
                  totalLayers={file.layer_count}
                  progress={previewMode === "full" ? 1 : null}
                  nozzleDiameter={file.nozzle_diameter}
                />
              </section>
            ) : null}

            <section className="gcode-file-protected-actions">
              <h4>Ações protegidas</h4>
              <label>
                <span>Destino para renomear, mover ou duplicar</span>
                <input value={targetDraft} onChange={(event) => onTargetChange(event.target.value)} placeholder="pasta/arquivo.gcode" />
              </label>
              <label>
                <span>Confirmação textual</span>
                <input value={confirmationDraft} onChange={(event) => onConfirmationChange(event.target.value)} placeholder="Digite a frase exibida na ação" />
              </label>
              <div className="gcode-file-action-cards">
                {mutableActions.map((action) => {
                  const expected = actionConfirmationPhrase(action.action, sourceName, action.requires_target ? targetDraft : "");
                  const disabled = !action.enabled || actionBusy !== null || (action.requires_target && !targetDraft.trim());
                  return (
                    <div key={action.action} className={`gcode-file-action-card ${action.destructive ? "danger" : ""}`}>
                      <div>
                        <strong>
                          <ActionIcon action={action.action} />
                          {action.label}
                        </strong>
                        <span>{action.block_reason || expected}</span>
                      </div>
                      <button type="button" className={action.destructive ? "danger-button" : "secondary-button"} onClick={() => onMutableAction(action)} disabled={disabled}>
                        {actionBusy === action.action ? "Executando" : action.label}
                      </button>
                    </div>
                  );
                })}
              </div>
            </section>

            <section className="gcode-file-history">
              <h4>Histórico</h4>
              {detail.history.length ? (
                <ul>
                  {detail.history.map((entry) => (
                    <li key={entry.id}>
                      <strong>{entry.action || entry.job_type}</strong>
                      <span>{entry.status} · {formatHistoryDate(entry.created_at)}</span>
                      <small>{entry.summary}</small>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="muted">Sem ações recentes registradas para este arquivo.</p>
              )}
            </section>
          </>
        ) : null}
      </aside>
    </div>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="gcode-file-detail-item">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ActionIcon({ action }: { action: GcodeFileActionName }) {
  const icons: Record<GcodeFileActionName, React.ComponentType<{ size?: number }>> = {
    preview: Eye,
    download: Download,
    copy_path: Copy,
    history: History,
    print: Play,
    rename: Pencil,
    move: MoveRight,
    duplicate: Files,
    delete: Trash2,
  };
  const Icon = icons[action];
  return <Icon size={15} />;
}

function filterAndSortFiles(files: OperationGcodeFile[], query: string, directory: string, metadataFilter: MetadataFilter, sortKey: SortKey) {
  const needle = query.trim().toLowerCase();
  return files
    .filter((file) => {
      const key = file.path ?? file.filename;
      if (directory !== "all" && file.directory !== directory) return false;
      if (metadataFilter === "with_metadata" && !file.metadata_available) return false;
      if (metadataFilter === "without_metadata" && file.metadata_available) return false;
      if (!needle) return true;
      return [file.filename, key, file.directory, file.slicer, file.slicer_version, file.filament_type, file.filament_name]
        .filter(Boolean)
        .some((value) => String(value).toLowerCase().includes(needle));
    })
    .sort((left, right) => compareFiles(left, right, sortKey));
}

function compareFiles(left: OperationGcodeFile, right: OperationGcodeFile, sortKey: SortKey) {
  if (sortKey === "name") return (left.name ?? left.filename).localeCompare(right.name ?? right.filename, "pt-BR");
  if (sortKey === "slicer") return formatSlicer(left.slicer, left.slicer_version).localeCompare(formatSlicer(right.slicer, right.slicer_version), "pt-BR");
  return numericValue(right[sortKey]) - numericValue(left[sortKey]);
}

function numericValue(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : -1;
}

function displayGcodeFileName(filename?: string | null) {
  const clean = (filename ?? "").trim();
  if (!clean) return "-";
  return clean.split("/").filter(Boolean).pop() ?? clean;
}

function formatUnixDate(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) return "-";
  const timestamp = value > 1000000000000 ? value : value * 1000;
  return new Date(timestamp).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function formatBytes(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) return "-";
  if (value < 1024) return `${Math.round(value)} B`;
  const units = ["KB", "MB", "GB"];
  let size = value / 1024;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size >= 10 ? size.toFixed(1) : size.toFixed(2)} ${units[unitIndex]}`;
}

function formatStorageDetail(payload: GcodeFilesResponse | null) {
  const used = formatBytes(payload?.storage?.used);
  const total = formatBytes(payload?.storage?.total);
  return used !== "-" || total !== "-" ? `${used} usado(s) de ${total}` : "";
}

function formatMillimeters(value?: number | null) {
  if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) return "-";
  return `${value >= 10 ? value.toFixed(1) : value.toFixed(2)} mm`;
}

function formatLayer(file: OperationGcodeFile) {
  const height = formatMillimeters(file.layer_height);
  if (typeof file.layer_count === "number" && Number.isFinite(file.layer_count)) return `${file.layer_count} · ${height}`;
  return height;
}

function formatGcodeFileFilament(file: OperationGcodeFile) {
  const material = file.filament_type || file.filament_name || "";
  const weight = typeof file.filament_weight_total === "number" ? `${file.filament_weight_total.toFixed(1)} g` : "";
  const length = typeof file.filament_total === "number" ? `${Math.round(file.filament_total)} mm` : "";
  return [material, weight || length].filter(Boolean).join(" · ") || "-";
}

function formatDuration(seconds?: number | null) {
  if (typeof seconds !== "number" || !Number.isFinite(seconds) || seconds <= 0) return "-";
  const totalSeconds = Math.round(seconds);
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);
  const remainingSeconds = totalSeconds % 60;
  if (hours > 0) return `${hours}h ${String(minutes).padStart(2, "0")}m`;
  return `${minutes}m ${String(remainingSeconds).padStart(2, "0")}s`;
}

function formatTemperatures(file: OperationGcodeFile) {
  const extruder = typeof file.first_layer_extr_temp === "number" ? `${Math.round(file.first_layer_extr_temp)}C` : "";
  const bed = typeof file.first_layer_bed_temp === "number" ? `${Math.round(file.first_layer_bed_temp)}C mesa` : "";
  return [extruder, bed].filter(Boolean).join(" · ") || "-";
}

function formatSlicer(slicer?: string | null, version?: string | null) {
  if (!slicer && !version) return "-";
  return [slicer, version].filter(Boolean).join(" ");
}

function formatLastPrint(file: OperationGcodeFile) {
  const duration = formatDuration(file.last_print_duration);
  const end = formatUnixDate(file.print_end_time ?? file.print_start_time);
  if (duration === "-" && end === "-") return "-";
  return [duration, end].filter((item) => item !== "-").join(" · ");
}

function actionConfirmationPhrase(action: GcodeFileActionName, filename: string, targetFilename = "") {
  if (action === "print") return `IMPRIMIR ${filename}`;
  if (action === "delete") return `EXCLUIR ${filename}`;
  if (action === "rename") return `RENOMEAR ${filename} -> ${targetFilename || "<novo-nome>"}`;
  if (action === "move") return `MOVER ${filename} -> ${targetFilename || "<destino>"}`;
  if (action === "duplicate") return `DUPLICAR ${filename} -> ${targetFilename || "<copia>"}`;
  return "";
}

function defaultCopyName(filename: string) {
  const clean = filename.trim();
  if (!clean) return "";
  const extensions = [".gcode.gz", ".gcode", ".gco", ".ngc", ".tap", ".gc", ".nc", ".g"];
  const lower = clean.toLowerCase();
  const extension = extensions.find((item) => lower.endsWith(item)) ?? ".gcode";
  const base = lower.endsWith(extension) ? clean.slice(0, -extension.length) : clean;
  return `${base}-copia${extension}`;
}

function downloadTextFile(filename: string, text: string) {
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename || "arquivo.gcode";
  anchor.click();
  URL.revokeObjectURL(url);
}

function formatHistoryDate(value?: string | null) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function previewModeLabel(mode: GcodePreviewMode) {
  if (mode === "full") return "Completo";
  if (mode === "until_layer") return "Até camada";
  if (mode === "current_layer") return "Camada";
  return "Progresso";
}

function normalizePreviewLayer(value: string, total?: number | null) {
  const parsed = Number.parseInt(value, 10);
  const max = Math.max(1, total ?? 9999);
  if (!Number.isFinite(parsed)) return 1;
  return Math.max(1, Math.min(max, parsed));
}
