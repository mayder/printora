import React from "react";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AccessibilityScreen } from "../../src/screens/AccessibilityScreen";
import { accessibilityApi } from "../../src/services/accessibilityApi";
import type {
  AccessibilityCatalog,
  AccessibilityPreferences,
} from "../../src/types/accessibility";


const capabilities = Array.from({ length: 8 }, (_, index) => {
  const number = index + 1;
  const slug = `capacidade-${number}`;
  return {
    capability_id: `CAP-09-${String(number).padStart(2, "0")}`,
    com_ids: Array.from(
      { length: 7 },
      (_unused, offset) => `COM-${String(449 + index * 7 + offset).padStart(4, "0")}`,
    ),
    screen_id: `SCR-${String(65 + index).padStart(4, "0")}`,
    slug,
    title: `Capacidade acessível ${number}`,
    summary: `Resumo verificável da capacidade ${number}.`,
    route: `/community/accessibility/${slug}`,
    evidence: ["teclado", "leitor de tela", "zoom"],
    supported_states: ["loading", "empty", "error", "success", "partial", "offline", "forbidden", "conflict"],
  };
});
const catalog: AccessibilityCatalog = {
  contract_version: "1.0.0",
  compatible_with: ["1.x"],
  capabilities,
};

const preferences: AccessibilityPreferences = {
  contract_version: "1.0.0",
  compatible_with: ["1.x"],
  revision: 1,
  updated_at: "2026-07-26T12:00:00Z",
  theme: "system",
  text_scale_percent: 100,
  reduce_motion: false,
  screen_reader_announcements: true,
  keyboard_navigation: true,
  voice_navigation: false,
  captions: true,
  audio_descriptions: false,
  simple_language: false,
  low_cognitive_load: false,
  three_d_text_alternative: true,
  tactile_format: "svg",
};

describe("AccessibilityScreen", () => {
  beforeEach(() => {
    window.history.replaceState(null, "", "/?section=accessibility");
    vi.spyOn(accessibilityApi, "catalog").mockResolvedValue(catalog);
    vi.spyOn(accessibilityApi, "preferences").mockResolvedValue(preferences);
    vi.spyOn(accessibilityApi, "save").mockResolvedValue({
      ...preferences,
      revision: 2,
      theme: "high-contrast",
    });
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    document.documentElement.style.fontSize = "";
    delete document.documentElement.dataset.contrast;
  });

  it("separates list, detail and edit and synchronizes preferences", async () => {
    render(React.createElement(AccessibilityScreen));

    expect(await screen.findByText("Escolha como quer usar o Printora")).toBeTruthy();
    expect(screen.queryByText("CAP-09-01")).toBeNull();
    expect(screen.queryByText("SCR-0065")).toBeNull();
    expect(screen.queryByText("COM-0449")).toBeNull();
    fireEvent.click(screen.getByText("Conheça os recursos de acessibilidade"));
    fireEvent.click(screen.getAllByRole("button", { name: /Saiba mais sobre/ })[0]);
    expect(await screen.findByText("Como este recurso ajuda")).toBeTruthy();
    expect(window.location.pathname).toBe("/community/accessibility/capacidade-1/detail");

    fireEvent.click(screen.getByRole("button", { name: "Ajustar minhas preferências" }));
    fireEvent.change(screen.getByLabelText("Tema adaptativo"), { target: { value: "high-contrast" } });
    fireEvent.click(screen.getByRole("button", { name: "Salvar preferências" }));

    await waitFor(() => expect(accessibilityApi.save).toHaveBeenCalledWith(
      expect.objectContaining({ theme: "high-contrast" }),
      1,
    ));
    expect(await screen.findByText("Preferências sincronizadas.", { selector: ".a11y-live" })).toBeTruthy();
    expect(window.location.pathname).toBe("/community/accessibility/capacidade-1/edit");
  });

  it("shows personal preferences before optional explanatory resources", async () => {
    render(React.createElement(AccessibilityScreen));
    expect(await screen.findByRole("button", { name: "Salvar preferências" })).toBeTruthy();
    expect(screen.getByText("Conheça os recursos de acessibilidade")).toBeTruthy();
    expect(document.querySelector<HTMLDetailsElement>(".a11y-resources")?.open).toBe(false);
  });
});
