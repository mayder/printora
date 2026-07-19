import React from "react";
import { operationApi } from "../../services/operationApi";
import type {
  OperationAction,
  OperationActionExecutionAttempt,
  OperationActionPreview,
  OperationActionPreviewRecord,
  OperationStatusResponse,
  OperationTemperatureHistoryRow,
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
    const preserveData = Boolean(options?.preserveData);
    if (!preserveData) {
      setOperationStatus(null);
      setOperationActionPreview(null);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
    }
    const response = await operationApi.status(printerId);
    if (!response.ok) {
      return;
    }
    const nextStatus = (await response.json()) as OperationStatusResponse;
    setOperationStatus((current) => mergeLiveTemperatureHistory(preserveData ? current : null, nextStatus));
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
      setActiveSection("monitoring");
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function previewOperationAction(action: OperationAction, parameterOverride?: Record<string, string | number>) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora para gerar a prévia da ação.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.preview(selectedPrinterId, {
        action_id: action.id,
        parameters: buildOperationActionPayload(parameterOverride ?? operationActionParameters[action.id] ?? {}),
      });
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

  async function preflightOperationAction(action: OperationAction, parameterOverride?: Record<string, string | number>) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora para validar o preflight da ação.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.preflight(selectedPrinterId, {
        action_id: action.id,
        parameters: buildOperationActionPayload(parameterOverride ?? operationActionParameters[action.id] ?? {}),
      });
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

  async function executeOperationAction(action: OperationAction, parameterOverride?: Record<string, string | number>) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora para executar a ação.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await operationApi.executeDirect(selectedPrinterId, {
        action_id: action.id,
        parameters: buildOperationActionPayload(parameterOverride ?? operationActionParameters[action.id] ?? {}),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setOperationExecutionAttempt((await response.json()) as OperationActionExecutionAttempt);
      setOperationActionPreview(null);
      await Promise.all([
        loadOperationActionHistory(selectedPrinterId),
        loadOperationExecutionHistory(selectedPrinterId),
        loadOperationStatus(selectedPrinterId, { preserveData: true }),
      ]);
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
    executeOperationAction,
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

const MAX_LOCAL_TEMPERATURE_HISTORY_ROWS = 1440;

function mergeLiveTemperatureHistory(previous: OperationStatusResponse | null, next: OperationStatusResponse): OperationStatusResponse {
  const sameScope =
    previous?.printer_id === next.printer_id &&
    (previous.miscellaneous.filename || "") === (next.miscellaneous.filename || "");
  const liveRow = liveTemperatureHistoryRow(next);
  const rows = dedupeTemperatureHistoryRows([
    ...(sameScope ? previous?.temperature_history ?? [] : []),
    ...(next.temperature_history ?? []),
    ...(liveRow ? [liveRow] : []),
  ]);
  return { ...next, temperature_history: rows.slice(-MAX_LOCAL_TEMPERATURE_HISTORY_ROWS) };
}

function liveTemperatureHistoryRow(status: OperationStatusResponse): OperationTemperatureHistoryRow | null {
  const readings = status.temperatures
    .filter((reading) => typeof reading.temperature === "number")
    .map((reading) => ({
      name: reading.name,
      temperature: reading.temperature,
      target: typeof reading.target === "number" ? reading.target : null,
    }));
  if (!readings.length) {
    return null;
  }
  return {
    snapshot_id: null,
    created_at: new Date().toISOString(),
    readings,
  };
}

function dedupeTemperatureHistoryRows(rows: OperationTemperatureHistoryRow[]) {
  const uniqueRows = new Map<string, OperationTemperatureHistoryRow>();
  rows.forEach((row) => {
    if (!row.readings.length) return;
    const key = row.snapshot_id !== null ? `snapshot:${row.snapshot_id}` : `live:${row.created_at}:${temperatureReadingsKey(row)}`;
    uniqueRows.set(key, row);
  });
  return Array.from(uniqueRows.values());
}

function temperatureReadingsKey(row: OperationTemperatureHistoryRow) {
  return row.readings
    .map((reading) => `${reading.name}:${reading.temperature ?? ""}:${reading.target ?? ""}`)
    .join("|");
}
