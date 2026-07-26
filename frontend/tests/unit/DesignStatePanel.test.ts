import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DesignStatePanel } from "../../src/components/design-system/DesignStatePanel";
import type { DesignState } from "../../src/types/designSystem";


const STATES: Array<{ state: DesignState; title: string }> = [
  { state: "loading", title: "Carregando referência" },
  { state: "empty", title: "Nenhum item encontrado" },
  { state: "error", title: "Não foi possível carregar" },
  { state: "success", title: "Referência pronta" },
  { state: "partial", title: "Conteúdo parcial" },
  { state: "offline", title: "Você está offline" },
  { state: "forbidden", title: "Acesso não permitido" },
  { state: "conflict", title: "Rascunho alterado em outra aba" },
];

describe("DesignStatePanel", () => {
  it("expõe todos os estados por texto, sem depender apenas de cor", () => {
    render(
      React.createElement(
        React.Fragment,
        null,
        STATES.map(({ state }) =>
          React.createElement(DesignStatePanel, { key: state, state }),
        ),
      ),
    );

    for (const { title } of STATES) {
      expect(screen.getByText(title)).toBeTruthy();
    }
  });

  it("oferece recuperação explícita quando uma ação é informada", () => {
    const onAction = vi.fn();
    render(React.createElement(DesignStatePanel, { state: "error", onAction }));

    fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
    expect(onAction).toHaveBeenCalledTimes(1);
  });
});
