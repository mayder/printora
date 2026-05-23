import React from "react";

const selectedPrinterStorageKey = "printora-selected-printer-id";

function getInitialSelectedPrinterId(): number | null {
  const storedPrinterId = Number(window.localStorage.getItem(selectedPrinterStorageKey));
  return Number.isInteger(storedPrinterId) && storedPrinterId > 0 ? storedPrinterId : null;
}

export function useSelectedPrinterPreference(): [number | null, React.Dispatch<React.SetStateAction<number | null>>] {
  const [selectedPrinterId, setSelectedPrinterId] = React.useState<number | null>(() => getInitialSelectedPrinterId());

  React.useEffect(() => {
    if (selectedPrinterId) {
      window.localStorage.setItem(selectedPrinterStorageKey, String(selectedPrinterId));
      return;
    }
    window.localStorage.removeItem(selectedPrinterStorageKey);
  }, [selectedPrinterId]);

  return [selectedPrinterId, setSelectedPrinterId];
}
