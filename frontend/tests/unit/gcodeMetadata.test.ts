import { describe, expect, it } from "vitest";
import { formatGcodeSlicer, normalizeGcodeMaterial } from "../../src/utils/formatters/gcodeMetadata";

describe("metadados de G-code", () => {
  it("transforma listas técnicas de filamento em texto único para o usuário", () => {
    expect(normalizeGcodeMaterial('["PLA","PLA","PLA"]')).toBe("PLA");
    expect(normalizeGcodeMaterial("PLA;ABS;ABS")).toBe("PLA · ABS");
  });

  it("omite marcadores técnicos quando o slicer não foi identificado", () => {
    expect(formatGcodeSlicer("Unknown", "?")).toBe("-");
    expect(formatGcodeSlicer("OrcaSlicer", "?")).toBe("OrcaSlicer");
    expect(formatGcodeSlicer("OrcaSlicer", "2.4.2")).toBe("OrcaSlicer 2.4.2");
  });
});
