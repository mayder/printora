import React from "react";
import { setupApi } from "../../services/setupApi";
import type { SetupAuthMethod, SetupSshPlanResponse, SetupSshPreflightResponse, SetupSshRunRecord, SetupSshTarget } from "../../types";
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
      const response = await setupApi.history();
      setSetupHistory(response.runs);
      return response.runs;
    } catch (err) {
      setError(unknownErrorMessage(err));
      return [];
    }
  }

  return {
    loadSetupHistory,
    runSetupPlan,
    runSetupPreflight,
    setSetupAuthMethod,
    setSetupHost,
    setSetupKeyPath,
    setSetupPort,
    setSetupTimeoutSeconds,
    setSetupUsername,
    setupAuthMethod,
    setupBusy,
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
