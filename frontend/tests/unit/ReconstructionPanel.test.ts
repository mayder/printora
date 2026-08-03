import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ReconstructionPanel } from "../../src/screens/projects/ReconstructionPanel";
import { photoReconstructionApi } from "../../src/services/photoReconstructionApi";
import { meshRevisionApi } from "../../src/services/meshRevisionApi";
import type { ReconstructionJob } from "../../src/types/photoReconstruction";


const queued: ReconstructionJob = {
  id: 11,
  capture_session_id: 8,
  project_id: 7,
  status: "queued",
  stage: "waiting",
  progress_percent: null,
  engine_policy: "auto",
  engine_key: null,
  correlation_id: "safe-correlation",
  error_code: null,
  error_message: null,
  estimated_cost_cents: null,
  actual_cost_cents: null,
  can_cancel: true,
  can_retry: false,
  next_action: "Você pode sair desta tela.",
  created_at: "2026-08-02T00:00:00Z",
  updated_at: "2026-08-02T00:00:00Z",
  attempts: [],
  artifacts: [],
  qualification: null,
};


afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("ReconstructionPanel", () => {
  it("explica a malha bruta e inicia sem exigir conhecimento técnico", async () => {
    vi.spyOn(photoReconstructionApi, "list").mockResolvedValue([]);
    const create = vi.spyOn(photoReconstructionApi, "create").mockResolvedValue(queued);
    render(React.createElement(ReconstructionPanel, { captureSessionId: 8, setError: vi.fn() }));

    expect(await screen.findByRole("heading", { name: "Criar o modelo 3D" })).toBeTruthy();
    expect(screen.getByText(/primeiro resultado é uma malha bruta/i)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Criar modelo 3D" }));

    await waitFor(() => expect(create).toHaveBeenCalledWith(8, "auto"));
    expect(await screen.findByRole("heading", { name: "Aguardando capacidade" })).toBeTruthy();
    expect(document.body.textContent).not.toContain("PKG-");
  });

  it("não inventa percentual quando o processador informa apenas estágio", async () => {
    vi.spyOn(photoReconstructionApi, "list").mockResolvedValue([queued]);
    vi.spyOn(photoReconstructionApi, "get").mockResolvedValue(queued);
    render(React.createElement(ReconstructionPanel, { captureSessionId: 8, setError: vi.fn() }));

    expect(await screen.findByRole("heading", { name: "Aguardando capacidade" })).toBeTruthy();
    expect(screen.queryByRole("progressbar")).toBeNull();
    expect(screen.getByRole("button", { name: "Cancelar" })).toBeTruthy();
  });

  it("explica por que a malha ainda não pode ser aprovada", async () => {
    const completed: ReconstructionJob = {
      ...queued,
      status: "succeeded",
      stage: "ready",
      progress_percent: 100,
      can_cancel: false,
      artifacts: [{
        id: 91, artifact_type: "raw_mesh", file_format: "obj", sha256: "abc",
        size_bytes: 100, unit: "unknown", observed_ratio: null, inferred_ratio: null, provenance: {},
      }],
      qualification: {
        id: 92,
        reconstruction_artifact_id: 91,
        analyzer_version: "deterministic-v1",
        status: "not_qualified",
        report: {
          dimensions: { x: 10, y: 20, z: 30 },
          mandatory_checks_complete: false,
          blockers: ["Confirme a unidade e uma medida conhecida do objeto."],
        },
        created_at: "2026-08-02T00:00:00Z",
      },
    };
    vi.spyOn(photoReconstructionApi, "list").mockResolvedValue([completed]);
    vi.spyOn(meshRevisionApi, "list").mockResolvedValue([]);
    render(React.createElement(ReconstructionPanel, { captureSessionId: 8, setError: vi.fn() }));

    expect(await screen.findByText("Conferência para impressão em andamento")).toBeTruthy();
    expect(screen.getByText(/unidade e uma medida conhecida/i)).toBeTruthy();
    expect(screen.getByText(/unidade ainda não confirmada/i)).toBeTruthy();
    expect(await screen.findByText("O arquivo final ainda está bloqueado")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Criar STL" })).toBeNull();
  });

  it("oferece uma correção humana recomendada e preserva a origem", async () => {
    const completed: ReconstructionJob = {
      ...queued,
      status: "succeeded",
      stage: "ready",
      progress_percent: 100,
      can_cancel: false,
      artifacts: [{
        id: 91, artifact_type: "raw_mesh", file_format: "obj", sha256: "abc",
        size_bytes: 100, unit: "mm", observed_ratio: 0.9, inferred_ratio: 0.1, provenance: {},
      }],
      qualification: {
        id: 92,
        reconstruction_artifact_id: 91,
        analyzer_version: "deterministic-v1",
        status: "not_qualified",
        report: {
          dimensions: { x: 10, y: 20, z: 30 },
          mandatory_checks_complete: false,
          blockers: ["Há triângulos sem área que precisam ser limpos."],
          checks: { degenerate_triangle_count: 2, watertight: true },
        },
        created_at: "2026-08-02T00:00:00Z",
      },
    };
    vi.spyOn(photoReconstructionApi, "list").mockResolvedValue([completed]);
    vi.spyOn(meshRevisionApi, "list").mockResolvedValue([]);
    const create = vi.spyOn(meshRevisionApi, "create").mockResolvedValue({
      id: 12, reconstruction_job_id: 11, source_artifact_id: 91, parent_revision_id: null,
      operation: "clean", parameters: { output_format: "obj" }, status: "queued",
      output_format: null, sha256: null, size_bytes: null, unit: "mm", manifest: {}, qualification: {},
      error_message: null, can_cancel: true, next_action: "A correção está na fila.",
      created_at: "2026-08-02T00:00:00Z", updated_at: "2026-08-02T00:00:00Z",
    });

    render(React.createElement(ReconstructionPanel, { captureSessionId: 8, setError: vi.fn() }));
    fireEvent.click(await screen.findByRole("button", { name: "Limpar a malha" }));

    await waitFor(() => expect(create).toHaveBeenCalledWith(11, {
      operation: "clean",
      parameters: { output_format: "obj" },
    }));
    expect(screen.getByText(/malha bruta nunca é alterada/i)).toBeTruthy();
  });
});
