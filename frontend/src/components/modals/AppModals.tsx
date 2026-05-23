import type { ComponentProps } from "react";
import { AlertCenterModal } from "./AlertCenterModal";
import { CalibrationExecuteModal } from "./CalibrationExecuteModal";
import { CalibrationHelpModal } from "./CalibrationHelpModal";
import { CalibrationResultModal } from "./CalibrationResultModal";
import { MaintenanceDoneModal } from "./MaintenanceDoneModal";
import { MaintenanceFreeModal } from "./MaintenanceFreeModal";
import { PrinterModal } from "./PrinterModal";
import { SelfUpdateModal } from "./SelfUpdateModal";
import { UpdateDialogModal } from "./UpdateDialogModal";

type AppModalsProps =
  & ComponentProps<typeof AlertCenterModal>
  & ComponentProps<typeof PrinterModal>
  & ComponentProps<typeof SelfUpdateModal>
  & ComponentProps<typeof UpdateDialogModal>
  & ComponentProps<typeof MaintenanceDoneModal>
  & ComponentProps<typeof MaintenanceFreeModal>
  & ComponentProps<typeof CalibrationHelpModal>
  & ComponentProps<typeof CalibrationExecuteModal>
  & ComponentProps<typeof CalibrationResultModal>;

export function AppModals(props: AppModalsProps) {
  return (
    <>
      <AlertCenterModal {...props} />
      <PrinterModal {...props} />
      <SelfUpdateModal {...props} />
      <UpdateDialogModal {...props} />
      <MaintenanceDoneModal {...props} />
      <MaintenanceFreeModal {...props} />
      <CalibrationHelpModal {...props} />
      <CalibrationExecuteModal {...props} />
      <CalibrationResultModal {...props} />
    </>
  );
}
