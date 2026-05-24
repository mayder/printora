import React from "react";
import { backupApi } from "../../services/backupApi";
import { printerApi } from "../../services/printerApi";
import { reportsApi } from "../../services/reportsApi";
import type {
  BackupArchiveCompareResponse,
  BackupPolicyRecord,
  BackupRestoreGateResponse,
  BackupRestorePlanResponse,
  BackupRunRecord,
  SanitizedReport,
  SnapshotDiff,
  SnapshotRecord,
} from "../../types";
import type { SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseReportsOptions = {
  selectedPrinterId: number | null;
  loadPrinterHealth: (printerId: number) => Promise<void>;
  setError: SetError;
  setLoading: SetLoading;
};

export function useReports({ selectedPrinterId, loadPrinterHealth, setError, setLoading }: UseReportsOptions) {
  const [snapshots, setSnapshots] = React.useState<SnapshotRecord[]>([]);
  const [fromSnapshotId, setFromSnapshotId] = React.useState<number | null>(null);
  const [toSnapshotId, setToSnapshotId] = React.useState<number | null>(null);
  const [snapshotDiff, setSnapshotDiff] = React.useState<SnapshotDiff | null>(null);
  const [backupPolicies, setBackupPolicies] = React.useState<BackupPolicyRecord[]>([]);
  const [backupRuns, setBackupRuns] = React.useState<BackupRunRecord[]>([]);
  const [backupCompareResult, setBackupCompareResult] = React.useState<BackupArchiveCompareResponse | null>(null);
  const [backupRestorePlan, setBackupRestorePlan] = React.useState<BackupRestorePlanResponse | null>(null);
  const [backupRestoreGate, setBackupRestoreGate] = React.useState<BackupRestoreGateResponse | null>(null);
  const [sanitizedReport, setSanitizedReport] = React.useState<SanitizedReport | null>(null);
  const [backupName, setBackupName] = React.useState("Config backup");
  const [backupSourcePath, setBackupSourcePath] = React.useState("/home/pi/printer_data/config");
  const [backupDestinationPath, setBackupDestinationPath] = React.useState("/home/pi/printer_data/backups/printora");
  const [backupDryRunOnly, setBackupDryRunOnly] = React.useState(true);
  const [backupCompareBasePath, setBackupCompareBasePath] = React.useState("");
  const [backupCompareTargetPath, setBackupCompareTargetPath] = React.useState("");
  const [backupRestoreArchivePath, setBackupRestoreArchivePath] = React.useState("");
  const [backupRestoreRoot, setBackupRestoreRoot] = React.useState("/home/pi/printer_data/config");
  const [backupRestoreFiles, setBackupRestoreFiles] = React.useState("printer.cfg");
  const [backupRestoreConfirmation, setBackupRestoreConfirmation] = React.useState("");

  async function captureSnapshot() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.captureSnapshot(selectedPrinterId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadSnapshots(selectedPrinterId);
      await loadPrinterHealth(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadSnapshots(printerId: number) {
    const response = await printerApi.snapshots(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { snapshots: SnapshotRecord[] };
    setSnapshots(payload.snapshots);
    setSnapshotDiff(null);
    if (payload.snapshots.length >= 2) {
      setFromSnapshotId(payload.snapshots[1].id);
      setToSnapshotId(payload.snapshots[0].id);
    } else {
      setFromSnapshotId(payload.snapshots[0]?.id ?? null);
      setToSnapshotId(payload.snapshots[0]?.id ?? null);
    }
  }

  async function loadBackups(printerId: number) {
    const [policiesResponse, runsResponse] = await Promise.all([
      backupApi.policies(printerId),
      backupApi.runs(printerId),
    ]);
    if (policiesResponse.ok) {
      const payload = (await policiesResponse.json()) as { policies: BackupPolicyRecord[] };
      setBackupPolicies(payload.policies);
    }
    if (runsResponse.ok) {
      const payload = (await runsResponse.json()) as { runs: BackupRunRecord[] };
      setBackupRuns(payload.runs);
    }
  }

  async function loadSanitizedReport() {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await reportsApi.sanitized(selectedPrinterId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setSanitizedReport((await response.json()) as SanitizedReport);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function createBackupPolicy(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.createPolicy(selectedPrinterId, {
        name: backupName,
        source_path: backupSourcePath,
        destination_path: backupDestinationPath,
        dry_run_only: backupDryRunOnly,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function executeLocalBackup(policyId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.executeLocal(policyId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function createBackupDryRun(policyId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.dryRun(policyId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadBackups(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function compareBackupArchives() {
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.compareArchives({
        base_archive_path: backupCompareBasePath,
        target_archive_path: backupCompareTargetPath,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setBackupCompareResult((await response.json()) as BackupArchiveCompareResponse);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function createBackupRestorePlan() {
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.restorePlan({
        archive_path: backupRestoreArchivePath,
        restore_root: backupRestoreRoot,
        files: backupRestoreFiles.split("\n").map((item) => item.trim()).filter(Boolean),
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setBackupRestorePlan((await response.json()) as BackupRestorePlanResponse);
      setBackupRestoreGate(null);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function validateBackupRestoreGate() {
    setLoading(true);
    setError(null);
    try {
      const response = await backupApi.restoreGate({
        archive_path: backupRestoreArchivePath,
        restore_root: backupRestoreRoot,
        files: backupRestoreFiles.split("\n").map((item) => item.trim()).filter(Boolean),
        confirmation: backupRestoreConfirmation,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setBackupRestoreGate((await response.json()) as BackupRestoreGateResponse);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function compareSnapshots() {
    if (!selectedPrinterId || !fromSnapshotId || !toSnapshotId || fromSnapshotId === toSnapshotId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await printerApi.snapshotDiff(selectedPrinterId, fromSnapshotId, toSnapshotId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setSnapshotDiff((await response.json()) as SnapshotDiff);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return {
    backupCompareBasePath,
    backupCompareResult,
    backupCompareTargetPath,
    backupDestinationPath,
    backupDryRunOnly,
    backupName,
    backupPolicies,
    backupRestoreArchivePath,
    backupRestoreConfirmation,
    backupRestoreFiles,
    backupRestoreGate,
    backupRestorePlan,
    backupRestoreRoot,
    backupRuns,
    backupSourcePath,
    captureSnapshot,
    compareBackupArchives,
    compareSnapshots,
    createBackupDryRun,
    createBackupPolicy,
    createBackupRestorePlan,
    executeLocalBackup,
    fromSnapshotId,
    loadBackups,
    loadSanitizedReport,
    loadSnapshots,
    sanitizedReport,
    setBackupCompareBasePath,
    setBackupCompareResult,
    setBackupCompareTargetPath,
    setBackupDestinationPath,
    setBackupDryRunOnly,
    setBackupName,
    setBackupPolicies,
    setBackupRestoreArchivePath,
    setBackupRestoreConfirmation,
    setBackupRestoreFiles,
    setBackupRestoreGate,
    setBackupRestorePlan,
    setBackupRestoreRoot,
    setBackupRuns,
    setBackupSourcePath,
    setFromSnapshotId,
    setSanitizedReport,
    setSnapshotDiff,
    setSnapshots,
    setToSnapshotId,
    snapshotDiff,
    snapshots,
    toSnapshotId,
    validateBackupRestoreGate,
  };
}
