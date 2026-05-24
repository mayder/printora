import type { BoardPreset } from "../../types";

export function formatConnectionType(connectionType: BoardPreset["connection_type"]) {
  const labels: Record<BoardPreset["connection_type"], string> = {
    usb: "USB",
    can: "CAN",
    usb_can_bridge: "USB-CAN bridge",
  };
  return labels[connectionType];
}
