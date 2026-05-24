import React from "react";
import { operationApi } from "../../services/operationApi";
import type {
  OperationAction,
  OperationActionExecutionAttempt,
  OperationActionPreview,
  OperationActionPreviewRecord,
  OperationStatusResponse,
} from "../../types";
import { buildOperationActionPayload } from "../../utils/formatters";
import type { SetActiveSection, SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseOperationOptions = {
  selectedPrinterId: number | null;
  setActiveSection: SetActiveSection;
  setError: SetError;
  setLoading: SetLoading;
};

export function useOperation({ selectedPrinterId, setActiveSection, setError, setLoading }: UseOperationOptions) {
  const [operationStatus, setOperationStatus] = React.useState<OperationStatusResponse | null>(null);
  const [operationActionPreview, setOperationActionPreview] = React.useState<OperationActionPreview | null>(null);
  const [operationActionHistory, setOperationActionHistory] = React.useState<OperationActionPreviewRecord[]>([]);
  const [operationExecutionHistory, setOperationExecutionHistory] = React.useState<OperationActionExecutionAttempt[]>([]);
  const [operationActionParameters, setOperationActionParameters] = React.useState<Record<string, Record<string, string>>>({});
  const [operationExecutionPhrase, setOperationExecutionPhrase] = React.useState("");
  const [operationExecutionAttempt, setOperationExecutionAttempt] = React.useState<OperationActionExecutionAttempt | null>(null);

  async function loadOperationStatus(printerId: number, options?: { preserveData?: boolean }) {
    if (!options?.preserveData) {
      setOperationStatus(null);
      setOperationActionPreview(null);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
    }
    const response = await operationApi.status(printerId);
    if (!response.ok) {
      return;
    }
    setOperationStatus((await response.json()) as OperationStatusResponse);
  }

  async function loadOperationActionHistory(printerId: number) {
    const response = await operationApi.actionHistory(printerId);
    if (!response.ok) {
      setOperationActionHistory([]);
      return;
    }
    const payload = (await response.json()) as { previews: OperationActionPreviewRecord[] };
    setOperationActionHistory(payload.previews);
  }

  async function loadOperationExecutionHistory(printerId: number) {
    const response = await operationApi.executionHistory(printerId);
    if (!response.ok) {
      setOperationExecutionHistory([]);
      return;
    }
    const payload = (await response.json()) as { attempts: OperationActionExecutionAttempt[] };
    setOperationExecutionHistory(payload.attempts);
  }

  async function loadOfflineOperationFixture() {
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.offlineFixture();
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationStatus((await response.json()) as OperationStatusResponse);
      setOperationActionPreview(null);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
      setActiveSection("operation");
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function previewOperationAction(action: OperationAction) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora para gerar a prévia da ação.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.preview(selectedPrinterId, { action_id: action.id, parameters: buildOperationActionPayload(operationActionParameters[action.id] ?? {}) });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationActionPreview((await response.json()) as OperationActionPreview);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
      await loadOperationActionHistory(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function preflightOperationAction(action: OperationAction) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora para validar o preflight da ação.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.preflight(selectedPrinterId, { action_id: action.id, parameters: buildOperationActionPayload(operationActionParameters[action.id] ?? {}) });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationActionPreview((await response.json()) as OperationActionPreview);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function updateOperationActionParameter(actionId: string, parameterName: string, value: string) {
    setOperationActionParameters((current) => ({
      ...current,
      [actionId]: {
        ...(current[actionId] ?? {}),
        [parameterName]: value,
      },
    }));
  }

  async function validateOperationExecutionGate() {
    if (!selectedPrinterId || !operationActionPreview?.history_id) {
      setError("Gere uma prévia antes de validar a execução.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.execute(selectedPrinterId, {
        preview_id: operationActionPreview.history_id,
        confirmation_phrase: operationExecutionPhrase,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationExecutionAttempt((await response.json()) as OperationActionExecutionAttempt);
      await loadOperationExecutionHistory(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function resetOperationSelection() {
    setOperationActionHistory([]);
    setOperationExecutionHistory([]);
    setOperationExecutionPhrase("");
    setOperationExecutionAttempt(null);
  }

  return {
    loadOfflineOperationFixture,
    loadOperationActionHistory,
    loadOperationExecutionHistory,
    loadOperationStatus,
    operationActionHistory,
    operationActionParameters,
    operationActionPreview,
    operationExecutionAttempt,
    operationExecutionHistory,
    operationExecutionPhrase,
    operationStatus,
    preflightOperationAction,
    previewOperationAction,
    resetOperationSelection,
    setOperationActionHistory,
    setOperationActionParameters,
    setOperationActionPreview,
    setOperationExecutionAttempt,
    setOperationExecutionHistory,
    setOperationExecutionPhrase,
    setOperationStatus,
    updateOperationActionParameter,
    validateOperationExecutionGate,
  };
}
