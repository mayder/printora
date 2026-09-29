import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { AuthUser } from "../../src/types";

const { createStepUpTokenMock, runMock, statusMock } = vi.hoisted(() => ({
  createStepUpTokenMock: vi.fn(),
  runMock: vi.fn(),
  statusMock: vi.fn(),
}));

vi.mock("../../src/services/authApi", () => ({
  createStepUpToken: createStepUpTokenMock,
}));

vi.mock("../../src/services/updatesApi", () => ({
  updatesApi: {
    run: runMock,
    status: statusMock,
  },
}));

import { useUpdates } from "../../src/hooks/domains/useUpdates";

const authUser = {
  id: 7,
  email: "admin@example.test",
  social_links: {},
  timezone: "America/Sao_Paulo",
  mfa_enabled: false,
  is_active: true,
  platform_admin: true,
  created_at: "2026-07-30T00:00:00Z",
  organizations: [],
} satisfies AuthUser;

const printerId = 1;

function renderUpdates(user: AuthUser | null = authUser) {
  return renderHook(() => useUpdates({
    authUser: user,
    selectedPrinterId: printerId,
    loadOperationStatus: vi.fn().mockResolvedValue(undefined),
    loadPrinterAudit: vi.fn().mockResolvedValue(undefined),
    loadPrinterChecklist: vi.fn().mockResolvedValue(undefined),
    loadPrinterHealth: vi.fn().mockResolvedValue(undefined),
    setActiveSection: vi.fn(),
    setAlertCenterOpen: vi.fn(),
    confirmAction: vi.fn(),
    showToast: vi.fn(),
    setError: vi.fn(),
    setLoading: vi.fn(),
  }));
}

describe("useUpdates authorization", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    createStepUpTokenMock.mockReset();
    runMock.mockReset();
    statusMock.mockReset();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("keeps the dialog open and explains which credential is missing", async () => {
    const hook = renderUpdates();

    act(() => hook.result.current.openUpdateDialog("moonraker"));
    await act(async () => {
      await hook.result.current.runUpdate("moonraker");
    });

    expect(hook.result.current.updateDialog?.phase).toBe("confirm");
    expect(hook.result.current.updateDialog?.authorizationError).toContain("senha atual");
    expect(createStepUpTokenMock).not.toHaveBeenCalled();
    expect(runMock).not.toHaveBeenCalled();
  });

  it("fails closed when the authenticated user is unavailable", async () => {
    const hook = renderUpdates(null);

    act(() => hook.result.current.openUpdateDialog("moonraker"));
    await act(async () => {
      await hook.result.current.runUpdate("moonraker");
    });

    expect(hook.result.current.updateDialog?.authorizationError).toBe("Sessão expirada.");
    expect(createStepUpTokenMock).not.toHaveBeenCalled();
    expect(runMock).not.toHaveBeenCalled();
  });

  it("creates a physical-operation proof and sends it only to the selected update", async () => {
    createStepUpTokenMock.mockResolvedValue({
      step_up_token: "fresh-update-proof",
      expires_at: "2026-07-30T22:30:00Z",
    });
    runMock.mockResolvedValue(Response.json({
      safe_mode: "agent_update_manager",
      action: "update",
      target: "moonraker",
      accepted: true,
      message: "Update solicitado.",
      result: {},
    }));
    statusMock.mockResolvedValue(Response.json({
      safe_mode: "moonraker_update_manager",
      busy: false,
      summary: "atualizado",
      counts: {},
      components: [{
        name: "moonraker",
        title: "Moonraker",
        configured_type: "git_repo",
        status: "up_to_date",
        commits_behind_count: 0,
        package_count: 0,
        warnings: [],
        anomalies: [],
        can_update: false,
        can_rollback: true,
        risk_level: "normal",
        requires_confirmation: false,
        alert_silenced: false,
      }],
      result: {},
    }));
    const hook = renderUpdates();

    act(() => {
      hook.result.current.openUpdateDialog("moonraker");
      hook.result.current.setUpdateDialog((current) =>
        current ? { ...current, authorizationCredential: "senha-controlada" } : current,
      );
    });
    let updatePromise!: Promise<void>;
    act(() => {
      updatePromise = hook.result.current.runUpdate("moonraker");
    });
    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(createStepUpTokenMock).toHaveBeenCalledWith({
      purpose: "setup_physical_operation",
      password: "senha-controlada",
      code: undefined,
    }, { store: false });
    expect(runMock).toHaveBeenCalledWith(
      printerId,
      { target: "moonraker", confirmation_phrase: "" },
      "fresh-update-proof",
    );

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500);
      await updatePromise;
    });
    expect(hook.result.current.updateDialog?.phase).toBe("done");
  });
});
