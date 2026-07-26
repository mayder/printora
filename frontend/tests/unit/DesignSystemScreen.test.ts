import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DesignSystemScreen } from "../../src/screens/DesignSystemScreen";
import { designSystemApi } from "../../src/services/designSystemApi";
import type { DesignSystemCatalog } from "../../src/types/designSystem";


const catalog: DesignSystemCatalog = {
  contract_version: "1.0.0",
  compatible_with: ["1.x"],
  permissions: { can_view: true, can_customize_local: true, can_publish_global: false },
  capabilities: Array.from({ length: 8 }, (_, index) => {
    const number = index + 1;
    const slug = `capacidade-${number}`;
    return {
      capability_id: `CAP-18-${String(number).padStart(2, "0")}`,
      com_ids: Array.from({ length: 7 }, (_unused, offset) => `COM-${String(953 + index * 7 + offset).padStart(4, "0")}`),
      screen_id: `SCR-${String(137 + index).padStart(4, "0")}`,
      slug,
      title: `Capacidade visual ${number}`,
      summary: `Resumo verificável da capacidade ${number}.`,
      route: `/community/design_system/${slug}`,
      tokens: [],
      supported_states: ["loading", "empty", "error", "success", "partial", "offline", "forbidden", "conflict"],
    };
  }),
};

describe("DesignSystemScreen", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.history.replaceState(null, "", "/?section=design-system");
    vi.spyOn(designSystemApi, "catalog").mockResolvedValue(catalog);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("separates list, detail and editor while preserving a local draft", async () => {
    render(React.createElement(DesignSystemScreen));

    expect(await screen.findByText("8 de 8 famílias")).toBeTruthy();
    fireEvent.click(screen.getAllByRole("button", { name: /Detalhe/ })[0]);
    expect(await screen.findByText("Evidências atribuídas")).toBeTruthy();
    expect(window.location.pathname).toBe("/community/design_system/capacidade-1/detail");

    fireEvent.click(screen.getByRole("button", { name: /Abrir editor/ }));
    fireEvent.change(screen.getByLabelText("Nome da referência"), { target: { value: "Fluxo de oficina" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar rascunho" }));

    await waitFor(() => expect(screen.getByRole("button", { name: /Rascunho salvo/ })).toBeTruthy());
    expect(window.location.pathname).toBe("/community/design_system/capacidade-1/edit");
    expect(window.localStorage.getItem("printora.design-system.lab.v1")).toContain("Fluxo de oficina");
  });

  it("filters the catalog and exposes an actionable empty state", async () => {
    render(React.createElement(DesignSystemScreen));
    await screen.findByText("8 de 8 famílias");

    fireEvent.change(screen.getByPlaceholderText("Buscar por nome ou capacidade"), { target: { value: "inexistente" } });
    expect(screen.getByText("Nenhum item encontrado")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Limpar filtros" }));
    expect(screen.getByText("8 de 8 famílias")).toBeTruthy();
  });
});
