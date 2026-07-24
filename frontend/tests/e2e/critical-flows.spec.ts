import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";
import {
  PLATFORM_ADMIN_EMAIL,
  SYNTHETIC_PASSWORD,
  bearer,
  ensureUser,
  loginInBrowser,
  openSection,
  syntheticEmail,
} from "./helpers";

const VALID_STL = Buffer.from(
  "solid printora\nfacet normal 0 0 0\nouter loop\nvertex 0 0 0\nvertex 1 0 0\nvertex 0 1 0\nendloop\nendfacet\nendsolid\n",
);

async function findUncontainedHorizontalOverflow(page: Page, rootSelector = ".workspace") {
  return page.locator(rootSelector).evaluate((workspace) => {
    const viewportWidth = document.documentElement.clientWidth;
    return Array.from(workspace.querySelectorAll<HTMLElement>("*"))
      .filter((element) => {
        const rect = element.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) return false;
        if (rect.left >= -1 && rect.right <= viewportWidth + 1) return false;
        let parent = element.parentElement;
        while (parent && parent !== workspace) {
          const overflowX = getComputedStyle(parent).overflowX;
          if (overflowX === "auto" || overflowX === "scroll") return false;
          parent = parent.parentElement;
        }
        return true;
      })
      .slice(0, 10)
      .map((element) => ({
        tag: element.tagName.toLowerCase(),
        className: element.className,
        text: element.textContent?.trim().replace(/\s+/g, " ").slice(0, 80) ?? "",
        bounds: {
          left: Math.round(element.getBoundingClientRect().left),
          right: Math.round(element.getBoundingClientRect().right),
        },
      }));
  });
}

