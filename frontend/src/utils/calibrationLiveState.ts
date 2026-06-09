import type { CalibrationExecutionRecord, CalibrationRunRecord, CalibrationTestRecord, OperationStatusResponse } from "../types";

export function isCalibrationVerifiedByLiveStatus(testKey: string, operationStatus: OperationStatusResponse | null) {
  if (testKey !== "homing_endstops" || !operationStatus?.connected) {
    return false;
  }
  const homedAxes = String(operationStatus.toolhead?.homed_axes ?? "").toLowerCase();
  return ["x", "y", "z"].every((axis) => homedAxes.includes(axis));
}

export function calibrationLiveEvidenceLabel(testKey: string, operationStatus: OperationStatusResponse | null) {
  if (!isCalibrationVerifiedByLiveStatus(testKey, operationStatus)) {
    return "";
  }
  return `Detectado: homed ${String(operationStatus?.toolhead?.homed_axes ?? "xyz")}`;
}

export function calibrationVisualState(
  test: CalibrationTestRecord,
  lastRun: CalibrationRunRecord | undefined,
  lastExecution: CalibrationExecutionRecord | undefined,
  operationStatus: OperationStatusResponse | null,
) {
  if (lastRun?.result_status === "passed" || isCalibrationVerifiedByLiveStatus(test.test_key, operationStatus)) {
    return "passed";
  }
  if (lastRun?.result_status === "failed") {
    return "failed";
  }
  if (lastRun?.result_status === "warning" || lastRun?.result_status === "skipped") {
    return lastRun.result_status;
  }
  if (lastExecution?.status === "executed" || lastExecution?.status === "dispatched_unconfirmed") {
    return "passed";
  }
  if (lastExecution?.status === "failed" || lastExecution?.status === "failed_partial") {
    return "failed";
  }
  return test.risk_level;
}
