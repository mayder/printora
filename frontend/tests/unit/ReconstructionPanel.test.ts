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
    vi.spyOn(meshRevisionApi, "listReviews").mockResolvedValue([]);
    render(React.createElement(ReconstructionPanel, { captureSessionId: 8, setError: vi.fn() }));

    expect(await screen.findByText("Conferência para impressão em andamento")).toBeTruthy();
    expect(screen.getByText(/unidade e uma medida conhecida/i)).toBeTruthy();
    expect(screen.getByText(/unidade ainda não confirmada/i)).toBeTruthy();
    expect(await screen.findByText("Confirmar o tamanho real")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Criar STL" })).toBeNull();
  });

  it("transforma uma medida conhecida em escala explícita sem termos técnicos", async () => {
    const completed: ReconstructionJob = {
      ...queued,
      status: "succeeded", stage: "ready", progress_percent: 100, can_cancel: false,
      artifacts: [{ id: 91, artifact_type: "raw_mesh", file_format: "obj", sha256: "abc", size_bytes: 100, unit: "unknown", observed_ratio: null, inferred_ratio: null, provenance: {} }],
      qualification: {
        id: 92, reconstruction_artifact_id: 91, analyzer_version: "deterministic-v1", status: "not_qualified",
        report: { dimensions: { x: 10, y: 20, z: 30 }, checks: { watertight: true, self_intersection_count: 0, non_manifold_edge_count: 0 } },
        created_at: "2026-08-02T00:00:00Z",
      },
    };
    vi.spyOn(photoReconstructionApi, "list").mockResolvedValue([completed]);
    vi.spyOn(meshRevisionApi, "list").mockResolvedValue([]);
    vi.spyOn(meshRevisionApi, "listReviews").mockResolvedValue([]);
    const create = vi.spyOn(meshRevisionApi, "create").mockResolvedValue({
      id: 13, reconstruction_job_id: 11, source_artifact_id: 91, parent_revision_id: null,
      operation: "scale", parameters: {}, status: "queued", output_format: null, sha256: null,
      size_bytes: null, unit: "unknown", manifest: {}, qualification: {}, error_message: null,
      can_cancel: true, next_action: "A correção está na fila.", created_at: "2026-08-02T00:00:00Z", updated_at: "2026-08-02T00:00:00Z",
    });
    render(React.createElement(ReconstructionPanel, { captureSessionId: 8, setError: vi.fn() }));

    fireEvent.change(await screen.findByLabelText("Lado medido"), { target: { value: "z" } });
    fireEvent.change(screen.getByLabelText("Medida real em milímetros"), { target: { value: "60" } });
    fireEvent.click(screen.getByRole("button", { name: "Aplicar medida" }));

    await waitFor(() => expect(create).toHaveBeenCalledWith(11, {
      operation: "scale",
      parameters: { output_format: "obj", scale_factor: 2, known_axis: "z", known_dimension_mm: 60 },
    }));
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
    vi.spyOn(meshRevisionApi, "listReviews").mockResolvedValue([]);
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

  it("exige comparação humana antes de adicionar o STL ao projeto", async () => {
    const completed: ReconstructionJob = {
      ...queued, status: "succeeded", stage: "ready", progress_percent: 100, can_cancel: false,
      artifacts: [{ id: 91, artifact_type: "raw_mesh", file_format: "obj", sha256: "abc", size_bytes: 100, unit: "mm", observed_ratio: 1, inferred_ratio: 0, provenance: {} }],
      qualification: { id: 92, reconstruction_artifact_id: 91, analyzer_version: "deterministic-v1", status: "not_qualified", report: { dimensions: { x: 20, y: 20, z: 20 }, checks: {} }, created_at: "2026-08-02T00:00:00Z" },
    };
    const revision = {
      id: 17, reconstruction_job_id: 11, source_artifact_id: 91, parent_revision_id: 16,
      operation: "convert" as const, parameters: { output_format: "stl" }, status: "succeeded" as const,
      output_format: "stl", sha256: "final", size_bytes: 200, unit: "mm", manifest: {},
      qualification: { dimensions: { x: 20, y: 20, z: 20 }, checks: { watertight: true, non_manifold_edge_count: 0, winding_conflict_count: 0, degenerate_triangle_count: 0, component_count: 1, self_intersection_count: 0 } },
      error_message: null, can_cancel: false, next_action: "A nova versão está pronta para revisão.",
      created_at: "2026-08-02T00:00:00Z", updated_at: "2026-08-02T00:00:00Z",
    };
    vi.spyOn(photoReconstructionApi, "list").mockResolvedValue([completed]);
    vi.spyOn(meshRevisionApi, "list").mockResolvedValue([revision]);
    vi.spyOn(meshRevisionApi, "listReviews").mockResolvedValue([]);
    const review = vi.spyOn(meshRevisionApi, "review").mockResolvedValue({
      id: 3, revision_id: 17, reconstruction_job_id: 11, decision: "approved_for_slicing",
      intended_use: "decorative", known_axis: "x", known_dimension_mm: 20, model_dimension_mm: 20,
      deviation_percent: 0, revision_sha256: "final", review_manifest: {}, qualification: {},
      project_file_id: 44, note: "", created_at: "2026-08-02T00:00:00Z",
    });
    const onModelApproved = vi.fn().mockResolvedValue(undefined);
    render(React.createElement(ReconstructionPanel, { captureSessionId: 8, setError: vi.fn(), onModelApproved }));

    expect(await screen.findByText("Revisão final antes do fatiamento")).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Medida do objeto em milímetros"), { target: { value: "20" } });
    fireEvent.click(screen.getByLabelText(/Comparei a forma/i));
    fireEvent.click(screen.getByLabelText(/não garante encaixe/i));
    fireEvent.click(screen.getByRole("button", { name: "Aprovar para fatiamento" }));

    await waitFor(() => expect(review).toHaveBeenCalledWith(11, 17, expect.objectContaining({
      decision: "approve", intended_use: "decorative", known_axis: "x", known_dimension_mm: 20,
      shape_reviewed: true, limitations_accepted: true,
    })));
    await waitFor(() => expect(onModelApproved).toHaveBeenCalledOnce());
    expect(await screen.findByText("Modelo adicionado ao projeto")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Continuar para o fatiamento" })).toBeTruthy();
  });
});