test("comunidade, busca, projeto e quarentena percorrem contratos reais", async ({
  page,
  request,
}, testInfo) => {
  const email = syntheticEmail(testInfo, "project-owner");
  const owner = await ensureUser(request, email, "Project Owner");
  const headers = bearer(owner.access_token);
  const suffix = `${testInfo.project.name}-${testInfo.repeatEachIndex}`;
  const publicMakerEmail = syntheticEmail(testInfo, "public-maker");
  const publicMaker = await ensureUser(request, publicMakerEmail, "Public Maker");
  const publicMakerHeaders = bearer(publicMaker.access_token);
  const publicSlug = `e2e-maker-${suffix}`;

  const publicProfile = await request.put("/api/social/me/profile", {
    headers: publicMakerHeaders,
    data: {
      slug: publicSlug,
      display_name: `Maker público ${suffix}`,
      bio: "Perfil sintético para validação responsiva.",
      visibility: "public",
    },
  });
  expect(publicProfile.ok()).toBe(true);

  const created = await request.post("/api/print-projects", {
    headers,
    data: {
      title: `Fixture E2E ${suffix}`,
      description: "Projeto sintético isolado para o gate E2E.",
      visibility: "private",
      license: "cc0",
      tags: ["e2e", "synthetic"],
    },
  });
  expect(created.ok()).toBe(true);
  const project = await created.json();

  const rejected = await request.post(
    `/api/print-projects/${project.id}/files/upload?file_name=invalido.stl&file_role=optional_part`,
    {
      headers: { ...headers, "Content-Type": "application/octet-stream" },
      data: Buffer.from("not-an-stl"),
    },
  );
  expect(rejected.ok()).toBe(true);
  expect((await rejected.json()).files).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        file_name: "invalido.stl",
        validation_status: "rejected",
        can_slice: false,
      }),
    ]),
  );

  const uploaded = await request.post(
    `/api/print-projects/${project.id}/files/upload?file_name=valido.stl&file_role=primary`,
    {
      headers: { ...headers, "Content-Type": "application/octet-stream" },
      data: VALID_STL,
    },
  );
  expect(uploaded.ok()).toBe(true);
  expect((await uploaded.json()).files).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        file_name: "valido.stl",
        validation_status: "validated",
        can_slice: true,
      }),
    ]),
  );

  const search = await request.get("/api/social/search?q=fixture");
  expect(search.ok()).toBe(true);
  const communities = await request.get("/api/social/communities");
  expect(communities.ok()).toBe(true);
  const communityRows = await communities.json() as Array<{
    slug: string;
    name: string;
    variant_id: number | null;
  }>;
  const publicCommunity = communityRows.find((community) => community.variant_id !== null);
  expect(publicCommunity, "catálogo sintético deve expor uma comunidade de variante").toBeDefined();

  const publicPrinterResponse = await request.post("/api/printers", {
    headers: publicMakerHeaders,
    data: {
      name: `Voron pública ${suffix}`,
      moonraker_url: "http://public-e2e-secret.invalid:7125",
      host_audit_mode: "disabled",
    },
  });
  expect(publicPrinterResponse.ok()).toBe(true);
  const publicPrinter = await publicPrinterResponse.json();
  const publishedPrinter = await request.put(
    `/api/printers/${publicPrinter.id}/public-profile`,
    {
      headers: publicMakerHeaders,
      data: {
        public_profile_enabled: true,
        catalog_variant_id: publicCommunity!.variant_id,
        public_name: `Voron pública ${suffix}`,
        public_description: "Impressora sintética para validação responsiva.",
        public_mods: ["Tap"],
      },
    },
  );
  expect(publishedPrinter.ok()).toBe(true);

  await loginInBrowser(page, email);
  await openSection(page, "projects", "Projetos de impressão");
  await page.getByRole("button", { name: "Meus projetos" }).click();
  await expect(page.getByText(`Fixture E2E ${suffix}`, { exact: true })).toBeVisible();
  await openSection(page, "social", "Social");
  await expect(
    page.getByRole("heading", {
      name: "Makers, impressoras públicas e comunidades técnicas",
      exact: true,
    }),
  ).toBeVisible();

  const publicViewports = testInfo.project.name === "desktop-chromium"
    ? [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]
    : [{ width: 320, height: 568 }, { width: 390, height: 844 }, { width: 768, height: 1024 }];
  for (const viewport of publicViewports) {
    await page.setViewportSize(viewport);

    await page.goto(`/u/${publicSlug}`);
    await expect(page.getByRole("heading", { name: `Maker público ${suffix}`, exact: true })).toBeVisible();
    expect(await findUncontainedHorizontalOverflow(page, ".public-profile-shell")).toEqual([]);

    await page.goto(`/p/${publicPrinter.id}`);
    await expect(page.getByRole("heading", { name: `Voron pública ${suffix}`, exact: true })).toBeVisible();
    await expect(page.getByText("public-e2e-secret.invalid", { exact: false })).toHaveCount(0);
    expect(await findUncontainedHorizontalOverflow(page, ".public-profile-shell")).toEqual([]);

    await page.goto(`/c/${publicCommunity!.slug}`);
    await expect(page.getByRole("heading", { name: publicCommunity!.name, exact: true })).toBeVisible();
    for (const tabName of ["Feed", "Projetos", "Mods", "Perfis", "Membros", "Impressoras públicas"]) {
      await page.getByRole("button", { name: tabName, exact: true }).click();
      expect(
        await findUncontainedHorizontalOverflow(page),
        `${tabName} ultrapassou a comunidade em ${viewport.width}px`,
      ).toEqual([]);
    }
  }
});

