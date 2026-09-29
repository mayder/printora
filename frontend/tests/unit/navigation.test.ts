import { describe, expect, it } from "vitest";

import { canShowSection } from "../../src/app/navigation";


describe("navigation access", () => {
  it("shows the design system only to the platform administrator", () => {
    expect(canShowSection("design-system", "none", false)).toBe(false);
    expect(canShowSection("design-system", "none", true)).toBe(true);
    expect(canShowSection("overview", "none", false)).toBe(true);
  });
});
