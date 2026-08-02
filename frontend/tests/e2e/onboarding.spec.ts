import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { ensureUser, loginInBrowser, syntheticEmail } from "./helpers";

test("primeiros passos orienta instalação vazia e preserva retomada em falha", async ({ page, request }, testInfo) => {
  const email = syntheticEmail(testInfo, "onboarding");
  await ensureUser(request, email, "Onboarding User");
  await loginInBrowser(page, email);

  await page.goto("/?section=onboarding");
  await expect(page.getByRole("heading", { name: "Prepare sua primeira impressão com segurança" })).toBeVisible();
  await expect(page.getByText("1 de 5 etapas concluídas", { exact: true })).toBeVisible();
  await expect(page.getByText("PKG-", { exact: false })).toHaveCount(0);

  await page.getByRole("button", { name: /Etapa 2 Conectar a impressora/ }).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("button", { name: "Cadastrar minha impressora" })).toBeVisible();

  const accessibility = await new AxeBuilder({ page }).analyze();
  expect(accessibility.violations.filter((violation) => ["critical", "serious"].includes(violation.impact ?? ""))).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1)).toBe(true);

  await page.evaluate(() => window.localStorage.setItem("printora.onboarding.resume.v1", JSON.stringify({
    step: "project",
    updatedAt: "2026-08-02T12:00:00.000Z",
  })));
  await page.route("**/api/print-projects/me", (route) => route.abort("timedout"));
  await page.route("**/api/slicing/jobs", (route) => route.abort("timedout"));
  await page.route("**/api/slicing/preflights", (route) => route.abort("timedout"));
  await page.reload();

  await expect(page.getByText("Não foi possível confirmar todas as etapas agora", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: /Etapa 4 Escolher o primeiro projeto/ })).toHaveAttribute("aria-current", "step");
  expect(await page.evaluate(() => JSON.parse(window.localStorage.getItem("printora.onboarding.resume.v1") ?? "{}").step)).toBe("project");
});
