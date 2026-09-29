import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { OnboardingScreen } from "../../src/screens/OnboardingScreen";
import { printProjectsApi } from "../../src/services/printProjectsApi";
import { printerApi } from "../../src/services/printerApi";
import { slicingApi } from "../../src/services/slicingApi";
import type { PrintoraScreenProps } from "../../src/hooks/usePrintoraApp";

function onboardingProps(overrides: Partial<PrintoraScreenProps> = {}): PrintoraScreenProps {
  return {
    printers: [],
    fleetPairingOverviews: {},
    loadPrinters: vi.fn().mockResolvedValue(undefined),
    loadFleetAgentPairings: vi.fn().mockResolvedValue(undefined),
    openCreatePrinterModal: vi.fn(),
    openEditPrinterModal: vi.fn(),
    selectPrinter: vi.fn(),
    setActiveSection: vi.fn(),
    ...overrides,
  } as unknown as PrintoraScreenProps;
}

describe("OnboardingScreen", () => {
  beforeEach(() => {
    vi.spyOn(printProjectsApi, "myProjects").mockResolvedValue([]);
    vi.spyOn(slicingApi, "jobs").mockResolvedValue([]);
    vi.spyOn(slicingApi, "preflights").mockResolvedValue([]);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("guides an empty installation without exposing internal package names", async () => {
    const props = onboardingProps();
    render(React.createElement(OnboardingScreen, props));

    expect(await screen.findByText("Prepare sua primeira impressão com segurança")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Conectar a impressora/ }));
    fireEvent.click(screen.getByRole("button", { name: "Cadastrar minha impressora" }));

    expect(props.openCreatePrinterModal).toHaveBeenCalledTimes(1);
    expect(document.body.textContent).not.toContain("PKG-");
  });

  it("keeps the local return point when remote checks fail", async () => {
    window.localStorage.setItem("printora.onboarding.resume.v1", JSON.stringify({ step: "project", updatedAt: "2026-08-02T12:00:00Z" }));
    vi.spyOn(printerApi, "moonrakerStatus").mockRejectedValue(new Error("offline"));
    vi.spyOn(printProjectsApi, "myProjects").mockRejectedValue(new Error("offline"));
    vi.spyOn(slicingApi, "jobs").mockRejectedValue(new Error("offline"));
    vi.spyOn(slicingApi, "preflights").mockRejectedValue(new Error("offline"));
    const printer = { id: 7, name: "Voron", cloud_status: "offline", cloud_tags: [] } as PrintoraScreenProps["printers"][number];

    render(React.createElement(OnboardingScreen, onboardingProps({ printers: [printer] })));

    expect(await screen.findByText("Não foi possível confirmar todas as etapas agora")).toBeTruthy();
    await waitFor(() => expect(screen.getByRole("button", { name: /Escolher o primeiro projeto/ }).getAttribute("aria-current")).toBe("step"));
    expect(JSON.parse(window.localStorage.getItem("printora.onboarding.resume.v1") ?? "{}").step).toBe("project");
  });
});
