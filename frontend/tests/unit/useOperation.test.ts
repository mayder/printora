import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { OperationStatusResponse } from "../../src/types";

const { statusMock } = vi.hoisted(() => ({
  statusMock: vi.fn(),
}));

vi.mock("../../src/services/operationApi", () => ({
  operationApi: {
    status: statusMock,
  },
}));

import { useOperation } from "../../src/hooks/domains/useOperation";

type OperationStatusFixtureOverrides = Partial<Omit<OperationStatusResponse, "miscellaneous">> & {
  miscellaneous?: Record<string, unknown>;
};

function operationStatus(printerId: number, printState: string, overrides: OperationStatusFixtureOverrides = {}): OperationStatusResponse {
  const miscellaneous = {
    print_state: printState,
    ...(overrides.miscellaneous ?? {}),
  };
  return {
    printer_id: printerId,
    connected: true,
    data_state: "live",
    agent: {
      ready: true,
      version: "0.1.34",
      expected_version: "0.1.34",
      diagnostic: null,
    },
    system_loads: [],
    temperatures: [],
    temperature_history: [],
    toolhead: {},
    extruder: {},
    ...overrides,
    miscellaneous,
  } as unknown as OperationStatusResponse;
}

function deferredResponse() {
  let resolve!: (response: Response) => void;
  const promise = new Promise<Response>((resolver) => {
    resolve = resolver;
  });
  return { promise, resolve };
}

function renderOperation() {
  return renderHook(() => useOperation({
    selectedPrinterId: 1,
    setActiveSection: vi.fn(),
    setError: vi.fn(),
    setLoading: vi.fn(),
  }));
}

describe("useOperation scoped status", () => {
  beforeEach(() => {
    statusMock.mockReset();
  });

  it("clears preserved data when the requested printer changes", async () => {
    statusMock.mockResolvedValueOnce(Response.json(operationStatus(1, "standby")));
    const hook = renderOperation();

    await act(async () => {
      await hook.result.current.loadOperationStatus(1);
    });
    expect(hook.result.current.operationStatus?.printer_id).toBe(1);

    const printerTwo = deferredResponse();
    statusMock.mockReturnValueOnce(printerTwo.promise);
    let request!: Promise<void>;
    act(() => {
      request = hook.result.current.loadOperationStatus(2, { preserveData: true });
    });

    expect(hook.result.current.operationStatus).toBeNull();

    await act(async () => {
      printerTwo.resolve(Response.json(operationStatus(2, "printing")));
      await request;
    });
    expect(hook.result.current.operationStatus?.printer_id).toBe(2);
  });

  it("ignores a late response from an older printer request", async () => {
    const printerOne = deferredResponse();
    const printerTwo = deferredResponse();
    statusMock
      .mockReturnValueOnce(printerOne.promise)
      .mockReturnValueOnce(printerTwo.promise);
    const hook = renderOperation();

    let firstRequest!: Promise<void>;
    let secondRequest!: Promise<void>;
    act(() => {
      firstRequest = hook.result.current.loadOperationStatus(1);
      secondRequest = hook.result.current.loadOperationStatus(2);
    });
    await act(async () => {
      printerTwo.resolve(Response.json(operationStatus(2, "printing")));
      await secondRequest;
    });
    await act(async () => {
      printerOne.resolve(Response.json(operationStatus(1, "standby")));
      await firstRequest;
    });

    expect(hook.result.current.operationStatus?.printer_id).toBe(2);
    expect(hook.result.current.operationStatus?.miscellaneous.print_state).toBe("printing");
  });

  it("keeps active print data when a degraded idle snapshot arrives", async () => {
    statusMock
      .mockResolvedValueOnce(Response.json(operationStatus(1, "printing", {
        miscellaneous: {
          print_state: "printing",
          filename: "Deck Box.gcode",
          current_layer: 11,
          total_layers: 369,
          progress: 0.12,
          thumbnail: { data_uri: "data:image/png;base64,abc" },
        },
      })))
      .mockResolvedValueOnce(Response.json(operationStatus(1, "standby", {
        connected: false,
        data_state: "last_snapshot",
        miscellaneous: {
          print_state: "standby",
          filename: "",
          current_layer: null,
          total_layers: null,
          progress: null,
        },
      })));
    const hook = renderOperation();

    await act(async () => {
      await hook.result.current.loadOperationStatus(1);
    });
    await act(async () => {
      await hook.result.current.loadOperationStatus(1, { preserveData: true });
    });

    expect(hook.result.current.operationStatus?.miscellaneous.print_state).toBe("printing");
    expect(hook.result.current.operationStatus?.miscellaneous.filename).toBe("Deck Box.gcode");
    expect(hook.result.current.operationStatus?.miscellaneous.current_layer).toBe(11);
    expect(hook.result.current.operationStatus?.miscellaneous.progress).toBe(0.12);
  });
});
