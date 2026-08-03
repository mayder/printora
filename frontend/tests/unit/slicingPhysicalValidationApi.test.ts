import { afterEach, describe, expect, it, vi } from "vitest";
import { slicingApi } from "../../src/services/slicingApi";


afterEach(() => vi.restoreAllMocks());

describe("slicingApi physical validation", () => {
  it("sends measured axes with an idempotency key", async () => {
    vi.spyOn(crypto, "randomUUID").mockReturnValue("00000000-0000-4000-8000-000000000003");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: 9 }), { status: 200 }),
    );

    await slicingApi.createMeshPhysicalValidation(42, {
      outcome: "needs_adjustment",
      instrument_label: "Paquímetro digital",
      measured_x_mm: 20.4,
      note: "Peça fria",
    });

    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/api\/slicing\/history\/42\/mesh-physical-validation$/);
    const init = fetchMock.mock.calls[0][1];
    expect(new Headers(init?.headers).get("Idempotency-Key")).toContain("mesh-pilot-42-");
    expect(JSON.parse(String(init?.body))).toEqual({
      outcome: "needs_adjustment",
      instrument_label: "Paquímetro digital",
      measured_x_mm: 20.4,
      note: "Peça fria",
    });
  });
});
