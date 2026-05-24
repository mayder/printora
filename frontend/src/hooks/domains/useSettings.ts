import React from "react";
import { canApi } from "../../services/canApi";
import { diagnosticsApi } from "../../services/diagnosticsApi";
import { printerApi } from "../../services/printerApi";
import type { MoonrakerStatus, CanBusRecord, CanBusRecordComparison, CanBusSummary } from "../../types";
import type { AuditResponse, ChecklistResponse, HealthResponse } from "../../alertCenter";
import type { SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseSettingsOptions = {
  selectedPrinterId: number | null;
  setError: SetError;
  setLoading: SetLoading;
};

export function useSettings({ selectedPrinterId, setError, setLoading }: UseSettingsOptions) {
  const [status, setStatus] = React.useState<MoonrakerStatus | null>(null);
  const [checklist, setChecklist] = React.useState<ChecklistResponse | null>(null);
  const [audit, setAudit] = React.useState<AuditResponse | null>(null);
  const [hostAudit, setHostAudit] = React.useState<AuditResponse | null>(null);
  const [health, setHealth] = React.useState<HealthResponse | null>(null);
  const [canRecords, setCanRecords] = React.useState<CanBusRecord[]>([]);
  const [canSummary, setCanSummary] = React.useState<CanBusSummary | null>(null);
  const [canComparison, setCanComparison] = React.useState<CanBusRecordComparison | null>(null);
  const [canInterfaceName, setCanInterfaceName] = React.useState("can0");
  const [canRxError, setCanRxError] = React.useState(0);
  const [canTxError, setCanTxError] = React.useState(0);
  const [canTxRetries, setCanTxRetries] = React.useState(0);
  const [canBusState, setCanBusState] = React.useState("ERROR-ACTIVE");
  const [canBitrate, setCanBitrate] = React.useState(1000000);
  const [canNotes, setCanNotes] = React.useState("");
  const [canRawOutput, setCanRawOutput] = React.useState("");

  async function loadGlobalDiagnostics() {
    const [statusResponse, checklistResponse, hostAuditResponse] = await Promise.allSettled([
      diagnosticsApi.moonrakerStatus(),
      diagnosticsApi.postUpdateChecklist(),
      diagnosticsApi.hostReadOnlyAudit(),
    ]);
    if (statusResponse.status === "fulfilled" && statusResponse.value.ok) {
      setStatus((await statusResponse.value.json()) as MoonrakerStatus);
    }
    if (checklistResponse.status === "fulfilled" && checklistResponse.value.ok) {
      setChecklist((await checklistResponse.value.json()) as ChecklistResponse);
    }
    if (hostAuditResponse.status === "fulfilled" && hostAuditResponse.value.ok) {
      setHostAudit((await hostAuditResponse.value.json()) as AuditResponse);
    }
  }

  async function loadPrinterChecklist(printerId: number) {
    const response = await printerApi.checklist(printerId);
    if (!response.ok) {
      setChecklist(null);
      return;
    }
    setChecklist((await response.json()) as ChecklistResponse);
  }

  async function loadPrinterAudit(printerId: number) {
    setAudit(null);
    const response = await printerApi.audit(printerId);
    if (!response.ok) {
      return;
    }
    setAudit((await response.json()) as AuditResponse);
  }

  async function loadPrinterHealth(printerId: number) {
    const response = await printerApi.health(printerId);
    if (!response.ok) {
      return;
    }
    setHealth((await response.json()) as HealthResponse);
  }

  async function loadCanRecords(printerId: number) {
    const [recordsResponse, summaryResponse] = await Promise.all([
      canApi.records(printerId),
      canApi.summary(printerId),
    ]);
    if (recordsResponse.ok) {
      const payload = (await recordsResponse.json()) as { records: CanBusRecord[] };
      setCanRecords(payload.records);
    }
    if (summaryResponse.ok) {
      setCanSummary((await summaryResponse.json()) as CanBusSummary);
    }
  }

  async function createCanRecord(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await canApi.createRecord(selectedPrinterId, {
        interface_name: canInterfaceName,
        rx_error: canRxError,
        tx_error: canTxError,
        tx_retries: canTxRetries,
        bus_state: canBusState,
        bitrate: canBitrate,
        notes: canNotes,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCanNotes("");
      setCanRawOutput("");
      await loadCanRecords(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function parseCanRawOutput() {
    if (!selectedPrinterId || !canRawOutput.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await canApi.parse(selectedPrinterId, { interface_name: canInterfaceName, output: canRawOutput });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const parsed = (await response.json()) as {
        interface_name: string;
        rx_error: number;
        tx_error: number;
        tx_retries: number;
        bus_state?: string | null;
        bitrate?: number | null;
        notes: string;
      };
      setCanInterfaceName(parsed.interface_name);
      setCanRxError(parsed.rx_error);
      setCanTxError(parsed.tx_error);
      setCanTxRetries(parsed.tx_retries);
      setCanBusState(parsed.bus_state ?? "");
      setCanBitrate(parsed.bitrate ?? 1000000);
      setCanNotes(parsed.notes);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function compareLatestCanRecords() {
    if (!selectedPrinterId || canRecords.length < 2) {
      return;
    }
    const pair = findLatestComparableCanRecords(canRecords);
    if (!pair) {
      setError("Não há duas leituras da mesma interface CAN para comparar.");
      return;
    }
    const { after, before } = pair;
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({
        before_record_id: String(before.id),
        after_record_id: String(after.id),
      });
      const response = await canApi.compare(selectedPrinterId, params);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCanComparison((await response.json()) as CanBusRecordComparison);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function findLatestComparableCanRecords(records: CanBusRecord[]) {
    for (let afterIndex = 0; afterIndex < records.length; afterIndex += 1) {
      const after = records[afterIndex];
      const before = records.slice(afterIndex + 1).find((record) => record.interface_name === after.interface_name);
      if (before) {
        return { after, before };
      }
    }
    return null;
  }

  return {
    audit,
    canBitrate,
    canBusState,
    canComparison,
    canInterfaceName,
    canNotes,
    canRawOutput,
    canRecords,
    canRxError,
    canSummary,
    canTxError,
    canTxRetries,
    checklist,
    compareLatestCanRecords,
    createCanRecord,
    findLatestComparableCanRecords,
    health,
    hostAudit,
    loadCanRecords,
    loadGlobalDiagnostics,
    loadPrinterAudit,
    loadPrinterChecklist,
    loadPrinterHealth,
    parseCanRawOutput,
    setAudit,
    setCanBitrate,
    setCanBusState,
    setCanComparison,
    setCanInterfaceName,
    setCanNotes,
    setCanRawOutput,
    setCanRecords,
    setCanRxError,
    setCanSummary,
    setCanTxError,
    setCanTxRetries,
    setChecklist,
    setHealth,
    setHostAudit,
    setStatus,
    status,
  };
}
