import { afterEach, describe, expect, it, vi } from "vitest";
import { photoCaptureApi } from "../../src/services/photoCaptureApi";


afterEach(() => vi.restoreAllMocks());

describe("photoCaptureApi", () => {
  it("sends JSON explicitly when creating a private capture", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ id: 8 }), { status: 200 }));

    await photoCaptureApi.create(7, 24);

    const init = fetchMock.mock.calls[0][1];
    expect(new Headers(init?.headers).get("Content-Type")).toBe("application/json");
    expect(JSON.parse(String(init?.body))).toEqual({ project_id: 7, target_photo_count: 24, consent_confirmed: true });
  });

  it("uses an idempotency key tied to the slot and file", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ id: 8 }), { status: 200 }));
    const file = new File(["photo"], "object.png", { type: "image/png" });

    await photoCaptureApi.upload(8, file, 3, "high");

    const init = fetchMock.mock.calls[0][1];
    expect(new Headers(init?.headers).get("Idempotency-Key")).toContain("8-3-object.png");
    expect(String(fetchMock.mock.calls[0][0])).toContain("capture_index=3");
  });
});
