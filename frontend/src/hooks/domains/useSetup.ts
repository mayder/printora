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
      const [sshResponse, canResponse] = await Promise.allSettled([
        setupApi.history(),
        setupApi.canHistory(),
      ]);
      const firmwareResponse = await setupApi.firmwareHistory().catch(() => null);
      if (sshResponse.status === "fulfilled") {
        setSetupHistory(sshResponse.value.runs);
      }
      if (canResponse.status === "fulfilled") {
        setSetupCanHistory(canResponse.value.runs);
      }
      if (firmwareResponse) {
        setSetupFirmwareHistory(firmwareResponse.runs);
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

  return {
    loadSetupHistory,
    runSetupPlan,
    runSetupCanApply,
    runSetupCanPlan,
    runSetupCanPreflight,
    runSetupFirmwareBuild,
    runSetupFirmwarePlan,
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
