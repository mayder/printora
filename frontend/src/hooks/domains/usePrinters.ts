import React from "react";
import { useSelectedPrinterPreference } from "../../selectedPrinterPreference";
import { printerApi } from "../../services/printerApi";
import type {
  ConnectionCheckResult,
  DiscoveredPrinter,
  MoonrakerStatus,
  PrinterConnectionTestResponse,
  PrinterDiscoveryResponse,
  PrinterRecord,
} from "../../types";
import { extractHost, validatePrinterConnectionInput } from "../../utils/formatters";
import type { SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UsePrintersOptions = {
  loadOperationStatus: (printerId: number) => Promise<void>;
  loadPrinterContext: (printerId: number) => Promise<void>;
  loadPrinterHealth: (printerId: number) => Promise<void>;
  loadUpdateStatus: (printerId: number) => Promise<unknown>;
  onSelectPrinter: () => void;
  setError: SetError;
  setLoading: SetLoading;
  setStatus: React.Dispatch<React.SetStateAction<MoonrakerStatus | null>>;
};

export function usePrinters(options: UsePrintersOptions) {
  const {
    loadOperationStatus,
    loadPrinterContext,
    loadPrinterHealth,
    loadUpdateStatus,
    onSelectPrinter,
    setError,
    setLoading,
    setStatus,
  } = options;
  const [printers, setPrinters] = React.useState<PrinterRecord[]>([]);
  const [selectedPrinterId, setSelectedPrinterId] = useSelectedPrinterPreference();
  const [discovery, setDiscovery] = React.useState<PrinterDiscoveryResponse | null>(null);
  const [printerModalOpen, setPrinterModalOpen] = React.useState(false);
  const [printerModalMode, setPrinterModalMode] = React.useState<"create" | "edit">("create");
  const [editingPrinterId, setEditingPrinterId] = React.useState<number | null>(null);
  const [newPrinterName, setNewPrinterName] = React.useState("Voron - Mayder");
  const [newPrinterUrl, setNewPrinterUrl] = React.useState("http://voron.local:7125");
  const [newPrinterSshHost, setNewPrinterSshHost] = React.useState("");
  const [newPrinterSshPort, setNewPrinterSshPort] = React.useState(22);
  const [newPrinterSshUser, setNewPrinterSshUser] = React.useState("");
  const [newPrinterSshCredential, setNewPrinterSshCredential] = React.useState("");
  const [printerConnectionTest, setPrinterConnectionTest] = React.useState<PrinterConnectionTestResponse | null>(null);

  const selectedPrinter = printers.find((printer) => printer.id === selectedPrinterId);

  async function loadPrinters() {
    const response = await printerApi.list();
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { printers: PrinterRecord[] };
    setPrinters(payload.printers);
    const nextSelected = payload.printers.some((printer) => printer.id === selectedPrinterId) ? selectedPrinterId : payload.printers[0]?.id ?? null;
    setSelectedPrinterId(nextSelected);
    if (nextSelected) {
      await loadPrinterContext(nextSelected);
    }
  }

  function selectPrinter(printerId: number) {
    setSelectedPrinterId(printerId);
    onSelectPrinter();
    void loadPrinterContext(printerId);
  }

  async function createPrinter(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const validationError = validatePrinterConnectionInput(newPrinterUrl, newPrinterSshHost);
      if (validationError) {
        setError(validationError);
        return;
      }
      const payload = {
        name: newPrinterName.trim(),
        moonraker_url: newPrinterUrl.trim(),
        host_audit_mode: newPrinterSshHost && newPrinterSshUser ? "ssh" : "local",
        ssh_host: newPrinterSshHost.trim() || null,
        ssh_port: newPrinterSshPort,
        ssh_username: newPrinterSshUser.trim() || null,
        ssh_credential: newPrinterSshCredential || null,
      };
      const response = await printerApi.save(printerModalMode === "edit" ? editingPrinterId : null, payload);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const created = (await response.json()) as PrinterRecord;
      await loadPrinters();
      setSelectedPrinterId(created.id);
      await loadPrinterContext(created.id);
      setPrinterModalOpen(false);
      setNewPrinterSshCredential("");
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function discoverPrinters() {
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.discover();
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setDiscovery((await response.json()) as PrinterDiscoveryResponse);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function testPrinterConnections() {
    setLoading(true);
    setError(null);
    setPrinterConnectionTest(null);
    try {
      const validationError = validatePrinterConnectionInput(newPrinterUrl, newPrinterSshHost);
      if (validationError) {
        setError(validationError);
        return;
      }
      const response = await printerApi.testConnection({
        moonraker_url: newPrinterUrl.trim(),
        ssh_host: newPrinterSshHost.trim() || null,
        ssh_port: newPrinterSshPort,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setPrinterConnectionTest((await response.json()) as PrinterConnectionTestResponse);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function useDiscoveredPrinter(candidate: DiscoveredPrinter) {
    setNewPrinterName(candidate.name);
    setNewPrinterUrl(candidate.moonraker_url);
    setNewPrinterSshHost(extractHost(candidate.moonraker_url));
    setPrinterConnectionTest(null);
  }

  function openCreatePrinterModal() {
    setPrinterModalMode("create");
    setEditingPrinterId(null);
    setNewPrinterName("Voron - Mayder");
    setNewPrinterUrl("http://voron.local:7125");
    setNewPrinterSshHost("");
    setNewPrinterSshPort(22);
    setNewPrinterSshUser("");
    setNewPrinterSshCredential("");
    setDiscovery(null);
    setPrinterConnectionTest(null);
    setPrinterModalOpen(true);
  }

  function openEditPrinterModal(printer: PrinterRecord) {
    setPrinterModalMode("edit");
    setEditingPrinterId(printer.id);
    setNewPrinterName(printer.name);
    setNewPrinterUrl(printer.moonraker_url);
    setNewPrinterSshHost(printer.ssh_host ?? extractHost(printer.moonraker_url));
    setNewPrinterSshPort(printer.ssh_port ?? 22);
    setNewPrinterSshUser(printer.ssh_username ?? "");
    setNewPrinterSshCredential("");
    setDiscovery(null);
    setPrinterConnectionTest(null);
    setPrinterModalOpen(true);
  }

  async function loadSelectedPrinterStatus() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.moonrakerStatus(selectedPrinterId);
      const payload = (await response.json()) as MoonrakerStatus;
      setStatus(payload);
      await loadOperationStatus(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
      await loadUpdateStatus(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return {
    createPrinter,
    discoverPrinters,
    discovery,
    editingPrinterId,
    loadPrinters,
    loadSelectedPrinterStatus,
    newPrinterName,
    newPrinterSshCredential,
    newPrinterSshHost,
    newPrinterSshPort,
    newPrinterSshUser,
    newPrinterUrl,
    openCreatePrinterModal,
    openEditPrinterModal,
    printerConnectionTest,
    printerModalMode,
    printerModalOpen,
    printers,
    selectPrinter,
    selectedPrinter,
    selectedPrinterId,
    setDiscovery,
    setEditingPrinterId,
    setNewPrinterName,
    setNewPrinterSshCredential,
    setNewPrinterSshHost,
    setNewPrinterSshPort,
    setNewPrinterSshUser,
    setNewPrinterUrl,
    setPrinterConnectionTest,
    setPrinterModalMode,
    setPrinterModalOpen,
    setPrinters,
    setSelectedPrinterId,
    testPrinterConnections,
    useDiscoveredPrinter,
  };
}
