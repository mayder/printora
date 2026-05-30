import { apiRequest } from "./http";
import type {
  SetupCanApplyResponse,
  SetupCanPlanResponse,
  SetupCanPreflightResponse,
  SetupCanRunRecord,
  SetupFirmwareBuildResponse,
  SetupFirmwarePlanResponse,
  SetupFirmwareRunRecord,
  SetupFlashExecuteResponse,
  SetupFlashPlanResponse,
  SetupFlashPreflightResponse,
  SetupFlashRunRecord,
  SetupSshPlanResponse,
  SetupSshPreflightResponse,
  SetupSshRunRecord,
  SetupSshTarget,
} from "../types";

export const setupApi = {
  preflight: (body: SetupSshTarget) =>
    apiRequest<SetupSshPreflightResponse>("/api/setup/ssh/preflight", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  plan: (body: SetupSshTarget) =>
    apiRequest<SetupSshPlanResponse>("/api/setup/ssh/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  history: () => apiRequest<{ runs: SetupSshRunRecord[] }>("/api/setup/ssh/history"),
  canPreflight: (body: unknown) =>
    apiRequest<SetupCanPreflightResponse>("/api/setup/can/preflight", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  canPlan: (body: unknown) =>
    apiRequest<SetupCanPlanResponse>("/api/setup/can/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  canApply: (body: unknown) =>
    apiRequest<SetupCanApplyResponse>("/api/setup/can/apply", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  canHistory: () => apiRequest<{ runs: SetupCanRunRecord[] }>("/api/setup/can/history"),
  firmwarePlan: (body: unknown) =>
    apiRequest<SetupFirmwarePlanResponse>("/api/setup/firmware/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  firmwareBuild: (body: unknown) =>
    apiRequest<SetupFirmwareBuildResponse>("/api/setup/firmware/build", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  firmwareHistory: () => apiRequest<{ runs: SetupFirmwareRunRecord[] }>("/api/setup/firmware/history"),
  flashPreflight: (body: unknown) =>
    apiRequest<SetupFlashPreflightResponse>("/api/setup/flash/preflight", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  flashPlan: (body: unknown) =>
    apiRequest<SetupFlashPlanResponse>("/api/setup/flash/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  flashExecute: (body: unknown) =>
    apiRequest<SetupFlashExecuteResponse>("/api/setup/flash/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  flashHistory: () => apiRequest<{ runs: SetupFlashRunRecord[] }>("/api/setup/flash/history"),
};
