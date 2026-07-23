import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import { ensureUser, loginInBrowser, syntheticEmail } from "./helpers";

test("login, tema, navegação por teclado e logout", async ({
  page,
  request,
}, testInfo) => {
  const email = syntheticEmail(testInfo, "owner");
  await ensureUser(request, email, "Synthetic Owner");
  await loginInBrowser(page, email);

  const themeButton = page.getByRole("button", { name: "Usar tema claro" });
  if (await themeButton.isVisible()) {
    await themeButton.focus();
    await page.keyboard.press("Enter");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "light");
  }

  await page.locator(".account-menu-button").click();
  await page.getByRole("menuitem", { name: "Sair" }).click();
  await expect(page.getByRole("heading", { name: "Entrar no Printora" })).toBeVisible();
});

test("duas organizações permanecem isoladas ponta a ponta", async ({
  page,
  request,
}, testInfo) => {
  const ownerEmail = syntheticEmail(testInfo, "tenant-a");
  const outsiderEmail = syntheticEmail(testInfo, "tenant-b");
  const owner = await ensureUser(request, ownerEmail, "Tenant A");
  const outsider = await ensureUser(request, outsiderEmail, "Tenant B");
  const organizationName =
    `Organization ${testInfo.project.name} repeat ${testInfo.repeatEachIndex}`;

  const created = await request.post("/api/auth/organizations", {
    headers: { Authorization: `Bearer ${owner.access_token}` },
    data: { name: organizationName },
  });
  expect(created.ok()).toBe(true);
  const organization = await created.json();

  const denied = await request.get(
    `/api/auth/organizations/${organization.id}`,
    { headers: { Authorization: `Bearer ${outsider.access_token}` } },
  );
  expect(denied.status()).toBe(403);

  await loginInBrowser(page, ownerEmail);
  await page.locator(".account-menu-button").click();
  await page.getByRole("menuitem", { name: "Organizações" }).click();
  await expect(page.getByText(organizationName, { exact: true })).toBeVisible();
});

test("rotas privilegiadas negam usuário comum", async ({ request }, testInfo) => {
  const user = await ensureUser(
    request,
    syntheticEmail(testInfo, "common"),
    "Common User",
  );
  const headers = { Authorization: `Bearer ${user.access_token}` };

  const finance = await request.get("/api/admin/finance/readiness", { headers });
  expect(finance.status()).toBe(403);
  const manufacturing = await request.get("/api/admin/manufacturing/overview", {
    headers,
  });
  expect(manufacturing.status()).toBe(403);
  const anonymousAgent = await request.get("/api/agents");
  expect([401, 404, 405]).toContain(anonymousAgent.status());
});

test("rotas P0 não possuem violações críticas ou sérias de acessibilidade", async ({
  page,
  request,
}, testInfo) => {
  await page.goto("/");
  const anonymous = await new AxeBuilder({ page }).analyze();
  expect(
    anonymous.violations.filter((violation) =>
      ["critical", "serious"].includes(violation.impact ?? ""),
    ),
  ).toEqual([]);

  const email = syntheticEmail(testInfo, "a11y");
  await ensureUser(request, email, "Accessible User");
  await loginInBrowser(page, email);
  const authenticated = await new AxeBuilder({ page }).analyze();
  expect(
    authenticated.violations.filter((violation) =>
      ["critical", "serious"].includes(violation.impact ?? ""),
    ),
  ).toEqual([]);
});
