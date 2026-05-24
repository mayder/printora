import { MonitoringDashboard } from "../MonitoringDashboard";
import type { ScreenPropsFor } from "./ScreenProps";

type MonitoringScreenProps = ScreenPropsFor<
  | "canComparison"
  | "canRecords"
  | "canSummary"
  | "compareLatestCanRecords"
  | "health"
  | "loadOperationStatus"
  | "loading"
  | "operationStatus"
  | "selectedPrinter"
  | "selectedPrinterId"
>;

export function MonitoringScreen(props: MonitoringScreenProps) {
  const {
    canComparison,
    canRecords,
    canSummary,
    compareLatestCanRecords,
    health,
    loadOperationStatus,
    loading,
    operationStatus,
    selectedPrinter,
    selectedPrinterId,
  } = props;

  return (
    <>
        <MonitoringDashboard
          selectedPrinterName={selectedPrinter?.name ?? "Impressora não selecionada"}
          operationStatus={operationStatus}
          health={health}
          canSummary={canSummary}
          canRecords={canRecords}
          canComparison={canComparison}
          loading={loading}
          onRefresh={() => selectedPrinterId ? void loadOperationStatus(selectedPrinterId, { preserveData: true }) : undefined}
          onCompareCan={() => void compareLatestCanRecords()}
        />


    </>
  );
}