test("agente sintético pareia, envia heartbeat e aparece na frota", async ({
  page,
  request,
}, testInfo) => {
  test.setTimeout(90_000);
  if (testInfo.project.name === "mobile-chromium") {
    await page.setViewportSize({ width: 320, height: 568 });
  } else {
    await page.setViewportSize({ width: 1024, height: 768 });
  }
  const email = syntheticEmail(testInfo, "agent-owner");
  const owner = await ensureUser(request, email, "Agent Owner");
  const headers = bearer(owner.access_token);
  const suffix = `${testInfo.project.name}-${testInfo.repeatEachIndex}`;

  const printerResponse = await request.post("/api/printers", {
    headers,
    data: {
      name: `Voron E2E ${suffix}`,
      moonraker_url: "http://voron-e2e.invalid:7125",
      host_audit_mode: "disabled",
    },
  });
  expect(printerResponse.ok()).toBe(true);
  const printer = await printerResponse.json();
  const tokenResponse = await request.post(
    `/api/printers/${printer.id}/pairing/tokens`,
    { headers, data: { ttl_minutes: 15 } },
  );
  expect(tokenResponse.ok()).toBe(true);
  const pairingToken = await tokenResponse.json();
  const exchangeResponse = await request.post("/api/agent/pairing/exchange", {
    data: {
      pairing_token: pairingToken.token,
      stable_id: `agent-e2e-${suffix}`,
      agent_version: "0.1.34",
      platform: "linux-arm64",
      capabilities: { heartbeat: true, snapshot: true },
    },
  });
  expect(exchangeResponse.ok()).toBe(true);
  const exchange = await exchangeResponse.json();
  const heartbeat = await request.post("/api/agent/heartbeat", {
    headers: bearer(exchange.credential),
    data: {
      agent_version: "0.1.34",
      platform: "linux-arm64",
      capabilities: { heartbeat: true, snapshot: true },
    },
  });
  expect(heartbeat.ok()).toBe(true);
  expect(await heartbeat.json()).toMatchObject({
    accepted: true,
    printer_id: printer.id,
    agent_id: exchange.agent_id,
  });

  await loginInBrowser(page, email);
  await openSection(page, "agents", "Agentes");
  await expect(page.getByText(`agent-e2e-${suffix}`, { exact: true }).first()).toBeVisible();
  await expect(page.getByText(`Voron E2E ${suffix}`, { exact: true }).first()).toBeVisible();
  await page.getByRole("button", { name: "Detalhar", exact: true }).first().click();
  await expect(page.getByRole("heading", { name: "Detalhe do agente", exact: true })).toBeVisible();
  await expect(page.getByText("linux-arm64", { exact: true })).toHaveCount(0);
  await expect(page.getByText("http://voron-e2e.invalid:7125", { exact: true })).toHaveCount(0);
  await page.getByRole("button", { name: "Impressora", exact: true }).click();
  const printerHeader = page.locator(".printer-detail-header");
  await expect(printerHeader).toBeVisible();
  const responsiveBounds = await printerHeader.evaluate((element) => {
    const panel = element.getBoundingClientRect();
    const heading = element.querySelector(".panel-heading")?.getBoundingClientRect();
    const tabs = element.querySelector(".detail-tabbar")?.getBoundingClientRect();
    return {
      panelWidth: panel.width,
      headingRight: heading?.right ?? Number.POSITIVE_INFINITY,
      tabsRight: tabs?.right ?? Number.POSITIVE_INFINITY,
      viewportWidth: document.documentElement.clientWidth,
    };
  });
  expect(responsiveBounds.panelWidth).toBeGreaterThan(
    testInfo.project.name === "desktop-chromium" ? 700 : 280,
  );
  expect(responsiveBounds.headingRight).toBeLessThanOrEqual(responsiveBounds.viewportWidth + 1);
  expect(responsiveBounds.tabsRight).toBeLessThanOrEqual(responsiveBounds.viewportWidth + 1);
  await expect(page.getByText("http://voron-e2e.invalid:7125", { exact: true })).toHaveCount(0);
  await expect(page.getByText("Auditoria", { exact: true })).toHaveCount(0);
  for (const tabName of [
    "Resumo",
    "Operação",
    "Arquivos G-code",
    "Atualizações",
    "Calibração",
    "Firmware",
    "Manutenção",
    "Diagnóstico",
    "Agentes",
  ]) {
    const tab = page.getByRole("tab", { name: tabName, exact: true });
    await tab.click();
    await expect(tab).toHaveAttribute("aria-selected", "true");
    if (tabName === "Manutenção") {
      await page.getByRole("button", { name: "Adicionar registro", exact: true }).click();
      const maintenanceDialog = page.getByRole("dialog", { name: "Registro livre de manutenção", exact: true });
      await expect(maintenanceDialog).toBeVisible();
      expect(await findUncontainedHorizontalOverflow(page, "[role='dialog']")).toEqual([]);
      await maintenanceDialog.getByRole("button", { name: "Fechar", exact: true }).click();
    }
    if (tabName === "Diagnóstico") {
      for (const [trigger, dialogName] of [
        ["Relatório seguro", "Relatório para compartilhar"],
        ["Criar política", "Criar política de backup"],
        ["Comparar backups", "Comparar backups"],
        ["Planejar restore", "Planejar restore seguro"],
      ] as const) {
        await page.getByRole("button", { name: trigger, exact: true }).click();
        const reportDialog = page.getByRole("dialog", { name: dialogName, exact: true });
        await expect(reportDialog).toBeVisible();
        expect(
          await findUncontainedHorizontalOverflow(page, "[role='dialog']"),
          `${dialogName} ultrapassou o viewport`,
        ).toEqual([]);
        await reportDialog.getByRole("button", { name: "Fechar", exact: true }).first().click();
      }
    }
    expect(
      await findUncontainedHorizontalOverflow(page),
      `${tabName} ultrapassou a largura do detalhe da impressora`,
    ).toEqual([]);
  }
});

