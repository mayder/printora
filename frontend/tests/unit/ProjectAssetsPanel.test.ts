import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ProjectAssetsSummary } from "../../src/screens/projects/ProjectAssetsPanel";
import type { PrintProjectDetail } from "../../src/types/printProjects";


const project = {
  id: 7,
  slug: "suporte",
  title: "Suporte",
  files: [
    {
      id: 11,
      file_kind: "stl",
      file_role: "primary",
      file_name: "suporte.stl",
      validation_status: "validated",
      piece_name: "Corpo principal",
      variant_name: "Grande",
      assembly_name: "Conjunto",
      inspection_status: "ready",
      inspection: {
        dimensions_mm: { x: 20, y: 30, z: 40 },
        triangle_count: 120,
        warnings: ["Revise os suportes no fatiador."],
      },
    },
  ],
  current_manifest: { schema: "printora.project-manifest/v1" },
  current_manifest_sha256: "1234567890abcdef",
} as unknown as PrintProjectDetail;


afterEach(cleanup);

describe("ProjectAssetsSummary", () => {
  it("explica medidas e alertas em texto sem depender da prévia visual", () => {
    render(React.createElement(ProjectAssetsSummary, { project, setError: vi.fn(), canDownload: false }));

    expect(screen.getByRole("heading", { name: "Peças e inspeção" })).toBeTruthy();
    expect(screen.getByText("20 × 30 × 40 mm")).toBeTruthy();
    expect(screen.getByText("120 triângulo(s)")).toBeTruthy();
    expect(screen.getByText("Revise os suportes no fatiador.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /Baixar pacote/ })).toBeNull();
  });

  it("oferece manifesto e pacote para usuário autenticado", () => {
    render(React.createElement(ProjectAssetsSummary, { project, setError: vi.fn(), canDownload: true }));

    expect(screen.getByRole("button", { name: /Manifesto/ })).toBeTruthy();
    expect(screen.getByRole("button", { name: /Baixar pacote/ })).toBeTruthy();
    expect(screen.getByText(/Identificador desta versão: 1234567890ab/)).toBeTruthy();
  });

  it("mantém a tela utilizável durante compatibilidade com resposta sem inspeção", () => {
    const compatibleProject = {
      ...project,
      files: [{ ...project.files[0], inspection: undefined }],
    } as unknown as PrintProjectDetail;

    render(React.createElement(ProjectAssetsSummary, { project: compatibleProject, setError: vi.fn(), canDownload: false }));

    expect(screen.getByText("Medidas ainda não disponíveis.")).toBeTruthy();
    expect(screen.getByText("Corpo principal")).toBeTruthy();
  });
});
