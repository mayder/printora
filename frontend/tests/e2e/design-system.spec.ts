import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { ensureUser, loginInBrowser, syntheticEmail } from "./helpers";


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
  const email = syntheticEmail(testInfo, "design-system");
  await ensureUser(request, email, "Design System User");
  await loginInBrowser(page, email);

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

  await page.getByRole("button", { name: /Detalhe/ }).click();
  await expect(page).toHaveURL(`${TOKENS_ROUTE}/detail`);
  await expect(page.getByText("Evidências atribuídas", { exact: true })).toBeVisible();
  await expect(page.getByText("COM-0953", { exact: true })).toBeVisible();

  await page.getByRole("button", { name: /Abrir editor/ }).click();
  await expect(page).toHaveURL(`${TOKENS_ROUTE}/edit`);
  await page.getByLabel("Nome da referência").fill("Fluxo visual E2E");
  await page.getByLabel("Público e necessidade").fill("Operador validando a oficina.");
  await page.getByLabel("Densidade").selectOption("administration");
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
