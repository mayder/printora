import { expect, test } from "@playwright/test";
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

test("comunidade, busca, projeto e quarentena percorrem contratos reais", async ({
  page,
  request,
}, testInfo) => {
  const email = syntheticEmail(testInfo, "project-owner");
  const owner = await ensureUser(request, email, "Project Owner");
  const headers = bearer(owner.access_token);
  const suffix = `${testInfo.project.name}-${testInfo.repeatEachIndex}`;

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
});

test("agente sintético pareia, envia heartbeat e aparece na frota", async ({
  page,
  request,
}, testInfo) => {
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
});

test("administração, financeiro sandbox e fabricação respeitam papéis", async ({
  page,
  request,
}, testInfo) => {
  const admin = await ensureUser(request, PLATFORM_ADMIN_EMAIL, "Platform Admin");
  const adminHeaders = bearer(admin.access_token);
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
