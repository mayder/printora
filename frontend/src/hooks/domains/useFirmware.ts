import React from "react";
import { firmwareApi } from "../../services/firmwareApi";
import { pluginApi } from "../../services/pluginApi";
import type {
  BoardPreset,
  FirmwareBoardRecord,
  FirmwareBuildPreflight,
  FirmwareBuildRunRecord,
  FirmwareFlashPreflight,
  FirmwareFlashRunRecord,
  FirmwareRecoveryPlan,
  PluginAuditResponse,
} from "../../types";
import type { SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseFirmwareOptions = {
  selectedPrinterId: number | null;
  setError: SetError;
  setLoading: SetLoading;
};

export function useFirmware({ selectedPrinterId, setError, setLoading }: UseFirmwareOptions) {
  const [pluginAudit, setPluginAudit] = React.useState<PluginAuditResponse | null>(null);
  const [boardPresets, setBoardPresets] = React.useState<BoardPreset[]>([]);
  const [firmwareBoards, setFirmwareBoards] = React.useState<FirmwareBoardRecord[]>([]);
  const [firmwareBuildRuns, setFirmwareBuildRuns] = React.useState<FirmwareBuildRunRecord[]>([]);
  const [firmwareFlashRuns, setFirmwareFlashRuns] = React.useState<FirmwareFlashRunRecord[]>([]);
  const [firmwareRecoveryPlan, setFirmwareRecoveryPlan] = React.useState<FirmwareRecoveryPlan | null>(null);
  const [firmwareBuildPreflight, setFirmwareBuildPreflight] = React.useState<FirmwareBuildPreflight | null>(null);
  const [firmwareFlashPreflight, setFirmwareFlashPreflight] = React.useState<FirmwareFlashPreflight | null>(null);
  const [firmwareFilter, setFirmwareFilter] = React.useState<"all" | "can" | "usb">("all");
  const [firmwareBoardName, setFirmwareBoardName] = React.useState("EBB T0");
  const [firmwareBoardPresetId, setFirmwareBoardPresetId] = React.useState("btt_ebb36_g0b1_can");
  const [firmwareBoardCanUuid, setFirmwareBoardCanUuid] = React.useState("");
  const [firmwareBoardCanInterface, setFirmwareBoardCanInterface] = React.useState("can0");
  const [firmwareBoardConfigFile, setFirmwareBoardConfigFile] = React.useState("firmware/ebb_t0.config");
  const [firmwareBoardNotes, setFirmwareBoardNotes] = React.useState("");
  const [firmwareKlipperPath, setFirmwareKlipperPath] = React.useState("~/klipper");
  const [firmwareOutputRoot, setFirmwareOutputRoot] = React.useState("~/printer_data/firmware_builds");
  const [firmwareBuildConfirmation, setFirmwareBuildConfirmation] = React.useState("");
  const [firmwareFlashBinaryPath, setFirmwareFlashBinaryPath] = React.useState("");
  const [firmwareFlashConfirmation, setFirmwareFlashConfirmation] = React.useState("");

  async function loadPluginAudit(printerId: number) {
    const response = await pluginApi.audit(printerId);
    if (!response.ok) {
      return;
    }
    setPluginAudit((await response.json()) as PluginAuditResponse);
  }

  async function loadBoardPresets() {
    const response = await firmwareApi.boardPresets();
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { presets: BoardPreset[] };
    setBoardPresets(payload.presets);
  }

  async function loadFirmwareBoards(printerId: number) {
    const response = await firmwareApi.boards(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { boards: FirmwareBoardRecord[] };
    setFirmwareBoards(payload.boards);
  }

  async function loadFirmwareBuildRuns(printerId: number) {
    const response = await firmwareApi.buildRuns(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { runs: FirmwareBuildRunRecord[] };
    setFirmwareBuildRuns(payload.runs);
  }

  async function loadFirmwareFlashRuns(printerId: number) {
    const response = await firmwareApi.flashRuns(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { runs: FirmwareFlashRunRecord[] };
    setFirmwareFlashRuns(payload.runs);
  }

  async function createFirmwareBoard(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.createBoard(selectedPrinterId, {
        name: firmwareBoardName,
        preset_id: firmwareBoardPresetId,
        can_uuid: firmwareBoardCanUuid || null,
        can_interface: firmwareBoardCanInterface,
        config_file: firmwareBoardConfigFile || null,
        notes: firmwareBoardNotes,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareBoardNotes("");
      await loadFirmwareBoards(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function createFirmwareBuildDryRun(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.buildDryRun(boardId, {
        klipper_path: firmwareKlipperPath,
        output_root: firmwareOutputRoot,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareBuildRuns(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function validateFirmwareBuildPreflight(boardId: number) {
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.buildPreflight(boardId, {
        klipper_path: firmwareKlipperPath,
        output_root: firmwareOutputRoot,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareBuildPreflight((await response.json()) as FirmwareBuildPreflight);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function executeFirmwareBuildLocal(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.executeBuildLocal(boardId, {
        klipper_path: firmwareKlipperPath,
        output_root: firmwareOutputRoot,
        confirmation: firmwareBuildConfirmation,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareBuildRuns(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function createFirmwareFlashDryRun(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const latestBuildRun = firmwareBuildRuns.find((run) => run.board_id === boardId);
      const response = await firmwareApi.flashDryRun(boardId, {
        build_run_id: latestBuildRun?.id ?? null,
        binary_path: firmwareFlashBinaryPath || null,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareFlashRuns(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function validateFirmwareFlashPreflight(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const latestBuildRun = firmwareBuildRuns.find((run) => run.board_id === boardId);
      const response = await firmwareApi.flashPreflight(boardId, {
        build_run_id: latestBuildRun?.id ?? null,
        binary_path: firmwareFlashBinaryPath || null,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareFlashPreflight((await response.json()) as FirmwareFlashPreflight);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function validateFirmwareFlashGate(boardId: number) {
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const latestBuildRun = firmwareBuildRuns.find((run) => run.board_id === boardId);
      const response = await firmwareApi.executeFlash(boardId, {
        build_run_id: latestBuildRun?.id ?? null,
        binary_path: firmwareFlashBinaryPath || null,
        confirmation: firmwareFlashConfirmation,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadFirmwareFlashRuns(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadFirmwareRecoveryPlan(boardId: number) {
    setLoading(true);
    setError(null);
    try {
      const response = await firmwareApi.recoveryPlan(boardId);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setFirmwareRecoveryPlan((await response.json()) as FirmwareRecoveryPlan);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  const visibleFirmwareBoards = firmwareBoards.filter((board) => {
    if (firmwareFilter === "can") {
      return board.connection_type === "can" || board.connection_type === "usb_can_bridge";
    }
    if (firmwareFilter === "usb") {
      return board.connection_type === "usb";
    }
    return true;
  });

  return {
    boardPresets,
    createFirmwareBoard,
    createFirmwareBuildDryRun,
    createFirmwareFlashDryRun,
    executeFirmwareBuildLocal,
    firmwareBoardCanInterface,
    firmwareBoardCanUuid,
    firmwareBoardConfigFile,
    firmwareBoardName,
    firmwareBoardNotes,
    firmwareBoardPresetId,
    firmwareBoards,
    firmwareBuildConfirmation,
    firmwareBuildPreflight,
    firmwareBuildRuns,
    firmwareFilter,
    firmwareFlashBinaryPath,
    firmwareFlashConfirmation,
    firmwareFlashPreflight,
    firmwareFlashRuns,
    firmwareKlipperPath,
    firmwareOutputRoot,
    firmwareRecoveryPlan,
    loadBoardPresets,
    loadFirmwareBoards,
    loadFirmwareBuildRuns,
    loadFirmwareFlashRuns,
    loadFirmwareRecoveryPlan,
    loadPluginAudit,
    pluginAudit,
    setBoardPresets,
    setFirmwareBoardCanInterface,
    setFirmwareBoardCanUuid,
    setFirmwareBoardConfigFile,
    setFirmwareBoardName,
    setFirmwareBoardNotes,
    setFirmwareBoardPresetId,
    setFirmwareBoards,
    setFirmwareBuildConfirmation,
    setFirmwareBuildPreflight,
    setFirmwareBuildRuns,
    setFirmwareFilter,
    setFirmwareFlashBinaryPath,
    setFirmwareFlashConfirmation,
    setFirmwareFlashPreflight,
    setFirmwareFlashRuns,
    setFirmwareKlipperPath,
    setFirmwareOutputRoot,
    setFirmwareRecoveryPlan,
    setPluginAudit,
    validateFirmwareBuildPreflight,
    validateFirmwareFlashGate,
    validateFirmwareFlashPreflight,
    visibleFirmwareBoards,
  };
}
