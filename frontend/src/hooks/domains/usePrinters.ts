import React from "react";
import { useSelectedPrinterPreference } from "../../selectedPrinterPreference";
import { printerApi } from "../../services/printerApi";
import type {
  ConnectionCheckResult,
  DiscoveredPrinter,
  AgentCredentialExchangeResponse,
  AgentInstallPlanResponse,
  AgentInstallStatusResponse,
  AgentJobRecord,
  AgentPairingOverview,
  AgentSupportBundle,
  AgentSupportOverview,
  MoonrakerStatus,
  PairingTokenResponse,
  PrinterConnectionTestResponse,
  PrinterDiscoveryResponse,
  PrinterRecord,
  RemoteOperationOverview,
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
  const [pairingOverview, setPairingOverview] = React.useState<AgentPairingOverview | null>(null);
  const [createdPairingToken, setCreatedPairingToken] = React.useState<PairingTokenResponse | null>(null);
  const [rotatedAgentCredential, setRotatedAgentCredential] = React.useState<AgentCredentialExchangeResponse | null>(null);
  const [agentInstallPlan, setAgentInstallPlan] = React.useState<AgentInstallPlanResponse | null>(null);
  const [agentInstallStatus, setAgentInstallStatus] = React.useState<AgentInstallStatusResponse | null>(null);
  const [remoteOperations, setRemoteOperations] = React.useState<RemoteOperationOverview | null>(null);
  const [remoteOperationPreflight, setRemoteOperationPreflight] = React.useState<AgentJobRecord | null>(null);
  const [remoteOperationExecution, setRemoteOperationExecution] = React.useState<AgentJobRecord | null>(null);
  const [remoteOperationConfirmation, setRemoteOperationConfirmation] = React.useState("");
  const [agentSupport, setAgentSupport] = React.useState<AgentSupportOverview | null>(null);
  const [agentSupportBundle, setAgentSupportBundle] = React.useState<AgentSupportBundle | null>(null);

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
    void loadPrinterPairing(printerId);
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
      await loadPrinterPairing(created.id);
      await loadRemoteOperations(created.id);
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

  async function loadPrinterPairing(printerId = selectedPrinterId) {
    if (!printerId) {
      setPairingOverview(null);
      setAgentInstallStatus(null);
      return;
    }
    const response = await printerApi.pairing(printerId);
    if (!response.ok) {
      return;
    }
    setPairingOverview((await response.json()) as AgentPairingOverview);
    await loadAgentInstallStatus(printerId);
    await loadRemoteOperations(printerId);
    await loadAgentSupport(printerId);
  }

  async function loadAgentInstallStatus(printerId = selectedPrinterId) {
    if (!printerId) {
      setAgentInstallStatus(null);
      return;
    }
    const response = await printerApi.agentInstallStatus(printerId);
    if (!response.ok) {
      return;
    }
    setAgentInstallStatus((await response.json()) as AgentInstallStatusResponse);
  }

  async function loadAgentSupport(printerId = selectedPrinterId) {
    if (!printerId) {
      setAgentSupport(null);
      return;
    }
    const response = await printerApi.agentSupport(printerId);
    if (!response.ok) {
      return;
    }
    setAgentSupport((await response.json()) as AgentSupportOverview);
  }

  async function createAgentDoctorJob() {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.createAgentDoctorJob(selectedPrinterId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadAgentSupport(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadAgentSupportBundle() {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.agentSupportBundle(selectedPrinterId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setAgentSupportBundle((await response.json()) as AgentSupportBundle);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function createAgentInstallPlan() {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.agentInstallPlan(selectedPrinterId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setAgentInstallPlan((await response.json()) as AgentInstallPlanResponse);
      await loadPrinterPairing(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadRemoteOperations(printerId = selectedPrinterId) {
    if (!printerId) {
      setRemoteOperations(null);
      return;
    }
    const response = await printerApi.remoteOperations(printerId);
    if (!response.ok) {
      return;
    }
    setRemoteOperations((await response.json()) as RemoteOperationOverview);
  }

  async function createRemoteOperationPreflight(actionId: string) {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.remoteOperationPreflight(selectedPrinterId, { action_id: actionId, parameters: {} });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setRemoteOperationPreflight((await response.json()) as AgentJobRecord);
      setRemoteOperationExecution(null);
      setRemoteOperationConfirmation("");
      await loadRemoteOperations(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function executeRemoteOperation() {
    if (!selectedPrinterId || !remoteOperationPreflight) {
      setError("Gere o preflight remoto antes de executar.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.remoteOperationExecute(selectedPrinterId, {
        preflight_job_id: remoteOperationPreflight.id,
        confirmation_phrase: remoteOperationConfirmation,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setRemoteOperationExecution((await response.json()) as AgentJobRecord);
      await loadRemoteOperations(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function cancelRemoteOperationJob(jobId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.cancelRemoteOperationJob(selectedPrinterId, jobId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadRemoteOperations(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function createPairingToken() {
    if (!selectedPrinterId) {
      setError("Selecione uma impressora");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.createPairingToken(selectedPrinterId, 15);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCreatedPairingToken((await response.json()) as PairingTokenResponse);
      await loadPrinterPairing(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function revokePairingToken(tokenId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.revokePairingToken(selectedPrinterId, tokenId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadPrinterPairing(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function revokePrinterAgent(agentId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.revokeAgent(selectedPrinterId, agentId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadPrinterPairing(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function rotatePrinterAgent(agentId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.rotateAgentCredential(selectedPrinterId, agentId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setRotatedAgentCredential((await response.json()) as AgentCredentialExchangeResponse);
      await loadPrinterPairing(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return {
    agentInstallPlan,
    agentInstallStatus,
    agentSupport,
    agentSupportBundle,
    cancelRemoteOperationJob,
    createPrinter,
    createAgentInstallPlan,
    createPairingToken,
    createAgentDoctorJob,
    createRemoteOperationPreflight,
    createdPairingToken,
    discoverPrinters,
    discovery,
    editingPrinterId,
    executeRemoteOperation,
    loadPrinters,
    loadPrinterPairing,
    loadAgentInstallStatus,
    loadAgentSupport,
    loadAgentSupportBundle,
    loadRemoteOperations,
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
    pairingOverview,
    printers,
    revokePairingToken,
    revokePrinterAgent,
    rotatePrinterAgent,
    rotatedAgentCredential,
    remoteOperationConfirmation,
    remoteOperationExecution,
    remoteOperationPreflight,
    remoteOperations,
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
    setCreatedPairingToken,
    setAgentInstallPlan,
    setAgentSupportBundle,
    setRotatedAgentCredential,
    setRemoteOperationConfirmation,
    setRemoteOperationExecution,
    setRemoteOperationPreflight,
    setPrinters,
    setSelectedPrinterId,
    testPrinterConnections,
    useDiscoveredPrinter,
  };
}
