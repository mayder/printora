import React from "react";
import { Copy, FolderPlus, ListPlus, MoveRight, Pause, Play, RefreshCw, Trash2 } from "lucide-react";
import { operationApi } from "../../services/operationApi";
import type { GcodeManagerAction, GcodeManagerResponse } from "../../types";

type ConfirmAction = (options: {
  tone: "danger" | "warning";
  title: string;
  detail: string;
  evidence: string;
  confirmLabel: string;
}) => Promise<boolean>;

export function GcodeManagerPanel({
  confirmAction,
  currentDirectory,
  directories,
  onChanged,
  printerId,
  selectedFiles,
  showToast,
}: {
  confirmAction: ConfirmAction;
  currentDirectory: string;
  directories: string[];
  onChanged: () => Promise<void>;
  printerId: number;
  selectedFiles: string[];
  showToast: (toast: { tone: "success" | "warning" | "danger" | "info"; title: string; detail: string }) => void;
}) {
  const [directoryDraft, setDirectoryDraft] = React.useState("");
  const [folderTargetDraft, setFolderTargetDraft] = React.useState("");
  const [targetDirectory, setTargetDirectory] = React.useState("");
  const [busy, setBusy] = React.useState<GcodeManagerAction | null>(null);
  const [queue, setQueue] = React.useState<GcodeManagerResponse | null>(null);
  const showToastRef = React.useRef(showToast);

  React.useEffect(() => {
    showToastRef.current = showToast;
  }, [showToast]);

  const loadQueue = React.useCallback(async () => {
    try {
      setQueue(await operationApi.gcodeQueue(printerId));
    } catch (error) {
      setQueue(null);
      showToastRef.current({ tone: "warning", title: "Fila indisponível", detail: error instanceof Error ? error.message : "Não foi possível consultar a fila." });
    }
  }, [printerId]);

  React.useEffect(() => {
    void loadQueue();
  }, [loadQueue]);

  async function execute(action: GcodeManagerAction, options?: { directory?: string; target?: string; files?: string[]; jobIds?: string[] }) {
    if (busy) return;
    const files = options?.files ?? [];
    const directory = options?.directory ?? "";
    const target = options?.target ?? "";
    const jobIds = options?.jobIds ?? [];
    const confirmation = confirmationFor(action, files, directory, target, jobIds.length);
    if (confirmation) {
      const confirmed = await confirmAction({
        tone: action.includes("delete") ? "danger" : "warning",
        title: "Confirmar ação no gerenciador",
        detail: files.length ? `${files.length} arquivo(s) selecionado(s).` : `${directory}${target ? ` para ${target}` : ""}.`,
        evidence: confirmation,
        confirmLabel: "Confirmar",
      });
      if (!confirmed) return;
    }
    setBusy(action);
    try {
      const result = await operationApi.manageGcodeFiles(printerId, {
        action,
        filenames: files,
        directory,
        target_directory: target,
        job_ids: jobIds,
        confirmation_phrase: confirmation,
      });
      if (result.status !== "executed") {
        showToast({ tone: "warning", title: "Ação bloqueada", detail: result.blockers.join(" ") || result.summary });
        return;
      }
      showToast({ tone: "success", title: "Ação concluída", detail: result.summary });
      setDirectoryDraft("");
      await Promise.all([onChanged(), loadQueue()]);
    } catch (error) {
      showToast({ tone: "danger", title: "Falha no gerenciador", detail: error instanceof Error ? error.message : "Ação não concluída." });
    } finally {
      setBusy(null);
    }
  }

  const activeDirectory = currentDirectory === "all" ? "" : currentDirectory;
  const queueSummary = summarizeQueue(queue);
  const queuedJobs = readQueueJobs(queue);
  return (
    <section className="gcode-manager-panel">
      <div className="gcode-manager-section">
        <div>
          <strong>Pastas</strong>
          <span>Criar, mover ou excluir pasta vazia.</span>
        </div>
        <input value={directoryDraft} onChange={(event) => setDirectoryDraft(event.target.value)} placeholder="nova-pasta" />
        <button type="button" className="secondary-button" disabled={busy !== null || !directoryDraft.trim()} onClick={() => void execute("directory_create", { directory: directoryDraft.trim() })}>
          <FolderPlus size={15} />
          Criar
        </button>
        <input value={folderTargetDraft} onChange={(event) => setFolderTargetDraft(event.target.value)} placeholder="novo-caminho-da-pasta" />
        <button type="button" className="secondary-button" disabled={busy !== null || !activeDirectory || !folderTargetDraft.trim()} onClick={() => void execute("directory_move", { directory: activeDirectory, target: folderTargetDraft.trim() })}>
          <MoveRight size={15} />
          Renomear/mover atual
        </button>
        <button type="button" className="danger-button" disabled={busy !== null || !activeDirectory} onClick={() => void execute("directory_delete", { directory: activeDirectory })}>
          <Trash2 size={15} />
          Excluir pasta atual
        </button>
      </div>

      <div className="gcode-manager-section">
        <div>
          <strong>Ações em lote</strong>
          <span>{selectedFiles.length ? `${selectedFiles.length} arquivo(s) selecionado(s).` : "Selecione arquivos na tabela."}</span>
        </div>
        <select aria-label="Destino da ação em lote" value={targetDirectory} onChange={(event) => setTargetDirectory(event.target.value)}>
          <option value="">Escolha o destino</option>
          {directories.map((directory) => <option key={directory} value={directory}>{directory}</option>)}
        </select>
        <button type="button" className="secondary-button" disabled={busy !== null || !selectedFiles.length} onClick={() => void execute("queue_add", { files: selectedFiles })}>
          <ListPlus size={15} />
          Adicionar à fila
        </button>
        <button type="button" className="secondary-button" disabled={busy !== null || !selectedFiles.length} onClick={() => void execute("batch_duplicate", { files: selectedFiles })}>
          <Copy size={15} />
          Duplicar
        </button>
        <button type="button" className="secondary-button" disabled={busy !== null || !selectedFiles.length || !targetDirectory} onClick={() => void execute("batch_move", { files: selectedFiles, target: targetDirectory })}>
          <MoveRight size={15} />
          Mover
        </button>
        <button type="button" className="danger-button" disabled={busy !== null || !selectedFiles.length} onClick={() => void execute("batch_delete", { files: selectedFiles })}>
          <Trash2 size={15} />
          Excluir
        </button>
      </div>

      <div className="gcode-manager-section">
        <div>
          <strong>Fila de impressão</strong>
          <span>{queueSummary}</span>
        </div>
        <button type="button" className="secondary-button" disabled={busy !== null} onClick={() => void execute("queue_pause")}>
          <Pause size={15} />
          Pausar fila
        </button>
        <button type="button" className="secondary-button" disabled={busy !== null} onClick={() => void execute("queue_resume")}>
          <Play size={15} />
          Continuar fila
        </button>
        <button type="button" className="icon-button" aria-label="Atualizar fila" onClick={() => void loadQueue()}>
          <RefreshCw size={15} />
        </button>
        {queuedJobs.map((job) => (
          <button key={job.id} type="button" className="ghost-button" disabled={busy !== null} onClick={() => void execute("queue_remove", { jobIds: [job.id] })}>
            <Trash2 size={14} />
            {job.filename}
          </button>
        ))}
      </div>
    </section>
  );
}

