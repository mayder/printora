import { apiResponse } from "./http";

export const firmwareApi = {
  boardPresets: () => apiResponse("/api/firmware/board-presets"),
  hardwareInventory: (printerId: number) => apiResponse(`/api/printers/${printerId}/firmware/hardware-inventory`),
  boards: (printerId: number) => apiResponse(`/api/printers/${printerId}/firmware/boards`),
  buildRuns: (printerId: number) => apiResponse(`/api/printers/${printerId}/firmware/build-runs`),
  flashRuns: (printerId: number) => apiResponse(`/api/printers/${printerId}/firmware/flash-runs`),
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
  flashDryRun: (boardId: number, body: unknown) =>
    apiResponse(`/api/firmware/boards/${boardId}/flash-runs/dry-run`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  flashPreflight: (boardId: number, body: unknown) =>
    apiResponse(`/api/firmware/boards/${boardId}/flash-runs/preflight`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  executeFlash: (boardId: number, body: unknown) =>
    apiResponse(`/api/firmware/boards/${boardId}/flash-runs/execute`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  recoveryPlan: (boardId: number) => apiResponse(`/api/firmware/boards/${boardId}/recovery-plan`),
};
