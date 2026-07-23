import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  AUTH_SESSION_EXPIRED_EVENT,
  apiOptional,
  apiRequest,
  apiResponse,
  readApiError,
  storeAuthToken,
  storeStepUpToken,
} from "../../src/services/http";

describe("HTTP client", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("sanitizes gateway and oversized errors", async () => {
    expect(
      await readApiError(
        new Response("<!doctype html>cloudflare error 524", { status: 524 }),
      ),
    ).toContain("limite do gateway");
    expect(
      await readApiError(
        Response.json(
          { detail: "autenticação reforçada obrigatória para ação crítica" },
          { status: 403 },
        ),
      ),
    ).toContain("Conta > 2FA");
    expect(
      await readApiError(new Response("x".repeat(600), { status: 500 })),
    ).toHaveLength(500);
    expect(await readApiError(new Response("", { status: 502 }))).toBe("Erro 502");
  });

  it("adds auth, parses results and supports empty responses", async () => {
    storeAuthToken("token");
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response('{"ok":true}', { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));

    await expect(apiRequest<{ ok: boolean }>("/api/test")).resolves.toEqual({
      ok: true,
    });
    await expect(apiRequest<void>("/api/test", { method: "POST" })).resolves.toBe(
      undefined,
    );
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get("Authorization")).toBe(
      "Bearer token",
    );
  });

  it("expires stored credentials on unauthorized responses", async () => {
    storeAuthToken("token");
    storeStepUpToken("step-up");
    const listener = vi.fn();
    window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, listener);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({ detail: "unauthorized" }, { status: 401 }),
    );

    await expect(apiOptional("/api/private")).resolves.toBeNull();
    expect(window.localStorage.length).toBe(0);
    expect(listener).toHaveBeenCalledOnce();

    window.removeEventListener(AUTH_SESSION_EXPIRED_EVENT, listener);
  });

  it("returns raw responses and throws readable API errors", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response("ok", { status: 200 }))
      .mockResolvedValueOnce(
        Response.json({ message: "falha controlada" }, { status: 429 }),
      );

    await expect(apiResponse("/health")).resolves.toHaveProperty("status", 200);
    await expect(apiRequest("/api/fail")).rejects.toThrow("falha controlada");
  });

  it("preserves explicit auth and handles optional non-auth failures", async () => {
    storeAuthToken("stored");
    storeStepUpToken(null);
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response("", { status: 200 }))
      .mockResolvedValueOnce(
        Response.json({ detail: "limite atingido" }, { status: 429 }),
      );

    await expect(
      apiRequest("/api/empty", {
        headers: { Authorization: "Bearer explicit" },
      }),
    ).resolves.toBeUndefined();
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get("Authorization")).toBe(
      "Bearer explicit",
    );
    await expect(apiOptional("/api/limited")).rejects.toThrow("limite atingido");
    storeAuthToken(null);
  });
});
