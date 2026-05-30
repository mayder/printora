import { apiRequest } from "./http";
import type { SetupSshPlanResponse, SetupSshPreflightResponse, SetupSshRunRecord, SetupSshTarget } from "../types";

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
};
