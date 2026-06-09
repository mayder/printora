import React from "react";
import * as authApi from "../../services/authApi";
import { calibrationApi } from "../../services/calibrationApi";
import { readApiError } from "../../services/http";
import { operationApi } from "../../services/operationApi";
import { zOffsetApi } from "../../services/zOffsetApi";
import type {
  CalibrationAvailableTestsResponse,
  CalibrationExecutionRecord,
  CalibrationPreflight,
  CalibrationRunRecord,
  CalibrationSequencePlan,
  CalibrationSummary,
  CalibrationTestRecord,
  ConfigRemediationResult,
  OperationActionExecutionAttempt,
  ConfirmActionOptions,
  ZOffsetRecord,
  ZOffsetWizardPlan,
  AuthUser,
} from "../../types";
import { calibrationExecutionPidParameters, formatDateTime, getCalibrationResultFormConfig } from "../../utils/formatters";
import type { SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseCalibrationOptions = {
  authUser: AuthUser | null;
  selectedPrinterId: number | null;
  confirmAction: (options: ConfirmActionOptions) => Promise<boolean>;
  setError: SetError;
  setLoading: SetLoading;
};

export function useCalibration({ authUser, selectedPrinterId, confirmAction, setError, setLoading }: UseCalibrationOptions) {
  const [calibrationTests, setCalibrationTests] = React.useState<CalibrationTestRecord[]>([]);
  const [calibrationHiddenTests, setCalibrationHiddenTests] = React.useState<CalibrationAvailableTestsResponse["hidden_tests"]>([]);
  const [calibrationRuns, setCalibrationRuns] = React.useState<CalibrationRunRecord[]>([]);
  const [calibrationSummary, setCalibrationSummary] = React.useState<CalibrationSummary | null>(null);
  const [calibrationSequence, setCalibrationSequence] = React.useState<CalibrationSequencePlan | null>(null);
  const [calibrationPreflight, setCalibrationPreflight] = React.useState<CalibrationPreflight | null>(null);
  const [calibrationExecutions, setCalibrationExecutions] = React.useState<CalibrationExecutionRecord[]>([]);
  const [calibrationExecutionResult, setCalibrationExecutionResult] = React.useState<CalibrationExecutionRecord | null>(null);
  const [calibrationExecutionBusy, setCalibrationExecutionBusy] = React.useState(false);
  const [calibrationSaveConfigBusy, setCalibrationSaveConfigBusy] = React.useState(false);
  const [calibrationSaveConfigError, setCalibrationSaveConfigError] = React.useState("");
  const [calibrationSaveConfigResult, setCalibrationSaveConfigResult] = React.useState<OperationActionExecutionAttempt | null>(null);
  const [calibrationConfigRemediationBusy, setCalibrationConfigRemediationBusy] = React.useState(false);
  const [calibrationConfigRemediationError, setCalibrationConfigRemediationError] = React.useState("");
  const [calibrationConfigRemediationPreview, setCalibrationConfigRemediationPreview] = React.useState<ConfigRemediationResult | null>(null);
  const [calibrationConfigRemediationApplyResult, setCalibrationConfigRemediationApplyResult] = React.useState<ConfigRemediationResult | null>(null);
  const [calibrationConfigRemediationSelectedIds, setCalibrationConfigRemediationSelectedIds] = React.useState<string[]>([]);
  const [calibrationStepUpOpen, setCalibrationStepUpOpen] = React.useState(false);
  const [calibrationStepUpPassword, setCalibrationStepUpPassword] = React.useState("");
  const [calibrationStepUpCode, setCalibrationStepUpCode] = React.useState("");
  const [calibrationStepUpBusy, setCalibrationStepUpBusy] = React.useState(false);
  const [calibrationStepUpError, setCalibrationStepUpError] = React.useState("");
  const [calibrationStepUpPendingAction, setCalibrationStepUpPendingAction] = React.useState<"save_config" | "config_remediation" | null>(null);
  const [calibrationHelpTestKey, setCalibrationHelpTestKey] = React.useState<string | null>(null);
  const [calibrationExecuteTestKey, setCalibrationExecuteTestKey] = React.useState<string | null>(null);
  const [calibrationResultTestKey, setCalibrationResultTestKey] = React.useState<string | null>(null);
  const [calibrationResultFormOpen, setCalibrationResultFormOpen] = React.useState(false);
  const [calibrationActivityCleared, setCalibrationActivityCleared] = React.useState(false);
  const [testFilter, setTestFilter] = React.useState<"all" | "executable" | "manual" | "blocked">("all");
  const [testSearch, setTestSearch] = React.useState("");
  const [testUsageFilter, setTestUsageFilter] = React.useState<"all" | "print" | "movement" | "manual">("all");
  const [zOffsetRecords, setZOffsetRecords] = React.useState<ZOffsetRecord[]>([]);
  const [zOffsetWizardPlan, setZOffsetWizardPlan] = React.useState<ZOffsetWizardPlan | null>(null);
  const [zOffsetWizardChecks, setZOffsetWizardChecks] = React.useState<Record<string, boolean>>({});
  const [zOffsetFormOpen, setZOffsetFormOpen] = React.useState(false);
  const [zOffsetPlateName, setZOffsetPlateName] = React.useState("");
  const [zOffsetMaterial, setZOffsetMaterial] = React.useState("");
  const [zOffsetNozzle, setZOffsetNozzle] = React.useState("");
  const [zOffsetValue, setZOffsetValue] = React.useState("");
  const [zOffsetNotes, setZOffsetNotes] = React.useState("");
  const [calibrationTestKey, setCalibrationTestKey] = React.useState("probe_accuracy_center");
  const [calibrationResultStatus, setCalibrationResultStatus] =
    React.useState<CalibrationRunRecord["result_status"]>("passed");
  const [calibrationMaterial, setCalibrationMaterial] = React.useState("PLA");
  const [calibrationPlateName, setCalibrationPlateName] = React.useState("Texturizada");
  const [calibrationNozzle, setCalibrationNozzle] = React.useState("T0");
  const [calibrationObservedValue, setCalibrationObservedValue] = React.useState("");
  const [calibrationNotes, setCalibrationNotes] = React.useState("");
  const [calibrationGcodeReviewed, setCalibrationGcodeReviewed] = React.useState(false);
  const [calibrationPhotoReference, setCalibrationPhotoReference] = React.useState("");
  const [calibrationOperatorPresent, setCalibrationOperatorPresent] = React.useState(false);
  const [calibrationExecutionConfirmation, setCalibrationExecutionConfirmation] = React.useState("");
  const calibrationExecutionInFlightRef = React.useRef(false);

  async function loadCalibrationTests(printerId?: number) {
    const response = await calibrationApi.availableTests(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { tests: CalibrationTestRecord[] } | CalibrationAvailableTestsResponse;
    setCalibrationTests(payload.tests);
    setCalibrationHiddenTests("hidden_tests" in payload ? payload.hidden_tests : []);
    setCalibrationTestKey((current) => {
      if (current && payload.tests.some((test) => test.test_key === current)) {
        return current;
      }
      return payload.tests[0]?.test_key || "";
    });
  }

  async function loadCalibrationRuns(printerId: number) {
    const [runsResponse, summaryResponse, sequenceResponse, executionsResponse] = await Promise.all([
      calibrationApi.runs(printerId),
      calibrationApi.summary(printerId),
      calibrationApi.sequence(printerId),
      calibrationApi.executions(printerId),
    ]);
    if (runsResponse.ok) {
      const payload = (await runsResponse.json()) as { runs: CalibrationRunRecord[] };
      setCalibrationRuns(payload.runs);
    }
    if (summaryResponse.ok) {
      setCalibrationSummary((await summaryResponse.json()) as CalibrationSummary);
    }
    if (sequenceResponse.ok) {
      setCalibrationSequence((await sequenceResponse.json()) as CalibrationSequencePlan);
    }
    if (executionsResponse.ok) {
      const payload = (await executionsResponse.json()) as { executions: CalibrationExecutionRecord[] };
      setCalibrationExecutions(payload.executions);
    }
  }

  async function createCalibrationRun(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await calibrationApi.createRun(selectedPrinterId, {
        test_key: calibrationTestKey,
        result_status: calibrationResultStatus,
        material: calibrationMaterial,
        plate_name: calibrationPlateName,
        nozzle: calibrationNozzle,
        observed_value: calibrationObservedValue,
        notes: calibrationNotes,
        gcode_reviewed: calibrationGcodeReviewed,
        photo_reference: calibrationPhotoReference || null,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationObservedValue("");
      setCalibrationNotes("");
      setCalibrationGcodeReviewed(false);
      setCalibrationPhotoReference("");
      setCalibrationResultTestKey(null);
      setCalibrationResultFormOpen(false);
      setCalibrationActivityCleared(false);
      await loadCalibrationRuns(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadCalibrationPreflight() {
    if (!selectedPrinterId || !calibrationTestKey) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await calibrationApi.preflight(selectedPrinterId, calibrationTestKey);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationPreflight((await response.json()) as CalibrationPreflight);
      setCalibrationExecutionResult(null);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function openCalibrationExecute(test: CalibrationTestRecord) {
    setCalibrationTestKey(test.test_key);
    setCalibrationExecuteTestKey(test.test_key);
    setCalibrationExecutionResult(null);
    setCalibrationSaveConfigError("");
    setCalibrationSaveConfigResult(null);
    setCalibrationPreflight(null);
    setCalibrationGcodeReviewed(false);
    setCalibrationOperatorPresent(false);
    setCalibrationExecutionConfirmation("");
    if (!selectedPrinterId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await calibrationApi.preflight(selectedPrinterId, test.test_key);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setCalibrationPreflight((await response.json()) as CalibrationPreflight);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function openCalibrationResult(
    test: CalibrationTestRecord,
    showForm = false,
    resultStatus: CalibrationRunRecord["result_status"] = "passed",
  ) {
    const formConfig = getCalibrationResultFormConfig(test);
    setCalibrationTestKey(test.test_key);
    setCalibrationResultTestKey(test.test_key);
    setCalibrationResultFormOpen(showForm);
    setCalibrationResultStatus(resultStatus);
    setCalibrationObservedValue("");
    setCalibrationNotes("");
    setCalibrationPhotoReference("");
    setCalibrationGcodeReviewed(test.gcode.length === 0);
    if (!formConfig.showMaterial) {
      setCalibrationMaterial("");
    } else if (!calibrationMaterial.trim()) {
      setCalibrationMaterial("PLA");
    }
    if (!formConfig.showPlate) {
      setCalibrationPlateName("");
    } else if (!calibrationPlateName.trim()) {
      setCalibrationPlateName("Texturizada");
    }
    if (!formConfig.showNozzle) {
      setCalibrationNozzle("");
    } else if (!calibrationNozzle.trim()) {
      setCalibrationNozzle("T0");
    }
  }

  async function executeCalibrationGcode(confirmationOverride?: string) {
    if (!selectedPrinterId || !calibrationTestKey || calibrationExecutionInFlightRef.current) {
      return;
    }
    calibrationExecutionInFlightRef.current = true;
    setCalibrationExecutionBusy(true);
    setError(null);
    try {
      const response = await calibrationApi.execute(selectedPrinterId, {
        test_key: calibrationTestKey,
        confirmation: confirmationOverride ?? calibrationExecutionConfirmation,
        operator_present: calibrationOperatorPresent,
        gcode_reviewed: calibrationGcodeReviewed,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = (await response.json()) as CalibrationExecutionRecord;
      setCalibrationExecutionResult(payload);
      setCalibrationSaveConfigError("");
      setCalibrationSaveConfigResult(null);
      resetCalibrationConfigRemediation();
      setCalibrationActivityCleared(false);
      await loadCalibrationRuns(selectedPrinterId);
      if (payload.status === "executed") {
        setCalibrationOperatorPresent(false);
        setCalibrationGcodeReviewed(false);
        setCalibrationExecutionConfirmation("");
      }
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      calibrationExecutionInFlightRef.current = false;
      setCalibrationExecutionBusy(false);
    }
  }

  async function saveCalibrationConfigFromExecution(options: { suppressStepUpPrompt?: boolean } = {}) {
    if (!selectedPrinterId || calibrationSaveConfigBusy) {
      return;
    }
    setCalibrationSaveConfigBusy(true);
    setCalibrationSaveConfigError("");
    setError(null);
    try {
      const response = await operationApi.executeDirect(selectedPrinterId, {
        action_id: "save_config",
        parameters: {},
      });
      if (!response.ok) {
        const apiError = await readOperationApiError(response);
        setCalibrationSaveConfigError(apiError.message);
        if (apiError.stepUpRequired && !options.suppressStepUpPrompt) {
          setCalibrationStepUpPendingAction("save_config");
          setCalibrationStepUpOpen(true);
          setCalibrationStepUpError("");
        }
        return;
      }
      setCalibrationSaveConfigResult((await response.json()) as OperationActionExecutionAttempt);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setCalibrationSaveConfigBusy(false);
    }
  }

  async function previewCalibrationConfigRemediation() {
    if (!selectedPrinterId || calibrationConfigRemediationBusy) {
      return;
    }
    const request = calibrationConfigRemediationRequest();
    if (!request) {
      setCalibrationConfigRemediationError("Não consegui identificar valores calculados para corrigir o arquivo.");
      return;
    }
    setCalibrationConfigRemediationBusy(true);
    setCalibrationConfigRemediationError("");
    setCalibrationConfigRemediationApplyResult(null);
    try {
      const response = await calibrationApi.configRemediationPreview(selectedPrinterId, request);
      if (!response.ok) {
        setCalibrationConfigRemediationError(await readApiError(response));
        return;
      }
      const payload = (await response.json()) as ConfigRemediationResult;
      setCalibrationConfigRemediationPreview(payload);
      setCalibrationConfigRemediationSelectedIds((payload.candidates ?? []).filter((candidate) => candidate.changed).map((candidate) => candidate.id));
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setCalibrationConfigRemediationBusy(false);
    }
  }

  async function applyCalibrationConfigRemediation(options: { suppressStepUpPrompt?: boolean } = {}) {
    if (!selectedPrinterId || calibrationConfigRemediationBusy) {
      return;
    }
    const request = calibrationConfigRemediationRequest();
    if (!request || calibrationConfigRemediationSelectedIds.length === 0) {
      setCalibrationConfigRemediationError("Selecione pelo menos um arquivo para aplicar.");
      return;
    }
    setCalibrationConfigRemediationBusy(true);
    setCalibrationConfigRemediationError("");
    try {
      const response = await calibrationApi.configRemediationApply(selectedPrinterId, {
        ...request,
        target_ids: calibrationConfigRemediationSelectedIds,
      });
      if (!response.ok) {
        const apiError = await readOperationApiError(response);
        setCalibrationConfigRemediationError(apiError.message);
        if (apiError.stepUpRequired && !options.suppressStepUpPrompt) {
          setCalibrationStepUpPendingAction("config_remediation");
          setCalibrationStepUpOpen(true);
          setCalibrationStepUpError("");
        }
        return;
      }
      const payload = (await response.json()) as ConfigRemediationResult;
      setCalibrationConfigRemediationApplyResult(payload);
      setCalibrationConfigRemediationPreview(payload);
      await loadCalibrationRuns(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setCalibrationConfigRemediationBusy(false);
    }
  }

  function toggleCalibrationConfigRemediationTarget(targetId: string) {
    setCalibrationConfigRemediationSelectedIds((current) =>
      current.includes(targetId) ? current.filter((item) => item !== targetId) : [...current, targetId],
    );
  }

  async function submitCalibrationStepUp() {
    const password = calibrationStepUpPassword.trim();
    const code = calibrationStepUpCode.trim();
    if (authUser?.mfa_enabled) {
      if (!code) {
        setCalibrationStepUpError("Informe o código 2FA para autorizar esta ação.");
        return;
      }
    } else if (!password) {
      setCalibrationStepUpError("Informe a senha atual da conta para autorizar esta ação.");
      return;
    }
    setCalibrationStepUpBusy(true);
    setCalibrationStepUpError("");
    try {
      await authApi.createStepUpToken({
        purpose: "destructive_action",
        password: password || undefined,
        code: code || undefined,
      });
      setCalibrationStepUpPassword("");
      setCalibrationStepUpCode("");
      setCalibrationStepUpOpen(false);
      const pendingAction = calibrationStepUpPendingAction;
      setCalibrationStepUpPendingAction(null);
      if (pendingAction === "config_remediation") {
        await applyCalibrationConfigRemediation({ suppressStepUpPrompt: true });
      } else {
        await saveCalibrationConfigFromExecution({ suppressStepUpPrompt: true });
      }
    } catch (err) {
      setCalibrationStepUpError(err instanceof Error ? err.message : "Falha ao gerar autorização.");
    } finally {
      setCalibrationStepUpBusy(false);
    }
  }

  function downloadCalibrationExecutionHistoryItem(execution: CalibrationExecutionRecord) {
    downloadCalibrationHistoryJson(`calibracao-${execution.test_key}-execucao-${execution.id}.json`, {
      kind: "calibration_execution",
      exported_at: new Date().toISOString(),
      execution,
    });
  }

  function downloadCalibrationRunHistoryItem(run: CalibrationRunRecord) {
    downloadCalibrationHistoryJson(`calibracao-${run.test_key}-resultado-${run.id}.json`, {
      kind: "calibration_result",
      exported_at: new Date().toISOString(),
      run,
    });
  }

  async function deleteCalibrationExecutionHistoryItem(execution: CalibrationExecutionRecord) {
    if (!selectedPrinterId) {
      return;
    }
    const confirmed = await confirmAction({
      tone: "danger",
      title: "Apagar execução",
      detail: "Esta execução antiga sairá do histórico deste teste. O último registro permanece protegido.",
      evidence: `${formatDateTime(execution.created_at)} · ${execution.status} · ${execution.sent_commands.length} comando(s)`,
      confirmLabel: "Apagar",
    });
    if (!confirmed) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await calibrationApi.deleteExecution(selectedPrinterId, execution.id);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadCalibrationRuns(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function deleteCalibrationRunHistoryItem(run: CalibrationRunRecord) {
    if (!selectedPrinterId) {
      return;
    }
    const confirmed = await confirmAction({
      tone: "danger",
      title: "Apagar resultado",
      detail: "Este resultado antigo sairá do histórico deste teste. O último registro permanece protegido.",
      evidence: `${formatDateTime(run.created_at)} · ${run.result_status} · ${run.observed_value || run.notes || "-"}`,
      confirmLabel: "Apagar",
    });
    if (!confirmed) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await calibrationApi.deleteRun(selectedPrinterId, run.id);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      await loadCalibrationRuns(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadZOffsets(printerId: number) {
    const response = await zOffsetApi.list(printerId);
    if (!response.ok) {
      return;
    }
    const payload = (await response.json()) as { records: ZOffsetRecord[] };
    setZOffsetRecords(payload.records);
  }

  async function createZOffsetRecord(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedPrinterId) {
      return;
    }
    const parsedOffset = Number(zOffsetValue);
    if (!zOffsetPlateName.trim() || !zOffsetMaterial.trim() || !zOffsetNozzle.trim() || !Number.isFinite(parsedOffset)) {
      setError("Preencha chapa, material, toolhead e um Z-offset válido antes de registrar.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await zOffsetApi.create(selectedPrinterId, {
        plate_name: zOffsetPlateName.trim(),
        material: zOffsetMaterial.trim(),
        nozzle: zOffsetNozzle.trim(),
        offset_value: parsedOffset,
        notes: zOffsetNotes,
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      setZOffsetNotes("");
      setZOffsetFormOpen(false);
      setZOffsetWizardPlan(null);
      setZOffsetWizardChecks({});
      await loadZOffsets(selectedPrinterId);
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function evaluateZOffsetWizard() {
    if (!selectedPrinterId) {
      return;
    }
    const parsedOffset = Number(zOffsetValue);
    if (!zOffsetPlateName.trim() || !zOffsetMaterial.trim() || !zOffsetNozzle.trim() || !Number.isFinite(parsedOffset)) {
      setError("Preencha chapa, material, toolhead e um Z-offset válido antes de avaliar.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const query = new URLSearchParams({
        plate_name: zOffsetPlateName.trim(),
        material: zOffsetMaterial.trim(),
        nozzle: zOffsetNozzle.trim(),
        proposed_offset_value: String(parsedOffset),
      });
      const response = await zOffsetApi.wizardPlan(selectedPrinterId, query);
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const plan = (await response.json()) as ZOffsetWizardPlan;
      setZOffsetWizardPlan(plan);
      setZOffsetWizardChecks(
        Object.fromEntries(plan.steps.filter((step) => step.must_confirm).map((step) => [step.key, false])),
      );
    } catch (err) {
      setError(unknownErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function toggleWizardCheck(key: string) {
    setZOffsetWizardChecks((current) => ({ ...current, [key]: !current[key] }));
  }

  const selectedCalibrationTest = calibrationTests.find((test) => test.test_key === calibrationTestKey) ?? calibrationTests[0];
  const calibrationHelpTest = calibrationTests.find((test) => test.test_key === calibrationHelpTestKey);
  const calibrationExecuteTest = calibrationTests.find((test) => test.test_key === calibrationExecuteTestKey);
  const calibrationResultTest = calibrationTests.find((test) => test.test_key === calibrationResultTestKey);
  const calibrationResultFormConfig = calibrationResultTest ? getCalibrationResultFormConfig(calibrationResultTest) : null;
  const calibrationResultRuns = calibrationResultTest ? calibrationRuns.filter((run) => run.test_key === calibrationResultTest.test_key) : [];
  const calibrationResultExecutions = calibrationResultTest ? calibrationExecutions.filter((execution) => execution.test_key === calibrationResultTest.test_key) : [];
  const latestCalibrationExecutionIdByTest = new Map<string, number>();
  calibrationExecutions.forEach((execution) => {
    if (!latestCalibrationExecutionIdByTest.has(execution.test_key)) {
      latestCalibrationExecutionIdByTest.set(execution.test_key, execution.id);
    }
  });
  const latestCalibrationRunIdByTest = new Map<string, number>();
  calibrationRuns.forEach((run) => {
    if (!latestCalibrationRunIdByTest.has(run.test_key)) {
      latestCalibrationRunIdByTest.set(run.test_key, run.id);
    }
  });
  const calibrationVisibleGcodeCount = calibrationTests.filter((test) => test.gcode.length > 0).length;
  const calibrationBlockedGcodeCount = calibrationHiddenTests.length;
  const calibrationRecommended = calibrationSummary?.recommended_next_tests.slice(0, 5) ?? [];
  const hiddenCalibrationKeys = new Set(calibrationHiddenTests.map((test) => test.test_key));
  const calibrationSequencePreview = (calibrationSequence?.steps ?? []).filter((step) => !hiddenCalibrationKeys.has(step.test_key));
  const visibleCalibrationCompletedSteps = calibrationSequencePreview.filter((step) => step.status === "completed" || step.status === "skipped").length;
  const visibleCalibrationRecommendations = calibrationRecommended.filter((test) => !hiddenCalibrationKeys.has(test.test_key));
  const normalizedTestSearch = testSearch.trim().toLowerCase();
  const printLikeCategories = new Set(["primeira_camada", "material", "extrusao", "qualidade", "dimensional"]);
  const visibleCalibrationTests = calibrationTests.filter((test) => {
    if (testFilter === "executable") {
      if (test.gcode.length === 0) return false;
    }
    if (testFilter === "manual") {
      if (test.gcode.length > 0) return false;
    }
    if (testFilter === "blocked") {
      return false;
    }
    if (testUsageFilter === "print" && !printLikeCategories.has(test.category)) {
      return false;
    }
    if (testUsageFilter === "movement" && (test.gcode.length === 0 || printLikeCategories.has(test.category))) {
      return false;
    }
    if (testUsageFilter === "manual" && test.gcode.length > 0) {
      return false;
    }
    if (!normalizedTestSearch) {
      return true;
    }
    return [test.title, test.category, test.objective, test.notes, test.execution_mode, test.risk_level]
      .join(" ")
      .toLowerCase()
      .includes(normalizedTestSearch);
  });
  const visibleHiddenCalibrationTests =
    testFilter === "all" || testFilter === "blocked"
      ? calibrationHiddenTests.filter((test) => {
          if (testUsageFilter !== "all") {
            return false;
          }
          if (!normalizedTestSearch) {
            return true;
          }
          return [test.title, test.reason, test.test_key].join(" ").toLowerCase().includes(normalizedTestSearch);
        })
      : [];
  const recentCalibrationActivityCount =
    (calibrationExecutionResult ? 1 : 0) + calibrationExecutions.slice(0, 4).length + calibrationRuns.slice(0, 4).length;

  function calibrationConfigRemediationRequest() {
    const execution = calibrationExecutionResult ?? calibrationResultExecutions[0] ?? null;
    if (!execution) {
      return null;
    }
    const pid = calibrationExecutionPidParameters(execution);
    if (!pid) {
      return null;
    }
    return {
      section: "extruder",
      source: `calibration:${execution.test_key}`,
      options: [
        { option: "pid_Kp", value: String(pid.kp) },
        { option: "pid_Ki", value: String(pid.ki) },
        { option: "pid_Kd", value: String(pid.kd) },
      ],
    };
  }

  function resetCalibrationConfigRemediation() {
    setCalibrationConfigRemediationError("");
    setCalibrationConfigRemediationPreview(null);
    setCalibrationConfigRemediationApplyResult(null);
    setCalibrationConfigRemediationSelectedIds([]);
  }

  return {
    calibrationActivityCleared,
    calibrationBlockedGcodeCount,
    calibrationConfigRemediationApplyResult,
    calibrationConfigRemediationBusy,
    calibrationConfigRemediationError,
    calibrationConfigRemediationPreview,
    calibrationConfigRemediationSelectedIds,
    calibrationExecuteTest,
    calibrationExecuteTestKey,
    calibrationExecutionConfirmation,
    calibrationExecutionBusy,
    calibrationExecutionResult,
    calibrationExecutions,
    calibrationSaveConfigBusy,
    calibrationSaveConfigError,
    calibrationSaveConfigResult,
    calibrationStepUpBusy,
    calibrationStepUpCode,
    calibrationStepUpError,
    calibrationStepUpOpen,
    calibrationStepUpPassword,
    calibrationGcodeReviewed,
    calibrationHelpTest,
    calibrationHelpTestKey,
    calibrationHiddenTests,
    calibrationMaterial,
    calibrationNotes,
    calibrationNozzle,
    calibrationObservedValue,
    calibrationOperatorPresent,
    calibrationPhotoReference,
    calibrationPlateName,
    calibrationPreflight,
    calibrationRecommended,
    calibrationResultExecutions,
    calibrationResultFormConfig,
    calibrationResultFormOpen,
    calibrationResultRuns,
    calibrationResultStatus,
    calibrationResultTest,
    calibrationResultTestKey,
    calibrationRuns,
    calibrationSequence,
    calibrationSequencePreview,
    calibrationSummary,
    calibrationTestKey,
    calibrationTests,
    calibrationVisibleGcodeCount,
    createCalibrationRun,
    createZOffsetRecord,
    deleteCalibrationExecutionHistoryItem,
    deleteCalibrationRunHistoryItem,
    downloadCalibrationExecutionHistoryItem,
    downloadCalibrationRunHistoryItem,
    evaluateZOffsetWizard,
    executeCalibrationGcode,
    hiddenCalibrationKeys,
    latestCalibrationExecutionIdByTest,
    latestCalibrationRunIdByTest,
    loadCalibrationPreflight,
    loadCalibrationRuns,
    loadCalibrationTests,
    loadZOffsets,
    openCalibrationExecute,
    openCalibrationResult,
    applyCalibrationConfigRemediation,
    previewCalibrationConfigRemediation,
    recentCalibrationActivityCount,
    saveCalibrationConfigFromExecution,
    selectedCalibrationTest,
    setCalibrationActivityCleared,
    setCalibrationExecuteTestKey,
    setCalibrationExecutionConfirmation,
    setCalibrationExecutionResult,
    setCalibrationExecutions,
    setCalibrationGcodeReviewed,
    setCalibrationHelpTestKey,
    setCalibrationHiddenTests,
    setCalibrationMaterial,
    setCalibrationNotes,
    setCalibrationNozzle,
    setCalibrationObservedValue,
    setCalibrationOperatorPresent,
    setCalibrationPhotoReference,
    setCalibrationPlateName,
    setCalibrationPreflight,
    setCalibrationResultFormOpen,
    setCalibrationResultStatus,
    setCalibrationResultTestKey,
    setCalibrationRuns,
    setCalibrationSequence,
    setCalibrationSummary,
    setCalibrationTestKey,
    setCalibrationTests,
    setCalibrationStepUpCode,
    setCalibrationStepUpOpen,
    setCalibrationStepUpPassword,
    toggleCalibrationConfigRemediationTarget,
    setTestFilter,
    setTestSearch,
    setTestUsageFilter,
    setZOffsetFormOpen,
    setZOffsetMaterial,
    setZOffsetNotes,
    setZOffsetNozzle,
    setZOffsetPlateName,
    setZOffsetRecords,
    setZOffsetValue,
    setZOffsetWizardChecks,
    setZOffsetWizardPlan,
    submitCalibrationStepUp,
    testFilter,
    testSearch,
    testUsageFilter,
    toggleWizardCheck,
    visibleCalibrationCompletedSteps,
    visibleCalibrationRecommendations,
    visibleCalibrationTests,
    visibleHiddenCalibrationTests,
    zOffsetFormOpen,
    zOffsetMaterial,
    zOffsetNotes,
    zOffsetNozzle,
    zOffsetPlateName,
    zOffsetRecords,
    zOffsetValue,
    zOffsetWizardChecks,
    zOffsetWizardPlan,
  };
}

async function readOperationApiError(response: Response) {
  try {
    const payload = await response.clone().json();
    if (payload?.detail === "autenticação reforçada obrigatória para ação crítica") {
      return {
        stepUpRequired: true,
        message: "Ação crítica bloqueada. Informe sua senha para gerar autorização e continuar.",
      };
    }
  } catch {
    // Fall back to the common API error reader.
  }
  return { stepUpRequired: false, message: await readApiError(response) };
}

function downloadCalibrationHistoryJson(filename: string, payload: unknown) {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return;
  }
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
