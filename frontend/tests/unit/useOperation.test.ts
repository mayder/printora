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

function operationStatus(printerId: number, printState: string): OperationStatusResponse {
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
    miscellaneous: {
      print_state: printState,
    },
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
});
