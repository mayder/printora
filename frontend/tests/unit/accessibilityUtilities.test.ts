import { describe, expect, it, vi } from "vitest";
import { applyAccessibilityPreferences } from "../../src/services/accessibilityDocument";
import { buildTactileArtifact } from "../../src/services/accessibilityTactile";
import { defaultAccessibilityValues } from "../../src/types/accessibility";


describe("accessibility utilities", () => {
  it("applies visual and semantic preferences without storage", () => {
    const root = document.createElement("div");
    applyAccessibilityPreferences({
      ...defaultAccessibilityValues(),
      theme: "high-contrast",
      text_scale_percent: 150,
      reduce_motion: true,
      simple_language: true,
    }, root);

    expect(root.style.fontSize).toBe("150%");
    expect(root.dataset.contrast).toBe("high");
    expect(root.dataset.reduceMotion).toBe("true");
    expect(root.dataset.simpleLanguage).toBe("true");
  });

  it("builds bounded SVG and BRF artifacts with textual alternatives", () => {
    const svg = buildTactileArtifact("svg");
    const brf = buildTactileArtifact("brf");

    expect(svg.content).toContain("<title>Referência tátil Printora</title>");
    expect(svg.content).toContain("<desc>");
    expect(svg.content.length).toBeLessThan(32 * 1024);
    expect(svg.fileName).toMatch(/\.svg$/);
    expect(brf.content).toContain("Forma retangular");
    expect(brf.fileName).toMatch(/\.brf$/);
    expect(vi.isMockFunction(buildTactileArtifact)).toBe(false);
  });
});
