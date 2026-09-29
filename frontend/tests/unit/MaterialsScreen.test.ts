import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MaterialsScreen } from "../../src/screens/materials/MaterialsScreen";
import { materialsApi } from "../../src/services/materialsApi";
import { socialApi } from "../../src/services/socialApi";
import type { MaterialSpool, PrinterRecord } from "../../src/types";

const printer = { id: 7, name: "Voron da oficina" } as PrinterRecord;
const localSpool: MaterialSpool = {
  id: 31,
  owner_user_id: 4,
  material_profile_id: null,
  source: "local",
  external_id: null,
  name: "PLA branco",
  material_type: "PLA",
  brand: "Printalot",
  color_name: "Branco",
  color_hex: "#FFFFFF",
  lot_code: "",
  initial_weight_g: 1000,
  remaining_weight_g: 840,
  location: "Caixa seca",
  storage_state: "dry",
  opened_at: null,
  dried_at: null,
  expires_at: null,
  revision: 1,
  status: "active",
  last_synced_at: null,
  created_at: "2026-08-02T12:00:00Z",
  updated_at: "2026-08-02T12:00:00Z",
  alerts: [],
};

describe("MaterialsScreen", () => {
  beforeEach(() => {
    vi.spyOn(materialsApi, "spools").mockResolvedValue([]);
    vi.spyOn(socialApi, "myMaterialProfiles").mockResolvedValue([]);
    vi.spyOn(materialsApi, "consumptions").mockResolvedValue([]);
    vi.spyOn(materialsApi, "quality").mockResolvedValue([]);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("guides a novice from the empty state to the separate creation form", async () => {
    const create = vi.spyOn(materialsApi, "createSpool").mockResolvedValue(localSpool);
    vi.spyOn(materialsApi, "spool").mockResolvedValue(localSpool);
    const showToast = vi.fn();
    render(React.createElement(MaterialsScreen, { printers: [printer], showToast, confirmAction: vi.fn() }));

    expect(await screen.findByText("Nenhum spool cadastrado")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Adicionar meu primeiro spool" }));
    expect(screen.getByRole("heading", { name: "Adicionar spool" })).toBeTruthy();

    fireEvent.change(screen.getByLabelText("Nome do spool *"), { target: { value: "PLA branco" } });
    fireEvent.change(screen.getByLabelText("Tipo do material *"), { target: { value: "PLA" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar spool" }));

    await waitFor(() => expect(create).toHaveBeenCalledWith(expect.objectContaining({ name: "PLA branco", material_type: "PLA" })));
    expect(await screen.findByRole("heading", { name: "PLA branco" })).toBeTruthy();
    expect(document.body.textContent).not.toContain("PKG-");
  });

  it("keeps local materials available when Spoolman is unavailable", async () => {
    vi.mocked(materialsApi.spools).mockResolvedValue([localSpool]);
    vi.spyOn(materialsApi, "syncSpoolman").mockResolvedValue({
      printer_id: printer.id,
      status: "unavailable",
      imported: 0,
      updated: 0,
      total: 0,
      detail: "Spoolman não respondeu pelo agente.",
    });
    const showToast = vi.fn();
    render(React.createElement(MaterialsScreen, { printers: [printer], showToast, confirmAction: vi.fn() }));

    expect(await screen.findByText("PLA branco")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Sincronizar" }));

    await waitFor(() => expect(showToast).toHaveBeenCalledWith(expect.objectContaining({
      tone: "warning",
      title: "Spoolman indisponível",
      detail: expect.stringContaining("spools locais continuam disponíveis"),
    })));
    expect(screen.getByText("PLA branco")).toBeTruthy();
  });
});
