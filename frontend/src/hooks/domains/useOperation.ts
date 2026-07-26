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
  const [operationStatusLoading, setOperationStatusLoading] = React.useState(false);
  const operationStatusRequestSequence = React.useRef(0);
  const operationStatusRequests = React.useRef(new Map<number, Promise<void>>());
  const [operationActionPreview, setOperationActionPreview] = React.useState<OperationActionPreview | null>(null);
  const [operationActionHistory, setOperationActionHistory] = React.useState<OperationActionPreviewRecord[]>([]);
  const [operationExecutionHistory, setOperationExecutionHistory] = React.useState<OperationActionExecutionAttempt[]>([]);
  const [operationActionParameters, setOperationActionParameters] = React.useState<Record<string, Record<string, string>>>({});
  const [operationExecutionPhrase, setOperationExecutionPhrase] = React.useState("");
  const [operationExecutionAttempt, setOperationExecutionAttempt] = React.useState<OperationActionExecutionAttempt | null>(null);

  function loadOperationStatus(printerId: number, options?: { preserveData?: boolean }) {
    const pendingRequest = operationStatusRequests.current.get(printerId);
    if (pendingRequest) {
      return pendingRequest;
    }
    const requestSequence = operationStatusRequestSequence.current + 1;
    operationStatusRequestSequence.current = requestSequence;
    const preserveData = Boolean(options?.preserveData);
    setOperationStatus((current) => (
      preserveData && current?.printer_id === printerId ? current : null
    ));
    if (!preserveData) {
      setOperationActionPreview(null);
      setOperationExecutionPhrase("");
      setOperationExecutionAttempt(null);
    }
    setOperationStatusLoading(true);
    const request = Promise.resolve()
      .then(() => operationApi.status(printerId))
      .then(async (response) => {
        if (!response.ok) {
          return;
        }
        const nextStatus = (await response.json()) as OperationStatusResponse;
        if (operationStatusRequestSequence.current !== requestSequence) {
          return;
        }
        setOperationStatus((current) => mergeOperationStatus(preserveData ? current : null, nextStatus));
      })
      .finally(() => {
        operationStatusRequests.current.delete(printerId);
        setOperationStatusLoading(operationStatusRequests.current.size > 0);
      });
    operationStatusRequests.current.set(printerId, request);
    return request;
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
    operationStatusLoading,
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

const LAST_KNOWN_MISCELLANEOUS_KEYS = [
  "progress",
  "progress_source",
  "file_progress",
  "file_position",
  "message",
  "print_state",
  "filename",
  "print_duration",
  "total_duration",
  "estimated_time",
  "remaining_time",
  "current_layer",
  "total_layers",
  "layer_source",
  "thumbnail",
  "layer_preview",
  "slicer",
  "slicer_version",
  "filament_total",
  "filament_weight_total",
  "object_height",
  "layer_height",
  "first_layer_height",
  "nozzle_diameter",
  "filament_type",
  "filament_name",
  "gcode_files",
] satisfies Array<keyof OperationStatusResponse["miscellaneous"]>;

const PRINT_SESSION_MISCELLANEOUS_KEYS = [
  "progress",
  "progress_source",
  "file_progress",
  "file_position",
  "message",
  "print_state",
  "filename",
  "print_duration",
  "total_duration",
  "estimated_time",
  "remaining_time",
  "current_layer",
  "total_layers",
  "layer_source",
  "thumbnail",
  "layer_preview",
  "slicer",
  "slicer_version",
  "filament_total",
  "filament_weight_total",
  "object_height",
  "layer_height",
  "first_layer_height",
  "nozzle_diameter",
  "filament_type",
  "filament_name",
] satisfies Array<keyof OperationStatusResponse["miscellaneous"]>;
const PRINT_SESSION_MISCELLANEOUS_KEY_SET = new Set<keyof OperationStatusResponse["miscellaneous"]>(PRINT_SESSION_MISCELLANEOUS_KEYS);

function mergeOperationStatus(previous: OperationStatusResponse | null, next: OperationStatusResponse): OperationStatusResponse {
  const merged = preserveLastKnownOperationData(previous, next);
  const sameScope =
    previous?.printer_id === merged.printer_id &&
    (previous.miscellaneous.filename || "") === (merged.miscellaneous.filename || "");
  const liveRow = liveTemperatureHistoryRow(merged);
  const rows = dedupeTemperatureHistoryRows([
    ...(sameScope ? previous?.temperature_history ?? [] : []),
    ...(merged.temperature_history ?? []),
    ...(liveRow ? [liveRow] : []),
  ]);
  return { ...merged, temperature_history: rows.slice(-MAX_LOCAL_TEMPERATURE_HISTORY_ROWS) };
}

function preserveLastKnownOperationData(previous: OperationStatusResponse | null, next: OperationStatusResponse): OperationStatusResponse {
  if (!previous || previous.printer_id !== next.printer_id) {
    return next;
  }
  const previousFilename = (previous.miscellaneous.filename ?? "").trim();
  const nextFilename = (next.miscellaneous.filename ?? "").trim();
  if (previousFilename && nextFilename && previousFilename !== nextFilename) {
    return next;
  }

  const miscellaneous: Record<string, unknown> = { ...previous.miscellaneous, ...next.miscellaneous };
  const nextPrintIdle = isIdlePrintState(next.miscellaneous.print_state);
  const shouldKeepPreviousPrintSession =
    isActivePrintState(previous.miscellaneous.print_state) &&
    next.data_state !== "live" &&
    (nextPrintIdle || isMissingOperationValue(next.miscellaneous.print_state));
  if (nextPrintIdle && !shouldKeepPreviousPrintSession) {
    PRINT_SESSION_MISCELLANEOUS_KEYS.forEach((key) => {
      miscellaneous[key] = next.miscellaneous[key] ?? null;
    });
  }
  if (shouldKeepPreviousPrintSession) {
    PRINT_SESSION_MISCELLANEOUS_KEYS.forEach((key) => {
      const previousValue = previous.miscellaneous[key];
      if (!isMissingOperationValue(previousValue)) {
        miscellaneous[key] = previousValue;
      }
    });
  }
  LAST_KNOWN_MISCELLANEOUS_KEYS.forEach((key) => {
    if (nextPrintIdle && !shouldKeepPreviousPrintSession && PRINT_SESSION_MISCELLANEOUS_KEY_SET.has(key)) {
      return;
    }
    const previousValue = previous.miscellaneous[key];
    const nextValue = next.miscellaneous[key];
    if (isMissingOperationValue(nextValue) && !isMissingOperationValue(previousValue)) {
      miscellaneous[key] = previousValue;
    }
  });

  return {
    ...next,
    agent: next.agent?.version || next.agent?.expected_version ? next.agent : previous.agent,
    system_loads: next.system_loads.length ? next.system_loads : previous.system_loads,
    temperatures: next.temperatures.length ? next.temperatures : previous.temperatures,
    toolhead: hasOperationObject(next.toolhead) ? next.toolhead : previous.toolhead,
    extruder: hasOperationObject(next.extruder) ? next.extruder : previous.extruder,
    miscellaneous: miscellaneous as OperationStatusResponse["miscellaneous"],
  };
}

function isMissingOperationValue(value: unknown) {
  return value === null || typeof value === "undefined" || value === "" || (Array.isArray(value) && value.length === 0);
}

function isIdlePrintState(value?: string | null) {
  const state = (value ?? "").trim().toLowerCase();
  return state === "standby" || state === "complete" || state === "cancelled" || state === "canceled" || state === "error";
}

function isActivePrintState(value?: string | null) {
  const state = (value ?? "").trim().toLowerCase();
  return Boolean(state) && !isIdlePrintState(state);
}

function hasOperationObject(value: Record<string, unknown>) {
  return Object.keys(value).length > 0;
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
