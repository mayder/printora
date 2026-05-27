import { apiResponse } from "./http";

export const firmwareApi = {
  catalog: () => apiResponse("/api/firmware/catalog"),
  boardPresets: () => apiResponse("/api/firmware/board-presets"),
  configPreview: (presetId: string) => apiResponse(`/api/firmware/board-presets/${presetId}/config-preview`),
  hardwareInventory: (printerId: number) => apiResponse(`/api/printers/${printerId}/firmware/hardware-inventory`),
  boards: (printerId: number) => apiResponse(`/api/printers/${printerId}/firmware/boards`),
  buildRuns: (printerId: number) => apiResponse(`/api/printers/${printerId}/firmware/build-runs`),
  createBoard: (printerId: number, body: unknown) =>
    apiResponse(`/api/printers/${printerId}/firmware/boards`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  buildDryRun: (boardId: number, body: unknown) =>
    apiResponse(`/api/firmware/boards/${boardId}/build-runs/dry-run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  buildPreflight: (boardId: number, body: unknown) =>
    apiResponse(`/api/firmware/boards/${boardId}/build-runs/preflight`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  executeBuildLocal: (boardId: number, body: unknown) =>
    apiResponse(`/api/firmware/boards/${boardId}/build-runs/execute-local`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  recoveryPlan: (boardId: number) => apiResponse(`/api/firmware/boards/${boardId}/recovery-plan`),
};
