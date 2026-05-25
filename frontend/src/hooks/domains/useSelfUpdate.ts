import React from "react";
import { systemApi } from "../../services/systemApi";
import { readApiError } from "../../services/http";
import type { ReleaseRecord, SystemReleasesResponse } from "../../types";
import {
  isSelfUpdateEnvironmentSupported,
  type SelfUpdateApplyResponse,
  type SelfUpdateHistoryResponse,
  type SelfUpdatePlanResponse,
  type SelfUpdateReconcileResponse,
  type SelfUpdateRollbackResponse,
  type SelfUpdateRunRecord,
} from "../../selfUpdate";

export function useSelfUpdate() {
  const [systemReleases, setSystemReleases] = React.useState<SystemReleasesResponse | null>(null);
  const [releaseLoading, setReleaseLoading] = React.useState(false);
  const [releaseError, setReleaseError] = React.useState<string | null>(null);
  const [selfUpdatePlan, setSelfUpdatePlan] = React.useState<SelfUpdatePlanResponse | null>(null);
  const [selfUpdateHistory, setSelfUpdateHistory] = React.useState<SelfUpdateRunRecord[]>([]);
  const [selfUpdateModalOpen, setSelfUpdateModalOpen] = React.useState(false);
  const [selfUpdateApplying, setSelfUpdateApplying] = React.useState(false);
  const [selfUpdateReconciling, setSelfUpdateReconciling] = React.useState(false);
  const [selfUpdateRollingBack, setSelfUpdateRollingBack] = React.useState(false);
  const [selfUpdateConfirmation, setSelfUpdateConfirmation] = React.useState("");
  const [selfUpdateRollbackConfirmation, setSelfUpdateRollbackConfirmation] = React.useState("");
  const [selfUpdateMessage, setSelfUpdateMessage] = React.useState<string | null>(null);
  const [selfUpdateConnectionLost, setSelfUpdateConnectionLost] = React.useState(false);

  const displayedReleaseRows = React.useMemo<ReleaseRecord[]>(() => {
    if (!systemReleases) {
      return [];
    }
    return systemReleases.releases.filter((release) => release.tag !== systemReleases.latest_release?.tag);
  }, [systemReleases]);

  async function loadSystemReleases() {
    setReleaseLoading(true);
    setReleaseError(null);
    try {
      const response = await systemApi.releases();
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      setSystemReleases((await response.json()) as SystemReleasesResponse);
    } catch (err) {
      setReleaseError(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setReleaseLoading(false);
    }
  }

  async function loadSelfUpdateHistory() {
    try {
      const response = await systemApi.updateHistory();
      if (!response.ok) {
        return;
      }
      const payload = (await response.json()) as SelfUpdateHistoryResponse;
      setSelfUpdateHistory(payload.runs);
    } catch {
      // Histórico não deve bloquear o restante da tela.
    }
  }

  async function reconcileSelfUpdateHistory() {
    setSelfUpdateReconciling(true);
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    try {
      const response = await systemApi.reconcileUpdate();
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdateReconcileResponse;
      setSelfUpdateHistory(payload.runs);
      setSelfUpdateMessage(payload.message);
      await loadSystemReleases();
    } catch (err) {
      setSelfUpdateMessage(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setSelfUpdateReconciling(false);
    }
  }

  async function planSelfUpdate() {
    const targetTag = systemReleases?.latest_release?.tag;
    if (!targetTag) {
      return;
    }
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    setReleaseLoading(true);
    try {
      const response = await systemApi.planUpdate({
        target_tag: targetTag,
        source_url: systemReleases.latest_release?.url ?? null,
      });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdatePlanResponse;
      setSelfUpdatePlan(payload);
      setSelfUpdateConfirmation("");
      setSelfUpdateRollbackConfirmation("");
      setSelfUpdateModalOpen(true);
      await loadSelfUpdateHistory();
    } catch (err) {
      setSelfUpdateMessage(err instanceof Error ? err.message : "Erro desconhecido");
    } finally {
      setReleaseLoading(false);
    }
  }

  async function startSelfUpdateFlow() {
    const plannedRun = selfUpdatePlan?.run;
    if (plannedRun && plannedRun.target_tag === systemReleases?.latest_release?.tag && plannedRun.status === "planned") return void setSelfUpdateModalOpen(true);
    await planSelfUpdate();
  }

  async function applySelfUpdate() {
    const targetTag = selfUpdatePlan?.run.target_tag ?? systemReleases?.latest_release?.tag;
    if (!targetTag) {
      return;
    }
    setSelfUpdateApplying(true);
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    try {
      const response = await systemApi.applyUpdate({
        target_tag: targetTag,
        source_url: systemReleases?.latest_release?.url ?? selfUpdatePlan?.run.source_url ?? null,
        confirmation_phrase: selfUpdateConfirmation,
      });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdateApplyResponse;
      setSelfUpdatePlan({
        safe_mode: "apply",
        update_supported: isSelfUpdateEnvironmentSupported(payload.run.environment),
        can_apply: false,
        message: payload.message,
        run: payload.run,
      });
      setSelfUpdateMessage(payload.message);
      const finalRun = await pollSelfUpdateRun(payload.run.id);
      await loadSelfUpdateHistory();
      if (finalRun?.status === "succeeded" || finalRun?.status === "rolled_back") {
        await loadSystemReleases();
      }
    } catch (err) {
      setSelfUpdateConnectionLost(true);
      setSelfUpdateMessage(err instanceof Error ? err.message : "O Printora pode estar reiniciando. Aguarde e recarregue.");
    } finally {
      setSelfUpdateApplying(false);
    }
  }

  async function pollSelfUpdateRun(runId: number): Promise<SelfUpdateRunRecord | null> {
    for (let attempt = 0; attempt < 20; attempt += 1) {
      try {
        const response = await systemApi.updateRun(runId);
        if (!response.ok) {
          throw new Error(await readApiError(response));
        }
        const run = (await response.json()) as SelfUpdateRunRecord;
        setSelfUpdatePlan((current) =>
          current ? { ...current, run, message: current.message } : { safe_mode: "poll", update_supported: isSelfUpdateEnvironmentSupported(run.environment), can_apply: false, message: "Status atualizado.", run },
        );
        if (run.status !== "running") {
          return run;
        }
      } catch {
        setSelfUpdateConnectionLost(true);
        setSelfUpdateMessage("O Printora pode estar reiniciando. Aguarde e recarregue.");
        window.setTimeout(() => {
          void loadSystemReleases();
          void loadSelfUpdateHistory();
        }, 8000);
        return null;
      }
      await new Promise((resolve) => window.setTimeout(resolve, 2000));
    }
    return null;
  }

  async function rollbackSelfUpdate(runId: number) {
    setSelfUpdateRollingBack(true);
    setSelfUpdateMessage(null);
    setSelfUpdateConnectionLost(false);
    try {
      const response = await systemApi.rollbackUpdate({
        run_id: runId,
        confirmation_phrase: selfUpdateRollbackConfirmation,
      });
      if (!response.ok) {
        throw new Error(await readApiError(response));
      }
      const payload = (await response.json()) as SelfUpdateRollbackResponse;
      setSelfUpdatePlan({
        safe_mode: "rollback",
        update_supported: isSelfUpdateEnvironmentSupported(payload.rollback_run.environment),
        can_apply: false,
        message: payload.message,
        run: payload.rollback_run,
      });
      setSelfUpdateMessage(payload.message);
      const finalRun = await pollSelfUpdateRun(payload.rollback_run.id);
      await loadSelfUpdateHistory();
      if (finalRun?.status === "succeeded" || finalRun?.status === "rolled_back") {
        await loadSystemReleases();
      }
    } catch (err) {
      setSelfUpdateConnectionLost(true);
      setSelfUpdateMessage(err instanceof Error ? err.message : "O Printora pode estar reiniciando. Aguarde e recarregue.");
    } finally {
      setSelfUpdateRollingBack(false);
    }
  }

  return {
    applySelfUpdate,
    displayedReleaseRows,
    loadSelfUpdateHistory,
    loadSystemReleases,
    planSelfUpdate,
    pollSelfUpdateRun,
    releaseError,
    releaseLoading,
    reconcileSelfUpdateHistory,
    rollbackSelfUpdate,
    selfUpdateApplying,
    selfUpdateConfirmation,
    selfUpdateConnectionLost,
    selfUpdateHistory,
    selfUpdateMessage,
    selfUpdateModalOpen,
    selfUpdatePlan,
    selfUpdateReconciling,
    selfUpdateRollbackConfirmation,
    selfUpdateRollingBack,
    setReleaseError,
    setReleaseLoading,
    setSelfUpdateApplying,
    setSelfUpdateConfirmation,
    setSelfUpdateConnectionLost,
    setSelfUpdateHistory,
    setSelfUpdateMessage,
    setSelfUpdateModalOpen,
    setSelfUpdatePlan,
    setSelfUpdateReconciling,
    setSelfUpdateRollbackConfirmation,
    setSelfUpdateRollingBack,
    setSystemReleases,
    startSelfUpdateFlow,
    systemReleases,
  };
}
