import { createElement } from "react";
import { cleanup, render, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { PrintoraScreenProps } from "../../src/hooks/usePrintoraApp";

const { gcodeFilesMock } = vi.hoisted(() => ({
  gcodeFilesMock: vi.fn(),
}));

vi.mock("../../src/services/operationApi", () => ({
  operationApi: {
    gcodeFiles: gcodeFilesMock,
  },
}));

import { GcodeFilesScreen } from "../../src/screens/GcodeFilesScreen";

function props(showToast: PrintoraScreenProps["showToast"]): PrintoraScreenProps {
  return {
    confirmAction: vi.fn(),
    selectedPrinter: { id: 1, name: "Voron" },
    selectedPrinterId: 1,
    showToast,
  } as unknown as PrintoraScreenProps;
}

describe("GcodeFilesScreen", () => {
  afterEach(() => {
    cleanup();
  });

  beforeEach(() => {
    gcodeFilesMock.mockReset();
    gcodeFilesMock.mockResolvedValue({
      printer_id: 1,
      safe_mode: "read_only",
      data_state: "live",
      root: "gcodes",
      summary: "Arquivos disponíveis",
      files: [],
      directories: [],
      storage: null,
      limit: 50,
      offset: 0,
      total: 0,
      has_more: false,
    });
  });

  it("não recarrega a listagem quando apenas o callback de toast muda", async () => {
    const view = render(createElement(GcodeFilesScreen, props(vi.fn())));

    await waitFor(() => expect(gcodeFilesMock).toHaveBeenCalledTimes(1));
    view.rerender(createElement(GcodeFilesScreen, props(vi.fn())));

    await waitFor(() => expect(gcodeFilesMock).toHaveBeenCalledTimes(1));
  });
});
