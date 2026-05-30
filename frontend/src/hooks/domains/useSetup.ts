import React from "react";
import { setupApi } from "../../services/setupApi";
import type {
  SetupAuthMethod,
  SetupCanApplyResponse,
  SetupCanPlanResponse,
  SetupCanPreflightResponse,
  SetupCanRunRecord,
  SetupFirmwareBuildResponse,
  SetupFirmwarePlanResponse,
  SetupFirmwareRole,
  SetupFirmwareRunRecord,
  SetupFlashExecuteResponse,
  SetupFlashMethod,
  SetupFlashPlanResponse,
  SetupFlashPreflightResponse,
  SetupFlashRunRecord,
  SetupFinalValidationResponse,
  SetupFinalValidationRunRecord,
  SetupSshPlanResponse,
  SetupSshPreflightResponse,
  SetupSshRunRecord,
  SetupSshTarget,
} from "../../types";
import type { SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseSetupOptions = {
  setError: SetError;
  setLoading: SetLoading;
};

export function useSetup({ setError, setLoading }: UseSetupOptions) {
  const [setupHost, setSetupHost] = React.useState("");
  const [setupPort, setSetupPort] = React.useState(22);
  const [setupUsername, setSetupUsername] = React.useState("pi");
  const [setupAuthMethod, setSetupAuthMethod] = React.useState<SetupAuthMethod>("agent");
  const [setupKeyPath, setSetupKeyPath] = React.useState("");
  const [setupTimeoutSeconds, setSetupTimeoutSeconds] = React.useState(12);
  const [setupPreflight, setSetupPreflight] = React.useState<SetupSshPreflightResponse | null>(null);
  const [setupPlan, setSetupPlan] = React.useState<SetupSshPlanResponse | null>(null);
  const [setupHistory, setSetupHistory] = React.useState<SetupSshRunRecord[]>([]);
  const [setupCanInterfaceName, setSetupCanInterfaceName] = React.useState("can0");
  const [setupCanBitrate, setSetupCanBitrate] = React.useState(1000000);
  const [setupCanConfirmation, setSetupCanConfirmation] = React.useState("");
  const [setupCanPreflight, setSetupCanPreflight] = React.useState<SetupCanPreflightResponse | null>(null);
  const [setupCanPlan, setSetupCanPlan] = React.useState<SetupCanPlanResponse | null>(null);
  const [setupCanApplyResult, setSetupCanApplyResult] = React.useState<SetupCanApplyResponse | null>(null);
  const [setupCanHistory, setSetupCanHistory] = React.useState<SetupCanRunRecord[]>([]);
  const [setupFirmwarePresetId, setSetupFirmwarePresetId] = React.useState("btt_octopus_pro_h723_usb_can");
  const [setupFirmwareBoardName, setSetupFirmwareBoardName] = React.useState("Octopus Pro H723");
  const [setupFirmwareBoardRole, setSetupFirmwareBoardRole] = React.useState<SetupFirmwareRole>("mainboard");
  const [setupFirmwareKlipperPath, setSetupFirmwareKlipperPath] = React.useState("~/klipper");
  const [setupFirmwareOutputRoot, setSetupFirmwareOutputRoot] = React.useState("~/.local/share/printora/firmware-setup");
  const [setupFirmwareVariantConfirmed, setSetupFirmwareVariantConfirmed] = React.useState(false);
  const [setupFirmwareConfirmation, setSetupFirmwareConfirmation] = React.useState("");
  const [setupFirmwarePlan, setSetupFirmwarePlan] = React.useState<SetupFirmwarePlanResponse | null>(null);
  const [setupFirmwareBuildResult, setSetupFirmwareBuildResult] = React.useState<SetupFirmwareBuildResponse | null>(null);
  const [setupFirmwareHistory, setSetupFirmwareHistory] = React.useState<SetupFirmwareRunRecord[]>([]);
  const [setupFlashMethod, setSetupFlashMethod] = React.useState<SetupFlashMethod>("can_katapult");
  const [setupFlashArtifactPath, setSetupFlashArtifactPath] = React.useState("");
  const [setupFlashExpectedUuid, setSetupFlashExpectedUuid] = React.useState("");
  const [setupFlashPreviousBinaryPath, setSetupFlashPreviousBinaryPath] = React.useState("");
  const [setupFlashChecklistConfirmed, setSetupFlashChecklistConfirmed] = React.useState(false);
  const [setupFlashConfirmation, setSetupFlashConfirmation] = React.useState("");
  const [setupFlashPreflight, setSetupFlashPreflight] = React.useState<SetupFlashPreflightResponse | null>(null);
  const [setupFlashPlan, setSetupFlashPlan] = React.useState<SetupFlashPlanResponse | null>(null);
  const [setupFlashExecuteResult, setSetupFlashExecuteResult] = React.useState<SetupFlashExecuteResponse | null>(null);
  const [setupFlashHistory, setSetupFlashHistory] = React.useState<SetupFlashRunRecord[]>([]);
  const [setupFinalExpectedUuids, setSetupFinalExpectedUuids] = React.useState("");
  const [setupFinalConfigRoot, setSetupFinalConfigRoot] = React.useState("~/printer_data/config");
  const [setupFinalLogRoot, setSetupFinalLogRoot] = React.useState("~/printer_data/logs");
  const [setupFinalValidation, setSetupFinalValidation] = React.useState<SetupFinalValidationResponse | null>(null);
  const [setupFinalHistory, setSetupFinalHistory] = React.useState<SetupFinalValidationRunRecord[]>([]);
  const [setupBusy, setSetupBusy] = React.useState(false);

  function setupTarget(): SetupSshTarget {
    return {
      host: setupHost.trim(),
      port: setupPort,
      username: setupUsername.trim(),
      auth_method: setupAuthMethod,
      key_path: setupAuthMethod === "key_path" && setupKeyPath.trim() ? setupKeyPath.trim() : null,
      timeout_seconds: setupTimeoutSeconds,
    };
  }

  async function runSetupPreflight() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.preflight(setupTarget());
      setSetupPreflight(response);
      setSetupPlan(null);
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  async function runSetupPlan() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.plan(setupTarget());
      setSetupPreflight(response.preflight);
      setSetupPlan(response);
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  async function loadSetupHistory() {
    try {
      const [sshResponse, canResponse, firmwareResponse, flashResponse, finalResponse] = await Promise.allSettled([
        setupApi.history(),
        setupApi.canHistory(),
        setupApi.firmwareHistory(),
        setupApi.flashHistory(),
        setupApi.finalValidationHistory(),
      ]);
      if (sshResponse.status === "fulfilled") {
        setSetupHistory(sshResponse.value.runs);
      }
      if (canResponse.status === "fulfilled") {
        setSetupCanHistory(canResponse.value.runs);
      }
      if (firmwareResponse.status === "fulfilled") {
        setSetupFirmwareHistory(firmwareResponse.value.runs);
      }
      if (flashResponse.status === "fulfilled") {
        setSetupFlashHistory(flashResponse.value.runs);
      }
      if (finalResponse.status === "fulfilled") {
        setSetupFinalHistory(finalResponse.value.runs);
      }
      return sshResponse.status === "fulfilled" ? sshResponse.value.runs : [];
    } catch (err) {
      setError(unknownErrorMessage(err));
      return [];
    }
  }

  function setupCanPayload() {
    return {
      target: setupTarget(),
      interface_name: setupCanInterfaceName.trim() || "can0",
      bitrate: setupCanBitrate,
    };
  }

  async function runSetupCanPreflight() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.canPreflight(setupCanPayload());
      setSetupCanPreflight(response);
      setSetupCanPlan(null);
      setSetupCanApplyResult(null);
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  async function runSetupCanPlan() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.canPlan(setupCanPayload());
      setSetupCanPreflight(response.preflight);
      setSetupCanPlan(response);
      setSetupCanApplyResult(null);
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  async function runSetupCanApply() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.canApply({
        ...setupCanPayload(),
        confirmation: setupCanConfirmation,
      });
      setSetupCanApplyResult(response);
      if (response.validation) {
        setSetupCanPreflight(response.validation);
      }
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  function setupFirmwarePayload() {
    return {
      target: setupTarget(),
      preset_id: setupFirmwarePresetId.trim(),
      board_name: setupFirmwareBoardName.trim(),
      board_role: setupFirmwareBoardRole,
      can_interface: setupCanInterfaceName.trim() || "can0",
      klipper_path: setupFirmwareKlipperPath.trim() || "~/klipper",
      output_root: setupFirmwareOutputRoot.trim() || "~/.local/share/printora/firmware-setup",
      variant_confirmed: setupFirmwareVariantConfirmed,
    };
  }

  async function runSetupFirmwarePlan() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.firmwarePlan(setupFirmwarePayload());
      setSetupFirmwarePlan(response);
      setSetupFirmwareBuildResult(null);
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  async function runSetupFirmwareBuild() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.firmwareBuild({
        ...setupFirmwarePayload(),
        confirmation: setupFirmwareConfirmation,
      });
      setSetupFirmwareBuildResult(response);
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  function setupFlashPayload() {
    return {
      target: setupTarget(),
      board_name: setupFirmwareBoardName.trim() || "Placa sem nome",
      board_role: setupFirmwareBoardRole,
      flash_method: setupFlashMethod,
      artifact_path: setupFlashArtifactPath.trim() || setupFirmwareBuildResult?.binary_path || setupFirmwarePlan?.expected_binary_path || "",
      can_interface: setupCanInterfaceName.trim() || "can0",
      expected_uuid: setupFlashExpectedUuid.trim() || null,
      klipper_path: setupFirmwareKlipperPath.trim() || "~/klipper",
      previous_binary_path: setupFlashPreviousBinaryPath.trim() || null,
      checklist_confirmed: setupFlashChecklistConfirmed,
    };
  }

  async function runSetupFlashPreflight() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.flashPreflight(setupFlashPayload());
      setSetupFlashPreflight(response);
      setSetupFlashPlan(null);
      setSetupFlashExecuteResult(null);
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  async function runSetupFlashPlan() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.flashPlan(setupFlashPayload());
      setSetupFlashPreflight(response.preflight);
      setSetupFlashPlan(response);
      setSetupFlashExecuteResult(null);
      setSetupFlashConfirmation("");
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  async function runSetupFlashExecute() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.flashExecute({
        ...setupFlashPayload(),
        confirmation: setupFlashConfirmation,
      });
      setSetupFlashExecuteResult(response);
      if (response.post_validation) {
        setSetupFlashPreflight(response.post_validation);
      }
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  function setupFinalValidationPayload() {
    return {
      target: setupTarget(),
      interface_name: setupCanInterfaceName.trim() || "can0",
      expected_uuids: setupFinalExpectedUuids
        .split(/[\s,;]+/)
        .map((item) => item.trim())
        .filter(Boolean),
      config_root: setupFinalConfigRoot.trim() || "~/printer_data/config",
      log_root: setupFinalLogRoot.trim() || "~/printer_data/logs",
    };
  }

  async function runSetupFinalValidation() {
    setLoading(true);
    setSetupBusy(true);
    setError(null);
    try {
      const response = await setupApi.finalValidationRun(setupFinalValidationPayload());
      setSetupFinalValidation(response);
      await loadSetupHistory();
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setSetupBusy(false);
      setLoading(false);
    }
  }

  return {
    loadSetupHistory,
    runSetupPlan,
    runSetupCanApply,
    runSetupCanPlan,
    runSetupCanPreflight,
    runSetupFirmwareBuild,
    runSetupFirmwarePlan,
    runSetupFlashExecute,
    runSetupFlashPlan,
    runSetupFlashPreflight,
    runSetupFinalValidation,
    runSetupPreflight,
    setSetupAuthMethod,
    setSetupCanBitrate,
    setSetupCanConfirmation,
    setSetupCanInterfaceName,
    setSetupFirmwareBoardName,
    setSetupFirmwareBoardRole,
    setSetupFirmwareConfirmation,
    setSetupFirmwareKlipperPath,
    setSetupFirmwareOutputRoot,
    setSetupFirmwarePresetId,
    setSetupFirmwareVariantConfirmed,
    setSetupFlashArtifactPath,
    setSetupFlashChecklistConfirmed,
    setSetupFlashConfirmation,
    setSetupFlashExpectedUuid,
    setSetupFlashMethod,
    setSetupFlashPreviousBinaryPath,
    setSetupFinalConfigRoot,
    setSetupFinalExpectedUuids,
    setSetupFinalLogRoot,
    setSetupHost,
    setSetupKeyPath,
    setSetupPort,
    setSetupTimeoutSeconds,
    setSetupUsername,
    setupAuthMethod,
    setupBusy,
    setupCanApplyResult,
    setupCanBitrate,
    setupCanConfirmation,
    setupCanHistory,
    setupCanInterfaceName,
    setupCanPlan,
    setupCanPreflight,
    setupFirmwareBoardName,
    setupFirmwareBoardRole,
    setupFirmwareBuildResult,
    setupFirmwareConfirmation,
    setupFirmwareHistory,
    setupFirmwareKlipperPath,
    setupFirmwareOutputRoot,
    setupFirmwarePlan,
    setupFirmwarePresetId,
    setupFirmwareVariantConfirmed,
    setupFlashArtifactPath,
    setupFlashChecklistConfirmed,
    setupFlashConfirmation,
    setupFlashExecuteResult,
    setupFlashExpectedUuid,
    setupFlashHistory,
    setupFlashMethod,
    setupFlashPlan,
    setupFlashPreflight,
    setupFlashPreviousBinaryPath,
    setupFinalConfigRoot,
    setupFinalExpectedUuids,
    setupFinalHistory,
    setupFinalLogRoot,
    setupFinalValidation,
    setupHistory,
    setupHost,
    setupKeyPath,
    setupPlan,
    setupPort,
    setupPreflight,
    setupTimeoutSeconds,
    setupUsername,
  };
}
