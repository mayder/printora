import { beforeEach, describe, expect, it, vi } from "vitest";

const catalogPayload = { manufacturers: [] };

async function loadSocialApi() {
  vi.resetModules();
  return (await import("../../src/services/socialApi")).socialApi;
}

describe("socialApi", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("reuses concurrent and cached catalog requests", async () => {
    let resolveFetch: ((response: Response) => void) | null = null;
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(
      () =>
        new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        }),
    );
    const socialApi = await loadSocialApi();

    const requests = Promise.all([
      socialApi.catalog(),
      socialApi.catalog(),
      socialApi.catalog(),
    ]);

    expect(fetchMock).toHaveBeenCalledOnce();
    resolveFetch?.(Response.json(catalogPayload));
    await expect(requests).resolves.toEqual([
      catalogPayload,
      catalogPayload,
      catalogPayload,
    ]);

    await expect(socialApi.catalog()).resolves.toEqual(catalogPayload);
    expect(fetchMock).toHaveBeenCalledOnce();
  });

  it("invalidates the catalog cache after catalog writes", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(Response.json(catalogPayload))
      .mockResolvedValueOnce(Response.json({ id: 123 }))
      .mockResolvedValueOnce(Response.json(catalogPayload));
    const socialApi = await loadSocialApi();

    await socialApi.catalog();
    await socialApi.createCatalogVariant({ model_id: 1, name: "Voron Test" });
    await socialApi.catalog();

    expect(fetchMock.mock.calls.map(([input]) => new URL(String(input)).pathname)).toEqual([
      "/api/catalog",
      "/api/catalog/variants",
      "/api/catalog",
    ]);
  });
});
