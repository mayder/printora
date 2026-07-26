import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import {
  bearer,
  ensureUser,
  loginInBrowser,
  PLATFORM_ADMIN_EMAIL,
  syntheticEmail,
} from "./helpers";


const TOKENS_ROUTE =
  "/community/design_system/design-system-documentado-com-tokens-semanticos";

async function findHorizontalOverflow(page: Page) {
  return page.getByTestId("design-system-screen").evaluate((root) => {
    const viewportWidth = document.documentElement.clientWidth;
    const documentOverflows = document.documentElement.scrollWidth > viewportWidth + 1;
    const elements = Array.from(root.querySelectorAll<HTMLElement>("*"))
      .filter((element) => {
        const rect = element.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return false;
        if (rect.left >= -1 && rect.right <= viewportWidth + 1) return false;
        let parent = element.parentElement;
        while (parent && parent !== root) {
          const overflowX = getComputedStyle(parent).overflowX;
          if (overflowX === "auto" || overflowX === "scroll") return false;
          parent = parent.parentElement;
        }
        return true;
      })
      .map((element) => element.className)
      .slice(0, 10);
    return { documentOverflows, elements };
  });
}

test("laboratório visual preserva contrato, acessibilidade e rascunho local", async ({
  page,
  request,
}, testInfo) => {
  const adminSession = await ensureUser(request, PLATFORM_ADMIN_EMAIL, "Platform Admin");
  const profile = await request.patch("/api/auth/me", {
    headers: bearer(adminSession.access_token),
    data: { display_name: "Design System User" },
  });
  expect(profile.ok()).toBe(true);
  await loginInBrowser(page, PLATFORM_ADMIN_EMAIL);

  await page.goto(TOKENS_ROUTE);
  await expect(
    page.getByRole("heading", { name: "Design system do Printora", exact: true }),
  ).toBeVisible();
  await expect(page.getByText("1 de 8 famílias", { exact: true })).toBeVisible();
  expect(await findHorizontalOverflow(page)).toEqual({
    documentOverflows: false,
    elements: [],
  });

  const accessibility = await new AxeBuilder({ page }).analyze();
  expect(
    accessibility.violations.filter((violation) =>
      ["critical", "serious"].includes(violation.impact ?? ""),
    ),
  ).toEqual([]);

  await expect(page.getByTestId("design-system-screen")).toHaveScreenshot(
    "design-system-list.png",
    { animations: "disabled" },
  );
  await page.getByPlaceholder("Buscar por nome ou capacidade").focus();
  await page.keyboard.press("Tab");
  const listButton = page.getByRole("button", { name: /Lista/ });
  await expect(listButton).toBeFocused();
  expect(
    await listButton.evaluate((element) => getComputedStyle(element).outlineStyle),
  ).not.toBe("none");

  const originalViewport = page.viewportSize();
  const viewports = testInfo.project.name === "desktop-chromium"
    ? [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]
    : [
        { width: 320, height: 568 },
        { width: 375, height: 667 },
        { width: 768, height: 375 },
      ];
  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    expect(
      await findHorizontalOverflow(page),
      `laboratório ultrapassou ${viewport.width}x${viewport.height}`,
    ).toEqual({ documentOverflows: false, elements: [] });
  }
  if (originalViewport) await page.setViewportSize(originalViewport);

  await page.getByRole("button", { name: /Detalhe/ }).click();
  await expect(page).toHaveURL(`${TOKENS_ROUTE}/detail`);
  await expect(page.getByText("Evidências atribuídas", { exact: true })).toBeVisible();
  await expect(page.getByText("COM-0953", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: /Abrir editor/ }).click();
  await expect(page).toHaveURL(`${TOKENS_ROUTE}/edit`);
  await page.goBack();
  await expect(page).toHaveURL(`${TOKENS_ROUTE}/detail`);
  await page.goBack();
  await expect(page).toHaveURL(TOKENS_ROUTE);
  await page.goForward();
  await page.goForward();
  await expect(page).toHaveURL(`${TOKENS_ROUTE}/edit`);
  await page.getByLabel("Nome da referência").fill("Fluxo visual E2E");
  await page.getByLabel("Público e necessidade").fill("Operador validando a oficina.");
  await page.getByRole("button", { name: "Tabela", exact: true }).click();
  await expect(page.getByRole("button", { name: "Tabela", exact: true })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await page.getByRole("button", { name: "Galeria", exact: true }).click();
  await page.getByRole("button", { name: "Cards", exact: true }).click();
  await page.getByLabel("Densidade").selectOption("workshop");
  await page.getByLabel("Densidade").selectOption("reading");
  await page.getByLabel("Densidade").selectOption("administration");
  await page.getByLabel("Estado simulado").selectOption("partial");
  await expect(page.getByText("Conteúdo parcial", { exact: true })).toBeVisible();
  await page.getByLabel("Estado simulado").selectOption("success");
  await page.getByLabel("Reduzir movimento nesta experiência").check();
  await page.getByRole("button", { name: "Salvar rascunho" }).click();
  await expect(page.getByRole("button", { name: /Rascunho salvo/ })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-density", "administration");
  await expect(page.locator("html")).toHaveAttribute("data-reduce-motion", "true");

  await page.reload();
  await expect(page.getByLabel("Nome da referência")).toHaveValue("Fluxo visual E2E");
  await expect(page.getByText("revisão 1", { exact: false })).toBeVisible();
  expect(await findHorizontalOverflow(page)).toEqual({
    documentOverflows: false,
    elements: [],
  });
  await expect(page.getByTestId("design-system-screen")).toHaveScreenshot(
    "design-system-editor.png",
    { animations: "disabled" },
  );

  await page.evaluate(() => window.dispatchEvent(new Event("offline")));
  await expect(page.getByText("Catálogo offline", { exact: true })).toBeVisible();
  await page.evaluate(() => window.dispatchEvent(new Event("online")));
  await expect(page.getByText("Catálogo conectado", { exact: true })).toBeVisible();

  await page.evaluate(() => {
    const key = "printora.design-system.lab.v1";
    const current = JSON.parse(window.localStorage.getItem(key) ?? "{}");
    window.localStorage.setItem(key, JSON.stringify({ ...current, revision: 2 }));
    window.dispatchEvent(new StorageEvent("storage", { key }));
  });
  await expect(
    page.getByText("Rascunho alterado em outra aba", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Carregar versão atual" }).click();
  await expect(page.getByText("revisão 2", { exact: false })).toBeVisible();
});

test("falhas do catálogo são seguras e recuperáveis", async ({
  page,
  request,
}) => {
  await ensureUser(request, PLATFORM_ADMIN_EMAIL, "Platform Admin");
  await loginInBrowser(page, PLATFORM_ADMIN_EMAIL);

  let failure: "timeout" | "rate-limit" | "server" | null = "timeout";
  await page.route("**/api/design-system/v1/capabilities", async (route) => {
    if (failure === "timeout") {
      await route.abort("timedout");
      return;
    }
    if (failure === "rate-limit") {
      await route.fulfill({
        status: 429,
        contentType: "application/json",
        body: JSON.stringify({ detail: "limite sintético" }),
      });
      return;
    }
    if (failure === "server") {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "falha sintética" }),
      });
      return;
    }
    await route.continue();
  });

  await page.goto(TOKENS_ROUTE);
  await expect(page.getByText("Não foi possível carregar", { exact: true })).toBeVisible();

  failure = "rate-limit";
  await page.getByRole("button", { name: "Tentar novamente", exact: true }).click();
  await expect(page.getByText("Não foi possível carregar", { exact: true })).toBeVisible();

  failure = "server";
  await page.getByRole("button", { name: "Tentar novamente", exact: true }).click();
  await expect(page.getByText("Não foi possível carregar", { exact: true })).toBeVisible();

  failure = null;
  await page.getByRole("button", { name: "Tentar novamente", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Design system do Printora", exact: true }),
  ).toBeVisible();
});

test("usuário comum não vê nem acessa o design system", async ({
  page,
  request,
}, testInfo) => {
  const email = syntheticEmail(testInfo, "design-system-reader");
  const session = await ensureUser(request, email, "Design System Reader");
  const denied = await request.get("/api/design-system/v1/capabilities", {
    headers: bearer(session.access_token),
  });
  expect(denied.status()).toBe(403);

  await loginInBrowser(page, email);
  await expect(
    page.getByRole("button", { name: "Design system", exact: true }),
  ).toHaveCount(0);

  await page.goto(TOKENS_ROUTE);
  await expect(
    page.getByRole("heading", { name: "Visão geral", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Design system do Printora", exact: true }),
  ).toHaveCount(0);
});