function confirmationFor(action: GcodeManagerAction, files: string[], directory: string, target: string, jobCount: number) {
  if (action === "directory_move") return `MOVER PASTA ${directory} -> ${target}`;
  if (action === "directory_delete") return `EXCLUIR PASTA ${directory}`;
  if (action === "batch_delete") return `EXCLUIR ${files.length} ARQUIVOS`;
  if (action === "batch_duplicate") return `DUPLICAR ${files.length} ARQUIVOS`;
  if (action === "batch_move") return `MOVER ${files.length} ARQUIVOS -> ${target}`;
  if (action === "queue_add") return `ADICIONAR ${files.length} ARQUIVOS NA FILA`;
  if (action === "queue_remove") return `REMOVER ${jobCount} ITENS DA FILA`;
  return "";
}

function readQueueJobs(response: GcodeManagerResponse | null) {
  const queue = response?.result.queue as Record<string, unknown> | undefined;
  const result = queue?.result as Record<string, unknown> | undefined;
  const jobs = Array.isArray(result?.queued_jobs) ? result.queued_jobs : [];
  return jobs.slice(0, 10).flatMap((job) => {
    if (!job || typeof job !== "object") return [];
    const item = job as Record<string, unknown>;
    const id = String(item.job_id ?? "");
    if (!id) return [];
    return [{ id, filename: String(item.filename ?? id) }];
  });
}

function summarizeQueue(response: GcodeManagerResponse | null) {
  if (!response) return "Carregando fila.";
  if (response.status !== "executed") return response.blockers.join(" ") || response.summary;
  const queue = response.result.queue as Record<string, unknown> | undefined;
  const result = queue?.result as Record<string, unknown> | undefined;
  const queuedJobs = Array.isArray(result?.queued_jobs) ? result.queued_jobs.length : 0;
  const state = typeof result?.queue_state === "string" ? result.queue_state : "ready";
  return `${queuedJobs} item(ns) · ${state}`;
}
