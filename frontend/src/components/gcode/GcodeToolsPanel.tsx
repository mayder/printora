import { GcodeManagerPanel } from "./GcodeManagerPanel";
import { GcodeUploadPanel } from "./GcodeUploadPanel";

type Toast = { tone: "success" | "warning" | "danger" | "info"; title: string; detail: string };

export function GcodeToolsPanel(props: {
  confirmAction: (options: { tone: "danger" | "warning"; title: string; detail: string; evidence: string; confirmLabel: string }) => Promise<boolean>;
  currentDirectory: string;
  directories: string[];
  onChanged: () => Promise<void>;
  printerId: number;
  selectedFiles: string[];
  showToast: (toast: Toast) => void;
}) {
  return (
    <>
      <GcodeUploadPanel
        confirmAction={props.confirmAction}
        directory={props.currentDirectory}
        printerId={props.printerId}
        onUploaded={props.onChanged}
        showToast={props.showToast}
      />
      <GcodeManagerPanel {...props} />
    </>
  );
}
