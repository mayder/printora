import { afterEach, describe, expect, it, vi } from "vitest";
import {
  calibrationLiveEvidenceLabel,
  calibrationVisualState,
  isCalibrationVerifiedByLiveStatus,
} from "../../src/utils/calibrationLiveState";
import { startSequentialPoll } from "../../src/utils/sequentialPoll";
import {
  canRollbackSelfUpdateRun,
  formatSelfUpdateEnvironment,
  selfUpdateProgressPercent,
  selfUpdateStepDetail,
  visibleSelfUpdateSteps,
} from "../../src/selfUpdate";
import {
  isCurrentAuthGeneration,
  nextAuthGeneration,
} from "../../src/utils/authGeneration";

afterEach(() => {
  vi.useRealTimers();
});

describe("quality-critical utilities", () => {
  it("invalidates stale authentication responses after session changes", () => {
    const captured = 4;
    const current = nextAuthGeneration(captured);

    expect(isCurrentAuthGeneration(current, captured)).toBe(false);
    expect(isCurrentAuthGeneration(current, current)).toBe(true);
  });

  it("never overlaps sequential polling", async () => {
    vi.useFakeTimers();
    let resolveTask = () => {};
    const task = vi.fn(
      () =>
        new Promise<void>((resolve) => {
          resolveTask = resolve;
        }),
    );
    const stop = startSequentialPoll(task, 100);

    expect(task).toHaveBeenCalledOnce();
    await vi.advanceTimersByTimeAsync(500);
    expect(task).toHaveBeenCalledOnce();
    resolveTask();
    await Promise.resolve();
    await vi.advanceTimersByTimeAsync(100);
    expect(task).toHaveBeenCalledTimes(2);
    stop();
  });

  it("derives calibration state only from valid live evidence", () => {
    const status = {
      connected: true,
      toolhead: { homed_axes: "xyz" },
    } as never;
    const test = { test_key: "homing_endstops", risk_level: "warning" } as never;

    expect(isCalibrationVerifiedByLiveStatus("homing_endstops", status)).toBe(true);
    expect(calibrationLiveEvidenceLabel("homing_endstops", status)).toContain("xyz");
    expect(calibrationVisualState(test, undefined, undefined, status)).toBe("passed");
    expect(
      calibrationVisualState(
        test,
        { result_status: "failed" } as never,
        undefined,
        null,
      ),
    ).toBe("failed");
  });

  it("formats self-update progress and safe rollback state", () => {
    const run = {
      status: "running",
      previous_project_path: "/previous",
      steps: [
        { status: "succeeded" },
        { status: "pending" },
      ],
    } as never;
    expect(formatSelfUpdateEnvironment("unix")).toBe("Unix/macOS/Linux");
    expect(canRollbackSelfUpdateRun({ ...run, status: "succeeded" } as never)).toBe(
      true,
    );
    expect(selfUpdateProgressPercent(run)).toBe(50);
    expect(visibleSelfUpdateSteps(run)).toHaveLength(1);
    expect(
      selfUpdateStepDetail({
        status: "failed",
        log_excerpt: JSON.stringify({ steps: [] }),
      } as never),
    ).toBe("Falhou");
  });
});
