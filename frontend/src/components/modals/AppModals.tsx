import type { ScreenProps } from "../../screens/ScreenProps";
import { AlertCenterModal } from "./AlertCenterModal";
import { MaintenanceModals } from "./MaintenanceModals";
import { PrinterModal } from "./PrinterModal";
import { SelfUpdateModal } from "./SelfUpdateModal";
import { UpdateDialogModal } from "./UpdateDialogModal";

export function AppModals(props: ScreenProps) {
  return (
    <>
      <AlertCenterModal {...props} />
      <PrinterModal {...props} />
      <SelfUpdateModal {...props} />
      <UpdateDialogModal {...props} />
      <MaintenanceModals {...props} />
    </>
  );
}
