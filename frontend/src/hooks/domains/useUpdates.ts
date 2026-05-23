import React from "react";
import { updatesApi } from "../../services/updatesApi";
import { readApiError } from "../../services/http";
import { delay, isUpdateTargetConfirmedUpdated, moonrakerWebsocketUrl, parseMoonrakerUpdateMessage } from "../../utils/formatters";
import type { PrinterRecord, UpdateActionResponse, UpdateDialogState, UpdateLogEntry } from "../../types";
import type { AlertCenterItem, UpdateStatusResponse } from "../../alertCenter";
import type { SetActiveSection, SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseUpdatesOptions = {
  selectedPrinter: PrinterRecord | undefined;
  selectedPrinterId: number | null;
  loadOperationStatus: (printerId: number, options?: { preserveData?: boolean }) => Promise<void>;
  loadPrinterAudit: (printerId: number) => Promise<void>;
  loadPrinterChecklist: (printerId: number) => Promise<void>;
  loadPrinterHealth: (printerId: number) => Promise<void>;
  setActiveSection: SetActiveSection;
  setAlertCenterOpen: React.Dispatch<React.SetStateAction<boolean>>;
  setError: SetError;
  setLoading: SetLoading;
};

export function useUpdates(options: UseUpdatesOptions) {
  const {
    selectedPrinter,
    selectedPrinterId,
    loadOperationStatus,
    loadPrinterAudit,
    loadPrinterChecklist,
    loadPrinterHealth,
    setActiveSection,
    setAlertCenterOpen,
    setError,
    setLoading,
  } = options;
  const [updateStatus, setUpdateStatus] = React.useState<UpdateStatusResponse | null>(null);
  const [updateActionResult, setUpdateActionResult] = React.useState<UpdateActionResponse | null>(null);
  const [updateDialog, setUpdateDialog] = React.useState<UpdateDialogState | null>(null);
  const [updateLogs, setUpdateLogs] = React.useState<UpdateLogEntry[]>([]);
  const updateSocketRef = React.useRef<WebSocket | null>(null);
  const updateLogIdRef = React.useRef(0);

  async function loadUpdateStatus(printerId: number): Promise<UpdateStatusResponse | null> {
    const response = await updatesApi.status(printerId);
    if (!response.ok) {
      return null;
    }
    const status = (await response.json()) as UpdateStatusResponse;
    setUpdateStatus(status);
    setError(null);
    return status;
  }

  async function refreshUpdateStatus(componentName?: string) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    setUpdateActionResult(null);
    try {
      const response = await updatesApi.refresh(selectedPrinterId, { name: componentName ?? null });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      setUpdateActionResult((await response.json()) as UpdateActionResponse);
      await loadUpdateStatus(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleAlertCenterAction(item: AlertCenterItem) {
    if (!selectedPrinterId) {
      return;
    }
    if (item.actionKind === "open_updates") {
      setActiveSection("updates");
      setAlertCenterOpen(false);
      return;
    }
    if (item.actionKind === "run_update") {
      setActiveSection("updates");
      setAlertCenterOpen(false);
      openUpdateDialog(item.target ?? "all");
      return;
    }
    if (item.actionKind === "refresh_update") {
      await refreshUpdateStatus(item.target);
      return;
    }
    if (item.actionKind === "open_monitoring") {
      setActiveSection("monitoring");
      setAlertCenterOpen(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await Promise.allSettled([
        loadPrinterChecklist(selectedPrinterId),
        loadOperationStatus(selectedPrinterId),
        loadPrinterAudit(selectedPrinterId),
        loadPrinterHealth(selectedPrinterId),
        loadUpdateStatus(selectedPrinterId),
      ]);
    } finally {
      setLoading(false);
    }
  }

  function appendUpdateLog(level: UpdateLogEntry["level"], message: string) {
    const id = updateLogIdRef.current + 1;
    updateLogIdRef.current = id;
    setUpdateLogs((currentLogs) => [
      ...currentLogs,
      {
        id,
        level,
        message,
        time: new Date().toLocaleTimeString("pt-BR", { hour12: false }),
      },
    ]);
  }

  function openUpdateDialog(target: string) {
    if (!selectedPrinterId) {
      return;
    }
    const selectedLabel = target === "all" ? "todos os componentes" : target;
    setError(null);
    setUpdateActionResult(null);
    setUpdateLogs([]);
    updateLogIdRef.current = 0;
    setUpdateDialog({ open: true, target, label: selectedLabel, phase: "confirm" });
  }

  function closeUpdateSocket() {
    updateSocketRef.current?.close();
    updateSocketRef.current = null;
  }

  function connectUpdateSocket(printer: PrinterRecord) {
    closeUpdateSocket();
    const websocketUrl = moonrakerWebsocketUrl(printer.moonraker_url);
    if (!websocketUrl) {
      appendUpdateLog("warning", "Nao foi possivel montar a URL WebSocket do Moonraker. O update continua sem log ao vivo.");
      return;
    }
    appendUpdateLog("info", `Conectando ao log ao vivo em ${websocketUrl}`);
    const socket = new WebSocket(websocketUrl);
    updateSocketRef.current = socket;
    socket.onopen = () => {
      socket.send(
        JSON.stringify({
          jsonrpc: "2.0",
          method: "server.connection.identify",
          params: {
            client_name: "Printora",
            version: "0.1.8",
            type: "web",
            url: "https://github.com/printora/printora",
          },
          id: 1,
        }),
      );
      appendUpdateLog("success", "Log ao vivo conectado.");
    };
    socket.onerror = () => appendUpdateLog("warning", "WebSocket do Moonraker indisponivel. O update continua via HTTP.");
    socket.onclose = () => {
      if (updateSocketRef.current === socket) {
        appendUpdateLog("warning", "Conexao de log encerrada. Moonraker pode estar reiniciando.");
      }
    };
    socket.onmessage = (event) => {
      const updateMessage = parseMoonrakerUpdateMessage(event.data);
      if (!updateMessage) {
        return;
      }
      appendUpdateLog(updateMessage.complete ? "success" : "info", updateMessage.message);
      if (updateMessage.complete) {
        setUpdateDialog((currentDialog) =>
          currentDialog && currentDialog.phase === "running" ? { ...currentDialog, phase: "done" } : currentDialog,
        );
      }
    };
  }

  async function runUpdate(target: string) {
    if (!selectedPrinterId || !selectedPrinter) {
      return;
    }
    setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "running" } : currentDialog));
    connectUpdateSocket(selectedPrinter);
    appendUpdateLog("info", `Solicitando update de ${target === "all" ? "todos os componentes" : target}.`);
    setLoading(true);
    setError(null);
    setUpdateActionResult(null);
    try {
      const response = await updatesApi.run(selectedPrinterId, { target });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const actionResult = (await response.json()) as UpdateActionResponse;
      setUpdateActionResult(actionResult);
      appendUpdateLog("success", actionResult.message);
      await loadUpdateStatus(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
      setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "done" } : currentDialog));
    } catch (err) {
      const latestStatus = await reloadUpdateStatusAfterUpdateError(selectedPrinterId, target);
      await loadPrinterHealth(selectedPrinterId);
      if (isUpdateTargetConfirmedUpdated(latestStatus, target)) {
        setUpdateActionResult({
          safe_mode: "moonraker_update_manager",
          action: "update",
          target,
          accepted: true,
          message:
            "Update aplicado. O Moonraker ficou temporariamente indisponível no fim da operação, mas a reanálise confirmou que está atualizado.",
          result: {},
        });
        appendUpdateLog(
          "success",
          "Update confirmado apos reanalise. O erro HTTP provavelmente veio de reinicio temporario do Moonraker.",
        );
        setError(null);
        setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "done" } : currentDialog));
      } else {
        const errorMessage = unknownErrorMessage(err);
        appendUpdateLog("error", errorMessage);
        setError(errorMessage);
        setUpdateDialog((currentDialog) => (currentDialog ? { ...currentDialog, phase: "failed" } : currentDialog));
      }
    } finally {
      setLoading(false);
    }
  }

  async function reloadUpdateStatusAfterUpdateError(printerId: number, target: string): Promise<UpdateStatusResponse | null> {
    const retryDelaysMs = [0, 1500, 3500];
    let latestStatus: UpdateStatusResponse | null = null;
    for (const retryDelayMs of retryDelaysMs) {
      if (retryDelayMs > 0) {
        appendUpdateLog("info", "Revalidando status do Update Manager apos indisponibilidade temporaria.");
        await delay(retryDelayMs);
      }
      try {
        latestStatus = await loadUpdateStatus(printerId);
      } catch {
        latestStatus = null;
      }
      if (isUpdateTargetConfirmedUpdated(latestStatus, target)) {
        return latestStatus;
      }
    }
    return latestStatus;
  }

  React.useEffect(() => () => closeUpdateSocket(), []);

  return {
    appendUpdateLog,
    closeUpdateSocket,
    connectUpdateSocket,
    handleAlertCenterAction,
    loadUpdateStatus,
    openUpdateDialog,
    refreshUpdateStatus,
    reloadUpdateStatusAfterUpdateError,
    runUpdate,
    setUpdateActionResult,
    setUpdateDialog,
    setUpdateLogs,
    setUpdateStatus,
    updateActionResult,
    updateDialog,
    updateLogIdRef,
    updateLogs,
    updateSocketRef,
    updateStatus,
  };
}
