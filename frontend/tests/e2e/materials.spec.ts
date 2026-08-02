import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { bearer, ensureUser, loginInBrowser, syntheticEmail } from "./helpers";

test("materiais orienta cadastro, conferência e consumo sem exigir conhecimento técnico", async ({ page, request }, testInfo) => {
  const email = syntheticEmail(testInfo, "materials");
  const owner = await ensureUser(request, email, "Materials User");
  const headers = bearer(owner.access_token);
  const suffix = `${testInfo.project.name}-${testInfo.repeatEachIndex}`;

  const printerResponse = await request.post("/api/printers", {
    headers,
    data: {
      name: `Voron materiais ${suffix}`,
      moonraker_url: "http://materials-e2e.invalid:7125",
      host_audit_mode: "disabled",
    },
  });
  expect(printerResponse.ok()).toBe(true);

  const spoolResponse = await request.post("/api/materials/spools", {
    headers,
    data: {
      name: `PLA branco ${suffix}`,
      material_type: "PLA",
      brand: "Printalot",
      color_name: "Branco",
      color_hex: "#FFFFFF",
      initial_weight_g: 1000,
      remaining_weight_g: 1000,
      location: "Caixa seca",
      storage_state: "dry",
    },
  });
  expect(spoolResponse.ok()).toBe(true);
  const spool = await spoolResponse.json();

  await loginInBrowser(page, email);
  await page.goto("/?section=materials");
  await expect(page.getByRole("heading", { name: "Meus spools" })).toBeVisible();
  await expect(page.getByText(`PLA branco ${suffix}`, { exact: true })).toBeVisible();
  await expect(page.getByText("PKG-", { exact: false })).toHaveCount(0);

  await page.getByText(`PLA branco ${suffix}`, { exact: true }).click();
  await expect(page.getByRole("heading", { name: `PLA branco ${suffix}` })).toBeVisible();
  await expect(page.getByText("O cadastro não possui alertas conhecidos.")).toBeVisible();

  await page.getByLabel("Peso (g) *").fill("50");
  await page.getByLabel("Tipo de registro").selectOption("confirmed");
  await page.getByRole("button", { name: "Registrar", exact: true }).click();
  await expect(page.getByText("950 g", { exact: true })).toBeVisible();

  const persisted = await request.get(`/api/materials/spools/${spool.id}`, { headers });
  expect(persisted.ok()).toBe(true);
  expect((await persisted.json()).remaining_weight_g).toBe(950);

  const accessibility = await new AxeBuilder({ page }).analyze();
  expect(accessibility.violations.filter((violation) => ["critical", "serious"].includes(violation.impact ?? ""))).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1)).toBe(true);
});
