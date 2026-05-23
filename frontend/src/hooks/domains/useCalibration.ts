import React from "react";
import { calibrationApi } from "../../services/calibrationApi";
import { zOffsetApi } from "../../services/zOffsetApi";
import type {
  CalibrationAvailableTestsResponse,
  CalibrationExecutionRecord,
  CalibrationPreflight,
  CalibrationRunRecord,
  CalibrationSequencePlan,
  CalibrationSummary,
  CalibrationTestRecord,
  ZOffsetRecord,
  ZOffsetWizardPlan,
} from "../../types";
import { getCalibrationResultFormConfig } from "../../utils/formatters";
import type { SetError, SetLoading } from "./shared";
import { unknownErrorMessage } from "./shared";

type UseCalibrationOptions = {
  selectedPrinterId: number | null;
  setError: SetError;
  setLoading: SetLoading;
};

export function useCalibration({ selectedPrinterId, setError, setLoading }: UseCalibrationOptions) {
  const [calibrationTests, setCalibrationTests] = React.useState<CalibrationTestRecord[]>([]);
  const [calibrationHiddenTests, setCalibrationHiddenTests] = React.useState<CalibrationAvailableTestsResponse["hidden_tests"]>([]);
  const [calibrationRuns, setCalibrationRuns] = React.useState<CalibrationRunRecord[]>([]);
  const [calibrationSummary, setCalibrationSummary] = React.useState<CalibrationSummary | null>(null);
  const [calibrationSequence, setCalibrationSequence] = React.useState<CalibrationSequencePlan | null>(null);
  const [calibrationPreflight, setCalibrationPreflight] = React.useState<CalibrationPreflight | null>(null);
  const [calibrationExecutions, setCalibrationExecutions] = React.useState<CalibrationExecutionRecord[]>([]);
  const [calibrationExecutionResult, setCalibrationExecutionResult] = React.useState<CalibrationExecutionRecord | null>(null);
  const [calibrationHelpTestKey, setCalibrationHelpTestKey] = React.useState<string | null>(null);
  const [calibrationExecuteTestKey, setCalibrationExecuteTestKey] = React.useState<string | null>(null);
  const [calibrationResultTestKey, setCalibrationResultTestKey] = React.useState<string | null>(null);
  const [calibrationResultFormOpen, setCalibrationResultFormOpen] = React.useState(false);
  const [calibrationActivityCleared, setCalibrationActivityCleared] = React.useState(false);
  const [testFilter, setTestFilter] = React.useState<"all" | "executable" | "manual" | "blocked">("all");
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
    if (!selectedPrinterId || !calibrationTestKey) {
      return;
    }
    setLoading(true);
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
  const calibrationVisibleGcodeCount = calibrationTests.filter((test) => test.gcode.length > 0).length;
  const calibrationBlockedGcodeCount = calibrationHiddenTests.length;
  const calibrationRecommended = calibrationSummary?.recommended_next_tests.slice(0, 5) ?? [];
  const hiddenCalibrationKeys = new Set(calibrationHiddenTests.map((test) => test.test_key));
  const calibrationSequencePreview = (calibrationSequence?.steps ?? []).filter((step) => !hiddenCalibrationKeys.has(step.test_key));
  const visibleCalibrationCompletedSteps = calibrationSequencePreview.filter((step) => step.status === "completed" || step.status === "skipped").length;
  const visibleCalibrationRecommendations = calibrationRecommended.filter((test) => !hiddenCalibrationKeys.has(test.test_key));
  const visibleCalibrationTests = calibrationTests.filter((test) => {
    if (testFilter === "executable") {
      return test.gcode.length > 0;
    }
    if (testFilter === "manual") {
      return test.gcode.length === 0;
    }
    return testFilter !== "blocked";
  });
  const visibleHiddenCalibrationTests = testFilter === "all" || testFilter === "blocked" ? calibrationHiddenTests : [];
  const recentCalibrationActivityCount =
    (calibrationExecutionResult ? 1 : 0) + calibrationExecutions.slice(0, 4).length + calibrationRuns.slice(0, 4).length;

  return {
    calibrationActivityCleared,
    calibrationBlockedGcodeCount,
    calibrationExecuteTest,
    calibrationExecuteTestKey,
    calibrationExecutionConfirmation,
    calibrationExecutionResult,
    calibrationExecutions,
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
    evaluateZOffsetWizard,
    executeCalibrationGcode,
    hiddenCalibrationKeys,
    loadCalibrationPreflight,
    loadCalibrationRuns,
    loadCalibrationTests,
    loadZOffsets,
    openCalibrationExecute,
    openCalibrationResult,
    recentCalibrationActivityCount,
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
    setTestFilter,
    setZOffsetFormOpen,
    setZOffsetMaterial,
    setZOffsetNotes,
    setZOffsetNozzle,
    setZOffsetPlateName,
    setZOffsetRecords,
    setZOffsetValue,
    setZOffsetWizardChecks,
    setZOffsetWizardPlan,
    testFilter,
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