test("administração, financeiro sandbox e fabricação respeitam papéis", async ({
  page,
  request,
}, testInfo) => {
  const admin = await ensureUser(request, PLATFORM_ADMIN_EMAIL, "Platform Admin");
  const adminHeaders = bearer(admin.access_token);
  const platformFinanceOverview = await request.get("/api/admin/finance/overview", {
    headers: adminHeaders,
  });
  expect(platformFinanceOverview.ok()).toBe(true);
  const platformFinanceReadiness = await request.get("/api/admin/finance/readiness", {
    headers: adminHeaders,
  });
  expect(platformFinanceReadiness.ok()).toBe(true);
  const platformManufacturing = await request.get("/api/admin/manufacturing/overview", {
    headers: adminHeaders,
  });
  expect(platformManufacturing.ok()).toBe(true);
  const stepUpResponse = await request.post("/api/auth/step-up", {
    headers: adminHeaders,
    data: {
      purpose: "finance_sensitive_action",
      password: SYNTHETIC_PASSWORD,
    },
  });
  expect(stepUpResponse.ok()).toBe(true);
  const stepUp = await stepUpResponse.json();
  const roleResponse = await request.put("/api/admin/finance/roles", {
    headers: adminHeaders,
    data: {
      user_id: admin.user.id,
      role: "finance_operator",
      active: true,
      step_up_token: stepUp.step_up_token,
    },
  });
  expect(roleResponse.ok()).toBe(true);
  const auditorStepUpResponse = await request.post("/api/auth/step-up", {
    headers: adminHeaders,
    data: {
      purpose: "finance_sensitive_action",
      password: SYNTHETIC_PASSWORD,
    },
  });
  expect(auditorStepUpResponse.ok()).toBe(true);
  const auditorStepUp = await auditorStepUpResponse.json();
  const auditorRoleResponse = await request.put("/api/admin/finance/roles", {
    headers: adminHeaders,
    data: {
      user_id: admin.user.id,
      role: "finance_auditor",
      active: true,
      step_up_token: auditorStepUp.step_up_token,
    },
  });
  expect(auditorRoleResponse.ok()).toBe(true);
  const suffix = `${testInfo.project.name}-${testInfo.repeatEachIndex}`;
  const sandboxIntent = await request.post("/api/admin/finance/sandbox/intents", {
    headers: adminHeaders,
    data: {
      amount_minor: 9700,
      currency: "BRL",
      idempotency_key: `e2e-finance-${suffix}`,
    },
  });
  expect(sandboxIntent.ok()).toBe(true);
  expect(await sandboxIntent.json()).toMatchObject({
    provider: "sandbox",
    amount_minor: 9700,
    currency: "BRL",
  });

  const manufacturingRole = await request.put(
    `/api/admin/manufacturing/roles/${admin.user.id}/production_operator`,
    { headers: adminHeaders },
  );
  expect(manufacturingRole.ok()).toBe(true);
  const manufacturing = await request.get("/api/admin/manufacturing/overview", {
    headers: adminHeaders,
  });
  expect(manufacturing.ok()).toBe(true);

  await loginInBrowser(page, PLATFORM_ADMIN_EMAIL);
  await openSection(page, "settings", "Administração");
  await openSection(page, "finance", "Finanças");
  await expect(page.getByText("sandbox", { exact: true })).toBeVisible();
  await openSection(page, "manufacturing", "Fabricação");
  await expect(page.getByRole("heading", { name: "Ordens produtivas", exact: true })).toBeVisible();
  const manufacturingWidth = await page.locator(".manufacturing-screen").evaluate(
    (element) => element.getBoundingClientRect().width,
  );
  expect(manufacturingWidth).toBeGreaterThan(
    testInfo.project.name === "desktop-chromium" ? 700 : 300,
  );
});

