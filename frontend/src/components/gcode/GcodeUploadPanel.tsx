import React from "react";
import { Play, Upload, X } from "lucide-react";
import { operationApi } from "../../services/operationApi";

type PendingUpload = {
  file: File;
  remoteName: string;
  progress: number;
  state: "pending" | "uploading" | "uploaded" | "failed";
  detail: string;
};

export function GcodeUploadPanel({
  confirmAction,
  directory,
  printerId,
  onUploaded,
  showToast,
}: {
  confirmAction: (options: { tone: "danger" | "warning"; title: string; detail: string; evidence: string; confirmLabel: string }) => Promise<boolean>;
  directory: string;
  printerId: number;
  onUploaded: () => Promise<void>;
  showToast: (toast: { tone: "success" | "warning" | "danger" | "info"; title: string; detail: string }) => void;
}) {
  const inputRef = React.useRef<HTMLInputElement>(null);
  const [uploads, setUploads] = React.useState<PendingUpload[]>([]);
  const [busy, setBusy] = React.useState(false);

  function addFiles(files: FileList | File[]) {
    const accepted = Array.from(files).filter((file) => /\.(gcode|gco|gc|nc|ngc|tap)$/i.test(file.name));
    if (!accepted.length) {
      showToast({ tone: "warning", title: "Arquivo inválido", detail: "Selecione G-code." });
      return;
    }
    setUploads((current) => [
      ...current,
      ...accepted.map((file) => ({
        file,
        remoteName: [directory === "all" ? "" : directory, file.name].filter(Boolean).join("/"),
        progress: 0,
        state: "pending" as const,
        detail: "",
      })),
    ]);
  }

  async function sendAll(startFirstPrint = false) {
    if (busy) return;
    const pendingIndexes = uploads.map((item, index) => ({ item, index })).filter(({ item }) => item.state === "pending" || item.state === "failed");
    if (!pendingIndexes.length) return;
    if (startFirstPrint && pendingIndexes.length !== 1) {
      showToast({ tone: "warning", title: "Seleção inválida", detail: "Escolha um arquivo." });
      return;
    }
    setBusy(true);
    let completed = 0;
    for (const { item, index } of pendingIndexes) {
      const startPrint = startFirstPrint && index === pendingIndexes[0].index;
      const confirmationPhrase = startPrint ? `ENVIAR E IMPRIMIR ${item.remoteName}` : "";
      setUploads((current) => current.map((entry, entryIndex) => entryIndex === index ? { ...entry, state: "uploading", progress: 0, detail: "" } : entry));
      try {
        let result = await operationApi.uploadGcodeFile(printerId, item.file, {
          filename: item.remoteName,
          startPrint,
          confirmationPhrase,
          onProgress: (progress) => setUploads((current) => current.map((entry, entryIndex) => entryIndex === index ? { ...entry, progress } : entry)),
        });
        if (result.status === "blocked" && result.blockers.join(" ").toLowerCase().includes("sobrescr")) {
          const overwritePhrase = `SOBRESCREVER ${item.remoteName}`;
          const confirmed = await confirmAction({
            tone: "warning",
            title: "Arquivo já existe",
            detail: `Sobrescrever ${item.remoteName} na impressora.`,
            evidence: overwritePhrase,
            confirmLabel: "Sobrescrever",
          });
          if (confirmed) {
            result = await operationApi.uploadGcodeFile(printerId, item.file, {
              filename: item.remoteName,
              overwrite: true,
              confirmationPhrase: overwritePhrase,
              onProgress: (progress) => setUploads((current) => current.map((entry, entryIndex) => entryIndex === index ? { ...entry, progress } : entry)),
            });
          }
        }
        const success = result.status === "uploaded" || result.status === "started";
        setUploads((current) => current.map((entry, entryIndex) => entryIndex === index ? {
          ...entry,
          state: success ? "uploaded" : "failed",
          progress: success ? 100 : entry.progress,
          detail: success ? result.summary : result.blockers.join(" ") || result.summary,
        } : entry));
        if (success) completed += 1;
      } catch (error) {
        setUploads((current) => current.map((entry, entryIndex) => entryIndex === index ? {
          ...entry,
          state: "failed",
          detail: error instanceof Error ? error.message : "Falha no envio",
        } : entry));
      }
    }
    setBusy(false);
    if (completed) {
      showToast({ tone: "success", title: startFirstPrint ? "Enviado para impressão" : "Upload concluído", detail: `${completed} arquivo(s).` });
      await onUploaded();
    }
  }

  return (
    <section
      className="gcode-upload-panel"
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        addFiles(event.dataTransfer.files);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".gcode,.gco,.gc,.nc,.ngc,.tap"
        multiple
        hidden
        onChange={(event) => {
          if (event.target.files) addFiles(event.target.files);
          event.target.value = "";
        }}
      />
      <div className="gcode-upload-heading">
        <div>
          <strong>Enviar G-code</strong>
          <span>Arraste ou escolha. Destino: {directory === "all" ? "raiz" : directory}</span>
        </div>
        <button type="button" className="secondary-button" onClick={() => inputRef.current?.click()} disabled={busy}>
          <Upload size={15} />
          Escolher arquivos
        </button>
      </div>
      {uploads.length ? (
        <>
          <ul className="gcode-upload-list">
            {uploads.map((item, index) => (
              <li key={`${item.file.name}-${item.file.lastModified}-${index}`}>
                <div>
                  <strong>{item.remoteName}</strong>
                  <span>{item.state === "uploading" ? `Enviando ${item.progress}%` : item.detail || `${Math.ceil(item.file.size / 1024)} KB · aguardando`}</span>
                </div>
                <progress max={100} value={item.progress} />
                <button type="button" className="icon-button" aria-label={`Remover ${item.file.name}`} disabled={busy} onClick={() => setUploads((current) => current.filter((_, entryIndex) => entryIndex !== index))}>
                  <X size={14} />
                </button>
              </li>
            ))}
          </ul>
          <div className="gcode-upload-actions">
            <button type="button" className="secondary-button" disabled={busy} onClick={() => void sendAll(false)}>
              <Upload size={15} />
              {busy ? "Enviando" : "Enviar"}
            </button>
            <button type="button" className="primary-button" disabled={busy || uploads.filter((item) => item.state !== "uploaded").length !== 1} onClick={() => void sendAll(true)}>
              <Play size={15} />
              Enviar e imprimir
            </button>
          </div>
        </>
      ) : null}
    </section>
  );
}
