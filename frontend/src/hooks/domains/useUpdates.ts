import React from "react";
import * as authApi from "../../services/authApi";
import { updatesApi } from "../../services/updatesApi";
import { readApiError } from "../../services/http";
import { delay, isUpdateTargetConfirmedUpdated } from "../../utils/formatters";
import { formatTime } from "../../utils/formatters/dates";
import type { AuthUser, UpdateActionResponse, UpdateDialogState, UpdateLogEntry } from "../../types";
import type { ConfirmActionOptions, ShowToastOptions } from "../../types";
import type { AlertCenterItem, UpdateComponent, UpdateStatusResponse } from "../../alertCenter";
import type { SetActiveSection, SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

const RISK_UPDATE_CONFIRMATION_PHRASE = "ATUALIZAR COM RISCO";
const ROLLBACK_CONFIRMATION_PHRASE = "ROLLBACK UPDATE";
const UPDATE_ALERT_ACTION_TIMEOUT_MS = 20000;

type PendingUpdateAction = {
  kind: "silence" | "clear_silence";
  target: string;
} | null;

type UseUpdatesOptions = {
  authUser: AuthUser | null;
  selectedPrinterId: number | null;
  loadOperationStatus: (printerId: number, options?: { preserveData?: boolean }) => Promise<void>;
  loadPrinterAudit: (printerId: number) => Promise<void>;
  loadPrinterChecklist: (printerId: number) => Promise<void>;
  loadPrinterHealth: (printerId: number) => Promise<void>;
  setActiveSection: SetActiveSection;
  setAlertCenterOpen: React.Dispatch<React.SetStateAction<boolean>>;
  confirmAction: (options: ConfirmActionOptions) => Promise<boolean>;
  showToast: (options: ShowToastOptions) => void;
  setError: SetError;
  setLoading: SetLoading;
};

export function useUpdates(options: UseUpdatesOptions) {
  const {
    authUser,
    selectedPrinterId,
    loadOperationStatus,
    loadPrinterAudit,
    loadPrinterChecklist,
    loadPrinterHealth,
    setActiveSection,
    setAlertCenterOpen,
    confirmAction,
    showToast,
    setError,
    setLoading,
  } = options;
  const [updateStatus, setUpdateStatus] = React.useState<UpdateStatusResponse | null>(null);
  const [updateActionResult, setUpdateActionResult] = React.useState<UpdateActionResponse | null>(null);
  const [updateDialog, setUpdateDialog] = React.useState<UpdateDialogState | null>(null);
  const [updateLogs, setUpdateLogs] = React.useState<UpdateLogEntry[]>([]);
  const [pendingUpdateAction, setPendingUpdateAction] = React.useState<PendingUpdateAction>(null);
  const updateLogIdRef = React.useRef(0);

  function patchUpdateDialog(patch: Partial<UpdateDialogState>) {
    setUpdateDialog((current) => (current ? { ...current, ...patch } : current));
  }

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
      window.setTimeout(() => void refreshPostUpdateContext(selectedPrinterId), 2500);
      window.setTimeout(() => void refreshPostUpdateContext(selectedPrinterId), 15000);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function silenceUpdateAlert(component: UpdateComponent) {
    if (!selectedPrinterId) {
      return;
    }
    const confirmed = await confirmAction({
      tone: "warning",
      title: "Silenciar versão",
      detail: `Silenciar alertas desta versão de ${component.title}. O card continua com as ações disponíveis.`,
      evidence: `${component.current_version ?? "-"} → ${component.remote_version ?? component.full_version ?? "-"}`,
      confirmLabel: "Silenciar versão",
    });
    if (!confirmed) {
      return;
    }
    setLoading(true);
    setPendingUpdateAction({ kind: "silence", target: component.name });
    setError(null);
    setUpdateActionResult(null);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), UPDATE_ALERT_ACTION_TIMEOUT_MS);
    try {
      const response = await updatesApi.silence(selectedPrinterId, {
        target: component.name,
        current_version: component.current_version,
        remote_version: component.remote_version,
        full_version: component.full_version,
        commits_behind_count: component.commits_behind_count,
        package_count: component.package_count,
        warnings: component.warnings,
        anomalies: component.anomalies,
        reason: "Usuário decidiu aguardar próxima versão.",
      }, {
        signal: controller.signal,
      });
      if (!response.ok) {
        if (response.status === 405) {
          throw new Error("Esta função ainda não está disponível nesta versão. Atualize o Printora e tente novamente.");
        }
        throw new Error(await readApiError(response));
      }
      await refreshPostUpdateContext(selectedPrinterId);
      showToast({
        tone: "success",
        title: "Versão silenciada",
        detail: "O alerta volta automaticamente quando surgir outra versão.",
      });
    } catch (err) {
      const message = err instanceof DOMException && err.name === "AbortError"
        ? "A solicitação demorou além do esperado. Tente novamente."
        : unknownErrorMessage(err);
      setError(message);
      showToast({ tone: "danger", title: "Falha ao silenciar versão", detail: message });
    } finally {
      window.clearTimeout(timeoutId);
      setPendingUpdateAction(null);
      setLoading(false);
    }
  }

  async function clearUpdateAlertSilence(component: UpdateComponent) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setPendingUpdateAction({ kind: "clear_silence", target: component.name });
    setError(null);
    setUpdateActionResult(null);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), UPDATE_ALERT_ACTION_TIMEOUT_MS);
    try {
      const response = await updatesApi.clearSilence(selectedPrinterId, {
        target: component.name,
        current_version: component.current_version,
        remote_version: component.remote_version,
        full_version: component.full_version,
        commits_behind_count: component.commits_behind_count,
        package_count: component.package_count,
        warnings: component.warnings,
        anomalies: component.anomalies,
      }, { signal: controller.signal });
      if (!response.ok) {
        if (response.status === 405) {
          throw new Error("Esta função ainda não está disponível nesta versão. Atualize o Printora e tente novamente.");
        }
        throw new Error(await readApiError(response));
      }
      await refreshPostUpdateContext(selectedPrinterId);
      showToast({
        tone: "success",
        title: "Alerta reativado",
        detail: `${component.title} voltou a contar nos alertas ativos.`,
      });
    } catch (err) {
      const message = err instanceof DOMException && err.name === "AbortError"
        ? "A solicitação demorou além do esperado. Tente novamente."
        : unknownErrorMessage(err);
      setError(message);
      showToast({ tone: "danger", title: "Falha ao reativar alerta", detail: message });
    } finally {
      window.clearTimeout(timeoutId);
      setPendingUpdateAction(null);
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
    if (item.actionKind === "open_maintenance") {
      setActiveSection("maintenance");
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
        time: formatTime(),
      },
    ]);
  }

  function openUpdateDialog(target: string) {
    if (!selectedPrinterId) {
      return;
    }
    const selectedLabel = target === "all" ? "todos os componentes" : target;
    const riskyComponents = riskyComponentsForTarget(target, updateStatus);
    setError(null);
    setUpdateActionResult(null);
    setUpdateLogs([]);
    updateLogIdRef.current = 0;
    setUpdateDialog({
      open: true,
      target,
      label: selectedLabel,
      action: "update",
      phase: "confirm",
      requiresConfirmation: riskyComponents.length > 0,
      confirmationPhrase: "",
      authorizationCredential: "",
      authorizationError: null,
      riskReason: riskyComponents.map((component) => `${component.title}: ${component.risk_reason ?? "risco operacional alto"}`).join(" "),
    });
  }

  function openRollbackDialog(component: UpdateComponent) {
    if (!selectedPrinterId) {
      return;
    }
    setError(null);
    setUpdateActionResult(null);
    setUpdateLogs([]);
    updateLogIdRef.current = 0;
    setUpdateDialog({
      open: true,
      target: component.name,
      label: component.title,
      action: "rollback",
      phase: "confirm",
      requiresConfirmation: true,
      confirmationPhrase: "",
      authorizationCredential: "",
      authorizationError: null,
      riskReason: `Voltar ${component.title} para ${component.rollback_version ?? "a versão anterior"} usando o rollback do Moonraker.`,
    });
  }

  async function refreshPostUpdateContext(printerId: number) {
    await Promise.allSettled([
      loadUpdateStatus(printerId),
      loadPrinterHealth(printerId),
      loadPrinterChecklist(printerId),
      loadOperationStatus(printerId, { preserveData: true }),
      loadPrinterAudit(printerId),
    ]);
  }

  async function closeUpdateDialog() {
    setUpdateDialog(null);
    if (selectedPrinterId) {
      await refreshPostUpdateContext(selectedPrinterId);
    }
  }

  async function runUpdate(target: string) {
    if (!selectedPrinterId) {
      return;
    }
    const stepUpToken = await requestUpdateAuthorization();
    if (stepUpToken === null) {
      return;
    }
    patchUpdateDialog({ phase: "running" });
    appendUpdateLog("info", `Solicitando update de ${target === "all" ? "todos os componentes" : target}.`);
    setLoading(true);
    setError(null);
    setUpdateActionResult(null);
    try {
      const confirmationPhrase = updateDialog?.target === target ? updateDialog.confirmationPhrase : "";
      const response = await updatesApi.run(selectedPrinterId, { target, confirmation_phrase: confirmationPhrase }, stepUpToken);
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const actionResult = (await response.json()) as UpdateActionResponse;
      setUpdateActionResult(actionResult);
      appendUpdateLog("success", actionResult.message);
      const confirmedStatus = await pollUpdateCompletion(selectedPrinterId, target);
      await refreshPostUpdateContext(selectedPrinterId);
      if (isUpdateTargetConfirmedUpdated(confirmedStatus, target)) {
        patchUpdateDialog({ phase: "done" });
      } else {
        appendUpdateLog("warning", "Update solicitado, mas o status final ainda nao foi confirmado pelo Moonraker.");
        patchUpdateDialog({ phase: "failed" });
      }
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
        patchUpdateDialog({ phase: "done" });
      } else {
        const errorMessage = unknownErrorMessage(err);
        appendUpdateLog("error", errorMessage);
        setError(errorMessage);
        patchUpdateDialog({ phase: "failed" });
      }
    } finally {
      setLoading(false);
    }
  }

  async function runRollback(target: string) {
    if (!selectedPrinterId) {
      return;
    }
    const stepUpToken = await requestUpdateAuthorization();
    if (stepUpToken === null) {
      return;
    }
    const confirmationPhrase = updateDialog?.target === target ? updateDialog.confirmationPhrase : "";
    patchUpdateDialog({ phase: "running" });
    appendUpdateLog("info", `Solicitando rollback de ${target}.`);
    setLoading(true);
    setError(null);
    setUpdateActionResult(null);
    try {
      const response = await updatesApi.rollback(selectedPrinterId, { target, confirmation_phrase: confirmationPhrase }, stepUpToken);
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const actionResult = (await response.json()) as UpdateActionResponse;
      setUpdateActionResult(actionResult);
      appendUpdateLog("success", actionResult.message);
      await delay(2500);
      await refreshPostUpdateContext(selectedPrinterId);
      patchUpdateDialog({ phase: "done" });
    } catch (err) {
      const errorMessage = unknownErrorMessage(err);
      appendUpdateLog("error", errorMessage);
      setError(errorMessage);
      await refreshPostUpdateContext(selectedPrinterId);
      patchUpdateDialog({ phase: "failed" });
    } finally {
      setLoading(false);
    }
  }

  async function requestUpdateAuthorization(): Promise<string | undefined | null> {
    if (!authUser) {
      patchUpdateDialog({ authorizationError: "Sessão expirada." });
      return null;
    }
    const credential = updateDialog?.authorizationCredential.trim() ?? "";
    const missingMessage = `Informe ${authUser.mfa_enabled ? "o código 2FA" : "a senha atual"} para autorizar.`;
    if (!credential) {
      patchUpdateDialog({ authorizationError: missingMessage });
      return null;
    }
    setLoading(true);
    patchUpdateDialog({ authorizationError: null });
    try {
      const proof = await authApi.createStepUpToken({
        purpose: "setup_physical_operation",
        password: authUser.mfa_enabled ? undefined : credential,
        code: authUser.mfa_enabled ? credential : undefined,
      }, { store: false });
      patchUpdateDialog({ authorizationCredential: "", authorizationError: null });
      return proof.step_up_token;
    } catch (err) {
      const detail = unknownErrorMessage(err);
      patchUpdateDialog({ authorizationError: `Autorização recusada. ${detail}` });
      return null;
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

  async function pollUpdateCompletion(printerId: number, target: string): Promise<UpdateStatusResponse | null> {
    const retryDelaysMs = [2500, 5000, 8000, 12000, 16000];
    let latestStatus: UpdateStatusResponse | null = null;
    for (const retryDelayMs of retryDelaysMs) {
      appendUpdateLog("info", "Aguardando o Moonraker confirmar o status final do update.");
      await delay(retryDelayMs);
      try {
        latestStatus = await loadUpdateStatus(printerId);
      } catch {
        latestStatus = null;
      }
      await loadPrinterHealth(printerId);
      if (isUpdateTargetConfirmedUpdated(latestStatus, target)) {
        return latestStatus;
      }
    }
    return latestStatus;
  }

  return {
    appendUpdateLog,
    closeUpdateDialog,
    handleAlertCenterAction,
    loadUpdateStatus,
    openRollbackDialog,
    openUpdateDialog,
    patchUpdateDialog,
    refreshUpdateStatus,
    silenceUpdateAlert,
    clearUpdateAlertSilence,
    reloadUpdateStatusAfterUpdateError,
    runUpdate,
    runRollback,
    setUpdateActionResult,
    setUpdateDialog,
    setUpdateLogs,
    setUpdateStatus,
    updateActionResult,
    updateDialog,
    updateLogIdRef,
    updateLogs,
    updateStatus,
    pendingUpdateAction,
  };
}

function riskyComponentsForTarget(target: string, status: UpdateStatusResponse | null): UpdateComponent[] {
  if (!status) {
    return [];
  }
  const candidates =
    target === "all"
      ? status.components.filter((component) => component.can_update)
      : status.components.filter((component) => component.name === target && component.can_update);
  return candidates.filter((component) => component.requires_confirmation);
}
