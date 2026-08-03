import { afterEach, describe, expect, it, vi } from "vitest";
import { meshRevisionApi } from "../../src/services/meshRevisionApi";


afterEach(() => vi.restoreAllMocks());

describe("meshRevisionApi", () => {
  it("creates an owner-scoped revision with a unique idempotency key", async () => {
    vi.spyOn(crypto, "randomUUID").mockReturnValue("00000000-0000-4000-8000-000000000001");
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ id: 17 }), { status: 200 }),
    );

    await meshRevisionApi.create(11, {
      operation: "clean",
      parameters: { output_format: "obj" },
    });

    expect(String(fetchMock.mock.calls[0][0])).toMatch(/\/api\/photo-reconstructions\/11\/mesh-revisions$/);
    const init = fetchMock.mock.calls[0][1];
    expect(new Headers(init?.headers).get("Idempotency-Key")).toContain("00000000-0000-4000-8000-000000000001");
    expect(JSON.parse(String(init?.body))).toEqual({ operation: "clean", parameters: { output_format: "obj" } });
  });
});
