import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { operationApi } from "../../src/services/operationApi";

describe("operationApi G-code cache recovery", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("retries a transient cache failure and returns the G-code without manual action", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValueOnce(
        Response.json(
          { detail: "agente não confirmou o cache do G-code" },
          { status: 502 },
        ),
      )
      .mockResolvedValueOnce(
        Response.json({
          status: "cached",
          cache_key: "a".repeat(64),
          printer_id: 3,
          filename: "跳舞_PLA_23m3s.gcode",
          size_bytes: 12,
          sha256: "b".repeat(64),
          created_at: "2026-07-26T14:00:00Z",
        }),
      )
      .mockResolvedValueOnce(new Response("G28\nG1 X10 Y10 E1\n"));
    vi.stubGlobal("fetch", fetchMock);
    const onRetry = vi.fn();

    const result = operationApi.gcodeCacheTextWithRecovery(
      3,
      "跳舞_PLA_23m3s.gcode",
      { onRetry },
    );
    await vi.advanceTimersByTimeAsync(1500);

    await expect(result).resolves.toContain("G1 X10");
    expect(onRetry).toHaveBeenCalledWith(1, 3);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("does not retry a permanent not-found response", async () => {
    const fetchMock = vi
      .fn<typeof fetch>()
      .mockResolvedValue(
        Response.json({ detail: "printer not found" }, { status: 404 }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      operationApi.gcodeCacheTextWithRecovery(99, "missing.gcode"),
    ).rejects.toThrow("printer not found");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
