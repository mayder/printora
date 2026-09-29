import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SlicingProfilesPanel } from "../../src/screens/projects/SlicingProfilesPanel";

const profileBundles = vi.fn();
const compareProfileRevisions = vi.fn();

vi.mock("../../src/services/slicingApi", () => ({
  slicingApi: {
    profileBundles: () => profileBundles(),
    compareProfileRevisions: (...args: unknown[]) => compareProfileRevisions(...args),
    importProfileBundle: vi.fn(),
    exportProfileRevision: vi.fn(),
  },
}));

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("SlicingProfilesPanel", () => {
  it("explica o perfil em linguagem simples e compara versões", async () => {
    profileBundles.mockResolvedValue([{
      id: 4,
      title: "Voron com PLA",
      engine: "orcaslicer",
      engine_version: "2.3.1",
      schema_version: "1",
      source_format: "orcaslicer_native_bundle",
      compatibility: {},
      current_revision_id: 12,
      current_sha256: "abcdef1234567890",
      revisions: [
        { id: 12, revision_number: 2, sha256: "abcdef1234567890" },
        { id: 11, revision_number: 1, sha256: "1234567890abcdef" },
      ],
    }]);
    compareProfileRevisions.mockResolvedValue({
      from_revision_id: 11,
      to_revision_id: 12,
      added: { "presets.process.wall_loops": "3" },
      changed: { "presets.process.speed": { before: "180", after: "220" } },
      removed: {},
      loss_report: [],
    });

    render(React.createElement(SlicingProfilesPanel, { setError: vi.fn() }));

    expect(screen.getByRole("heading", { name: "Perfis de fatiamento" })).toBeTruthy();
    expect(screen.getByText(/trabalhos antigos continuam reproduzíveis/)).toBeTruthy();
    expect(await screen.findByText("Voron com PLA")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Comparar versões/ }));
    await waitFor(() => expect(screen.getByRole("status").textContent).toContain("1 adicionado(s), 1 alterado(s) e 0 removido(s)"));
    expect(compareProfileRevisions).toHaveBeenCalledWith(11, 12);
  });
});
