import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import { bearer, ensureUser, loginInBrowser, syntheticEmail } from "./helpers";


const ACCESSIBILITY_ROUTE =
  "/community/accessibility/conformidade-continua-com-wcag-e-testes-com-usuarios";

async function findHorizontalOverflow(page: Page) {
  return page.getByTestId("accessibility-screen").evaluate((root) => {
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

test("central acessível sincroniza preferências e preserva alternativas", async ({
  page,
  request,
}, testInfo) => {
  const email = syntheticEmail(testInfo, "accessibility");
  await ensureUser(request, email, "Accessibility User");
  await loginInBrowser(page, email);

  await page.goto(ACCESSIBILITY_ROUTE);
  await expect(page.getByRole("heading", { name: "Acessibilidade", exact: true })).toBeVisible();
  await expect(page.getByText("Escolha como quer usar o Printora", { exact: true })).toBeVisible();
  await expect(page.getByText("CAP-09-01", { exact: true })).toHaveCount(0);
  await expect(page.getByText("SCR-0065", { exact: true })).toHaveCount(0);
  await expect(page.getByText("COM-0449", { exact: true })).toHaveCount(0);
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
  await expect(page.getByTestId("accessibility-screen")).toHaveScreenshot(
    "accessibility-list.png",
    { animations: "disabled" },
  );

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
    expect(await findHorizontalOverflow(page)).toEqual({
      documentOverflows: false,
      elements: [],
    });
  }
  if (originalViewport) await page.setViewportSize(originalViewport);

  await page.getByText("Conheça os recursos de acessibilidade", { exact: true }).click();
  await page.getByRole("button", { name: /Saiba mais sobre Usar o Printora com confiança/ }).click();
  await expect(page).toHaveURL(`${ACCESSIBILITY_ROUTE}/detail`);
  await expect(page.getByText("Como este recurso ajuda", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("img", {
      name: "Peça retangular com botão circular no canto inferior direito",
    }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Exportar alternativa tátil" })).toBeVisible();

  await page.getByRole("button", { name: "Ajustar minhas preferências" }).click();
  await expect(page).toHaveURL(`${ACCESSIBILITY_ROUTE}/edit`);
  await page.getByLabel("Tema adaptativo").selectOption("high-contrast");
  await page.getByLabel(/Escala de texto/).fill("125");
  await page.getByLabel("Reduzir movimento e transições").check();
  await page.getByLabel("Usar linguagem simples").check();
  await page.getByLabel("Reduzir carga cognitiva e densidade").check();
  await page.getByRole("button", { name: "Salvar preferências" }).click();
  await expect(page.getByText("Preferências sincronizadas.", { exact: true })).toBeVisible();
  await expect(page.locator("html")).toHaveAttribute("data-contrast", "high");
  await expect(page.locator("html")).toHaveAttribute("data-reduce-motion", "true");

  await page.reload();
  await expect(page.getByLabel("Tema adaptativo")).toHaveValue("high-contrast");
  await expect(page.getByLabel("Reduzir movimento e transições")).toBeChecked();
  await expect(page.getByRole("heading", { name: "Ajustar acessibilidade" })).toBeVisible();

  await page.evaluate(() => window.dispatchEvent(new Event("offline")));
  await expect(page.getByText("Offline: alterações preservadas nesta tela.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Salvar preferências" })).toBeDisabled();
});

test("conflito e falha de rede não sobrescrevem preferências", async ({
  page,
  request,
}, testInfo) => {
  const email = syntheticEmail(testInfo, "accessibility-conflict");
  const session = await ensureUser(request, email, "Accessibility Conflict User");
  await loginInBrowser(page, email);
  await page.goto(`${ACCESSIBILITY_ROUTE}/edit`);
  await expect(page.getByRole("button", { name: "Salvar preferências" })).toBeVisible();

  const external = await request.put("/api/accessibility/v1/preferences", {
    headers: {
      ...bearer(session.access_token),
      "Idempotency-Key": `external-${testInfo.project.name}-1`,
    },
    data: {
      expected_revision: 0,
      theme: "dark",
      text_scale_percent: 100,
      reduce_motion: false,
      screen_reader_announcements: true,
      keyboard_navigation: true,
      voice_navigation: false,
      captions: true,
      audio_descriptions: false,
      simple_language: false,
      low_cognitive_load: false,
      three_d_text_alternative: true,
      tactile_format: "svg",
    },
  });
  expect(external.ok()).toBe(true);

  await page.getByLabel("Usar linguagem simples").check();
  await page.getByRole("button", { name: "Salvar preferências" }).click();
  await expect(
    page.getByText("Suas preferências foram alteradas em outro dispositivo.", { exact: false }),
  ).toBeVisible();

  await page.route("**/api/accessibility/v1/capabilities", (route) => route.abort("timedout"));
  await page.reload();
  await expect(page.getByRole("heading", { name: "Não foi possível abrir a central" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Tentar novamente" })).toBeVisible();
});
