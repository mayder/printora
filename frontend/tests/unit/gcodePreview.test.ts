import { describe, expect, it } from "vitest";
import {
  buildLayerOffsets,
  previewTargetPosition,
  sliceGcodeTextForPreview,
} from "../../src/components/monitoring/gcodePreview";

describe("gcode preview", () => {
  it("maps progress, layers and terminal states", () => {
    const text = [
      ";LAYER:0",
      "G1 X0",
      "x".repeat(80),
      ";LAYER:1",
      "G1 X1",
      "x".repeat(80),
      ";LAYER:2",
      "G1 X2",
    ].join("\n");
    const offsets = buildLayerOffsets(text);

    expect(offsets.length).toBeGreaterThanOrEqual(4);
    expect(previewTargetPosition(text.length, offsets, "full")).toBe(text.length);
    expect(
      previewTargetPosition(text.length, offsets, "progress", null, null, "complete"),
    ).toBe(text.length);
    expect(
      previewTargetPosition(text.length, offsets, "progress", null, 600, "printing"),
    ).toBe(Math.min(text.length, 250));
    expect(previewTargetPosition(1000, [], "progress", null, null, "printing", 25)).toBe(
      250,
    );
    expect(
      previewTargetPosition(text.length, offsets, "until_layer", 1, null, "printing"),
    ).toBe(offsets[2]);
  });

  it("limits large previews at a complete line", () => {
    const large = "G1 X1 Y1 E0.1\n".repeat(720000);
    const partial = sliceGcodeTextForPreview(large, 1024);
    expect(partial.partial).toBe(true);
    expect(partial.text.endsWith("\n")).toBe(true);

    const complete = sliceGcodeTextForPreview(large, Number.POSITIVE_INFINITY);
    expect(complete.partial).toBe(true);
    expect(sliceGcodeTextForPreview("", 0)).toEqual({
      text: "",
      sourceLimit: 0,
      sourceBytes: 0,
      partial: false,
    });
    expect(sliceGcodeTextForPreview("G1 X1", 100)).toMatchObject({ partial: false });
  });
});
