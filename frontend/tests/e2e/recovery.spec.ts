import { expect, test } from "@playwright/test";
import { ensureUser, syntheticEmail } from "./helpers";

test("login apresenta 429 sanitizado e permite nova tentativa", async ({
  page,
  request,
}, testInfo) => {
  const email = syntheticEmail(testInfo, "rate-limit");
  await ensureUser(request, email, "Rate Limited User");
  let intercepted = false;
  await page.route("**/api/auth/login", async (route) => {
    if (!intercepted) {
      intercepted = true;
      await route.fulfill({
        status: 429,
        contentType: "application/json",
        body: JSON.stringify({ detail: "limite sintético atingido" }),
      });
      return;
    }
    await route.continue();
  });

  await page.goto("/");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Senha").fill("synthetic-correct-horse-97");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("limite sintético atingido")).toBeVisible();
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Visão geral", exact: true }),
  ).toBeVisible();
});

test("falha offline mantém a tela recuperável", async ({ page }, testInfo) => {
  await page.goto("/");
  await page.getByLabel("Email").fill(syntheticEmail(testInfo, "offline"));
  await page.getByLabel("Senha").fill("synthetic-correct-horse-97");
  await page.context().setOffline(true);
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Entrar no Printora" })).toBeVisible();
  await page.context().setOffline(false);
  await expect(page.getByRole("button", { name: "Entrar", exact: true })).toBeEnabled();
});
