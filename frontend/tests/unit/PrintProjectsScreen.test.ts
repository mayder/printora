import React from "react";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PrintProjectsScreen } from "../../src/screens/PrintProjectsScreen";
import { printProjectsApi } from "../../src/services/printProjectsApi";
import { slicingApi } from "../../src/services/slicingApi";
import type { AuthUser } from "../../src/types/auth";
import type { PrintProjectContract, PrintProjectSummary } from "../../src/types/printProjects";

const user: AuthUser = {
  id: 7,
  email: "maker@example.com",
  display_name: "Maker",
  social_links: {},
  timezone: "America/Sao_Paulo",
  mfa_enabled: false,
  is_active: true,
  platform_admin: false,
  created_at: "2026-08-04T00:00:00Z",
  organizations: [],
};

const contract = {
  root_entity: "Projeto de impressão",
  relations: [],
  visibility_values: [],
  publication_values: [],
  commercial_class_values: [],
  file_kinds: [],
  file_roles: [],
  immutable_snapshot_required_for: [],
  community_ownership_rule: "Comunidades compartilham projetos.",
  external_link_rule: "Links precisam ser importados.",
  public_privacy_rule: "Dados privados não são publicados.",
  legacy_surfaces: [],
} satisfies PrintProjectContract;

const project = {
  id: 11,
  slug: "teste-objeto-3d",
  title: "Teste objeto 3D",
  description: "",
  visibility: "private",
  lifecycle_status: "active",
  publication_status: "draft",
  commercial_class: "free",
  license: "cc-by",
  original_author_name: "",
  source_url: null,
  price_cents: 0,
  currency: "BRL",
  commercial_terms: "",
  promotion_disclosure: "",
  primary_file: null,
  file_count: 0,
  printable_file_count: 0,
  community_shares: [],
  tags: [],
  hosted_in_printora: false,
  external_reference_only: false,
  can_slice: false,
  created_at: "2026-08-04T00:00:00Z",
  updated_at: "2026-08-04T00:00:00Z",
} satisfies PrintProjectSummary;

describe("PrintProjectsScreen", () => {
  beforeEach(() => {
    vi.spyOn(printProjectsApi, "contract").mockResolvedValue(contract);
    vi.spyOn(printProjectsApi, "explore").mockResolvedValue([]);
    vi.spyOn(printProjectsApi, "myProjects").mockResolvedValue([project]);
    vi.spyOn(printProjectsApi, "storage").mockRejectedValue(new Error("Internal Server Error"));
    vi.spyOn(slicingApi, "profileBundles").mockResolvedValue([]);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it("keeps personal projects visible when the storage summary fails", async () => {
    const setError = vi.fn();
    render(React.createElement(PrintProjectsScreen, { authUser: user, setError }));

    fireEvent.click(await screen.findByRole("button", { name: "Meus projetos" }));

    expect(await screen.findByText("Teste objeto 3D")).toBeTruthy();
    expect(screen.getByText("Não foi possível carregar o armazenamento agora. Seus projetos continuam disponíveis.")).toBeTruthy();
    expect(setError).not.toHaveBeenCalledWith("Internal Server Error");
  });

  it("opens project registration in the standard modal without leaving the list", async () => {
    render(React.createElement(PrintProjectsScreen, { authUser: user, setError: vi.fn() }));

    fireEvent.click(await screen.findByRole("button", { name: "Meus projetos" }));
    fireEvent.click(await screen.findByRole("button", { name: "Novo projeto" }));

    expect(await screen.findByRole("dialog", { name: "Cadastrar projeto" })).toBeTruthy();
    expect(screen.getByText("Teste objeto 3D")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Fechar" }));
    expect(screen.queryByRole("dialog", { name: "Cadastrar projeto" })).toBeNull();
    expect(screen.getByRole("heading", { name: "Meus projetos", exact: true })).toBeTruthy();
  });
});
