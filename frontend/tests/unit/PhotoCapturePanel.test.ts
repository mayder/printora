import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { PhotoCapturePanel } from "../../src/screens/projects/PhotoCapturePanel";
import { photoCaptureApi } from "../../src/services/photoCaptureApi";
import type { PhotoCaptureSession } from "../../src/types/photoCapture";


const session: PhotoCaptureSession = {
  id: 8,
  project_id: 7,
  status: "draft",
  target_photo_count: 24,
  scale_method: "none",
  scale_value_mm: null,
  scale_uncertainty_mm: null,
  scale_confirmed: false,
  consent_confirmed: true,
  expires_at: "2026-09-01T00:00:00Z",
  created_at: "2026-08-02T00:00:00Z",
  updated_at: "2026-08-02T00:00:00Z",
  photos: [],
  accepted_photo_count: 0,
  covered_photo_count: 0,
  accepted_by_height_band: { low: 0, middle: 0, high: 0 },
  required_by_height_band: { low: 8, middle: 8, high: 8 },
  missing_height_bands: ["low", "middle", "high"],
  next_actions: ["Na altura do objeto: faça mais 8 foto(s) durante a volta."],
  can_complete: false,
};


afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("PhotoCapturePanel", () => {
  it("explica a preparação antes de iniciar e exige consentimento", async () => {
    vi.spyOn(photoCaptureApi, "list").mockResolvedValue([]);
    const create = vi.spyOn(photoCaptureApi, "create").mockResolvedValue(session);
    render(React.createElement(PhotoCapturePanel, { projectId: 7, setError: vi.fn() }));

    expect(await screen.findByRole("heading", { name: "Digitalizar este objeto" })).toBeTruthy();
    expect(screen.getByText("Você fará exatamente 24 fotos")).toBeTruthy();
    const start = screen.getByRole("button", { name: "Começar pelas fotos" });
    expect(start).toHaveProperty("disabled", true);
    fireEvent.click(screen.getByRole("checkbox"));
    fireEvent.click(start);

    await waitFor(() => expect(create).toHaveBeenCalledWith(7));
    expect(await screen.findByText("0 de 24 posições cobertas. 0 fotos aprovadas.")).toBeTruthy();
    expect(document.body.textContent).not.toContain("PKG-");
  });

  it("retoma uma captura existente sem pedir conhecimento técnico", async () => {
    vi.spyOn(photoCaptureApi, "list").mockResolvedValue([session]);
    render(React.createElement(PhotoCapturePanel, { projectId: 7, setError: vi.fn() }));

    expect(await screen.findByRole("heading", { name: "Fotografe uma volta por vez" })).toBeTruthy();
    expect(screen.getByText("Na altura do objeto: faça mais 8 foto(s) durante a volta.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Na altura do objeto 0 de 8" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.getByText("Mantenha a câmera na metade da altura do objeto e aponte para o centro.")).toBeTruthy();
    expect(screen.getByText("Frente")).toBeTruthy();
    expect(screen.getAllByText("Adicionar")).toHaveLength(8);
    expect(screen.queryByText("Posição 9")).toBeNull();
  });
});