test("telas principais permanecem utilizáveis em desktop, tablet e celular", async ({
  page,
  request,
}, testInfo) => {
  test.setTimeout(90_000);
  await ensureUser(request, PLATFORM_ADMIN_EMAIL, "Platform Admin");
  await loginInBrowser(page, PLATFORM_ADMIN_EMAIL);

  const routes = [
    ["overview", "Visão geral"],
    ["printers", "Impressoras"],
    ["agents", "Agentes"],
    ["projects", "Projetos de impressão"],
    ["social", "Social"],
    ["catalog", "Catálogo"],
    ["setup", "Setup"],
    ["finance", "Finanças"],
    ["manufacturing", "Fabricação"],
    ["data-intelligence", "Dados e inteligência"],
    ["settings", "Administração"],
    ["account", "Conta"],
    ["about", "Sobre"],
    ["license", "Licença"],
  ] as const;
  const viewports = testInfo.project.name === "desktop-chromium"
    ? [{ width: 1024, height: 768 }, { width: 1440, height: 900 }]
    : [{ width: 320, height: 568 }, { width: 390, height: 844 }, { width: 768, height: 1024 }];

  for (const viewport of viewports) {
    await page.setViewportSize(viewport);
    for (const [section, heading] of routes) {
      await openSection(page, section, heading);
      if (section === "overview") {
        await page.getByRole("button", { name: /alertas da frota/i }).click();
        const alertsDialog = page.getByRole("dialog", { name: "Central de alertas", exact: true });
        await expect(alertsDialog).toBeVisible();
        expect(await findUncontainedHorizontalOverflow(page, "[role='dialog']")).toEqual([]);
        await alertsDialog.getByRole("button", { name: "Fechar", exact: true }).click();
      }
      if (section === "printers") {
        await page.getByRole("button", { name: "Adicionar impressora", exact: true }).click();
        const printerDialog = page.getByRole("dialog", { name: "Cadastrar impressora", exact: true });
        await expect(printerDialog).toBeVisible();
        expect(await findUncontainedHorizontalOverflow(page, "[role='dialog']")).toEqual([]);
        await printerDialog.getByRole("button", { name: "Fechar", exact: true }).click();
      }
      const overflowing = await findUncontainedHorizontalOverflow(page);
      expect(
        overflowing,
        `${section} ultrapassou ${viewport.width}x${viewport.height}`,
      ).toEqual([]);
    }
  }
});

test("timeout e erro 5xx são recuperáveis sem recarregar a sessão", async ({
  page,
  request,
}, testInfo) => {
  const email = syntheticEmail(testInfo, "recovery-ui");
  await ensureUser(request, email, "Recovery User");
  await loginInBrowser(page, email);

  let failure: "timeout" | "server" | null = "timeout";
  await page.route("**/api/print-projects**", async (route) => {
    if (failure === "timeout") {
      await route.abort("timedout");
      return;
    }
    if (failure === "server") {
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "falha sintética 5xx" }),
      });
      return;
    }
    await route.continue();
  });

  await openSection(page, "projects", "Projetos de impressão");
  await expect(page.getByText(/Failed to fetch|ERR_TIMED_OUT/i)).toBeVisible();
  failure = "server";
  await page.getByRole("button", { name: "Atualizar" }).first().click();
  await expect(page.getByText("falha sintética 5xx", { exact: true })).toBeVisible();
  failure = null;
  await page.getByRole("button", { name: "Atualizar" }).first().click();
  await expect(page.getByText("falha sintética 5xx", { exact: true })).toBeHidden();
  await expect(page.getByRole("heading", { name: "Explorar", exact: true })).toBeVisible();
});
