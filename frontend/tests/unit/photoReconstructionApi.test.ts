import { afterEach, describe, expect, it, vi } from "vitest";
import { photoReconstructionApi } from "../../src/services/photoReconstructionApi";


afterEach(() => vi.restoreAllMocks());

describe("photoReconstructionApi", () => {
  it("creates an idempotent private reconstruction job", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ id: 11 }), { status: 200 }));

    await photoReconstructionApi.create(8, "auto");

    const init = fetchMock.mock.calls[0][1];
    expect(new Headers(init?.headers).get("Idempotency-Key")).toBe("capture-8-auto");
    expect(JSON.parse(String(init?.body))).toEqual({ capture_session_id: 8, engine_policy: "auto" });
  });
});
