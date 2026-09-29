import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MonitoringDashboard } from "../../src/components/monitoring/MonitoringDashboard";

describe("MonitoringDashboard loading state", () => {
  it("does not report an outdated agent before the first status arrives", () => {
    render(
      React.createElement(MonitoringDashboard, {
        selectedPrinterName: "Voron 2.4",
        operationStatus: null,
        operationStatusLoading: true,
        operationActionHistory: [],
        operationActionParameters: {},
        operationActionPreview: null,
        operationExecutionAttempt: null,
        operationExecutionHistory: [],
        operationExecutionPhrase: "",
        health: null,
        canSummary: null,
        canRecords: [],
        canComparison: null,
        loading: false,
        onRefresh: vi.fn(),
        onCompareCan: vi.fn(),
        onPreviewAction: vi.fn(),
        onPreflightAction: vi.fn(),
        onExecuteAction: vi.fn(),
        onActionParameterChange: vi.fn(),
        onExecutionPhraseChange: vi.fn(),
        onValidateExecutionGate: vi.fn(),
        onOpenGcodeFiles: vi.fn(),
      }),
    );

    expect(screen.getByText("Buscando dados do agente")).toBeTruthy();
    expect(screen.getByText("carregando")).toBeTruthy();
    expect(screen.queryByText("Agente precisa atualizar")).toBeNull();
  });
});
