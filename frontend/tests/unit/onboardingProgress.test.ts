import { beforeEach, describe, expect, it, vi } from "vitest";
import { printProjectsApi } from "../../src/services/printProjectsApi";
import { printerApi } from "../../src/services/printerApi";
import { slicingApi } from "../../src/services/slicingApi";
import {
  deriveOnboardingCompletion,
  loadOnboardingEvidence,
  nextOnboardingStep,
  readOnboardingResume,
  writeOnboardingResume,
} from "../../src/services/onboardingProgress";
import type { PrinterRecord } from "../../src/types/printers";

const printer = {
  id: 7,
  name: "Voron",
  moonraker_url: "http://printer.test:7125",
  cloud_status: "online",
  cloud_tags: [],
} as PrinterRecord;

describe("onboarding progress", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("preserves only a valid local resume point", () => {
    const saved = writeOnboardingResume(window.localStorage, "project", new Date("2026-08-02T12:00:00Z"));
    expect(readOnboardingResume(window.localStorage)).toEqual(saved);

    window.localStorage.setItem("printora.onboarding.resume.v1", "invalid-json");
    expect(readOnboardingResume(window.localStorage)).toBeNull();
    expect(window.localStorage.getItem("printora.onboarding.resume.v1")).toBeNull();
  });

  it("does not claim remote completion when dependencies are unavailable", async () => {
    vi.spyOn(printerApi, "moonrakerStatus").mockRejectedValue(new Error("offline"));
    vi.spyOn(printProjectsApi, "myProjects").mockRejectedValue(new Error("offline"));
    vi.spyOn(slicingApi, "jobs").mockRejectedValue(new Error("offline"));
    vi.spyOn(slicingApi, "preflights").mockRejectedValue(new Error("offline"));

    const evidence = await loadOnboardingEvidence([printer]);
    const completion = deriveOnboardingCompletion([
      { key: "browser", label: "Navegador", detail: "ok", status: "ready" },
      { key: "storage", label: "Retomada", detail: "ok", status: "ready" },
    ], [printer], evidence);

    expect(evidence.unavailableSources).toEqual(["moonraker", "projects", "slicing_jobs", "preflights"]);
    expect(completion.printer).toBe(false);
    expect(completion.project).toBe(false);
    expect(completion.preflight).toBe(false);
  });

  it("advances only after each verified result", () => {
    expect(nextOnboardingStep({ environment: true, printer: true, agent: false, project: false, preflight: false })).toBe("agent");
    expect(nextOnboardingStep({ environment: true, printer: true, agent: true, project: true, preflight: true })).toBe("complete");
  });
});
