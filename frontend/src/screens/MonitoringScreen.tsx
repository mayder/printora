import { MonitoringDashboard } from "../MonitoringDashboard";
import type { ScreenPropsFor } from "./ScreenProps";

type MonitoringScreenProps = ScreenPropsFor<
  | "canComparison"
  | "canRecords"
  | "canSummary"
  | "compareLatestCanRecords"
  | "health"
  | "loadOfflineOperationFixture"
  | "loadOperationStatus"
  | "loading"
  | "operationStatus"
  | "operationActionHistory"
  | "operationActionParameters"
  | "operationActionPreview"
  | "operationExecutionAttempt"
  | "operationExecutionHistory"
  | "operationExecutionPhrase"
  | "preflightOperationAction"
  | "previewOperationAction"
  | "selectedPrinter"
  | "selectedPrinterId"
  | "setOperationExecutionPhrase"
  | "updateOperationActionParameter"
  | "validateOperationExecutionGate"
>;

export function MonitoringScreen(props: MonitoringScreenProps) {
  const {
    canComparison,
    canRecords,
    canSummary,
    compareLatestCanRecords,
    health,
    loadOfflineOperationFixture,
    loadOperationStatus,
    loading,
    operationStatus,
    operationActionHistory,
    operationActionParameters,
    operationActionPreview,
    operationExecutionAttempt,
    operationExecutionHistory,
    operationExecutionPhrase,
    preflightOperationAction,
    previewOperationAction,
    selectedPrinter,
    selectedPrinterId,
    setOperationExecutionPhrase,
    updateOperationActionParameter,
    validateOperationExecutionGate,
  } = props;

  return (
    <>
        <MonitoringDashboard
          selectedPrinterName={selectedPrinter?.name ?? "Impressora não selecionada"}
          operationStatus={operationStatus}
          operationActionHistory={operationActionHistory}
          operationActionParameters={operationActionParameters}
          operationActionPreview={operationActionPreview}
          operationExecutionAttempt={operationExecutionAttempt}
          operationExecutionHistory={operationExecutionHistory}
          operationExecutionPhrase={operationExecutionPhrase}
          health={health}
          canSummary={canSummary}
          canRecords={canRecords}
          canComparison={canComparison}
          loading={loading}
          onRefresh={() => selectedPrinterId ? void loadOperationStatus(selectedPrinterId, { preserveData: true }) : undefined}
          onLoadOfflineFixture={loadOfflineOperationFixture}
          onCompareCan={() => void compareLatestCanRecords()}
          onPreviewAction={previewOperationAction}
          onPreflightAction={preflightOperationAction}
          onActionParameterChange={updateOperationActionParameter}
          onExecutionPhraseChange={setOperationExecutionPhrase}
          onValidateExecutionGate={validateOperationExecutionGate}
        />


    </>
  );
}
