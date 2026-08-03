import { beforeEach, describe, expect, it, vi } from "vitest";
import { createStepUpToken } from "../../src/services/authApi";
import { updatesApi } from "../../src/services/updatesApi";

describe("update authorization API", () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.restoreAllMocks();
  });

  it("does not persist an operation-specific proof", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(Response.json({
      step_up_token: "physical-operation-proof",
      expires_at: "2026-07-30T22:30:00Z",
    }));

    await createStepUpToken({
      purpose: "setup_physical_operation",
      password: "senha-controlada",
    }, { store: false });

    expect(window.localStorage.length).toBe(0);
  });

  it("sends the explicit one-time proof in the protected update request", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      Response.json({ accepted: true }),
    );

    await updatesApi.run(3, { target: "moonraker" }, "physical-operation-proof");

    const headers = new Headers(fetchMock.mock.calls[0][1]?.headers);
    expect(headers.get("X-Printora-Step-Up")).toBe("physical-operation-proof");
  });
});
