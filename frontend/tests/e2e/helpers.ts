import type { APIRequestContext, Page, TestInfo } from "@playwright/test";
import { expect } from "@playwright/test";

const PASSWORD = "synthetic-correct-horse-97";
export const SYNTHETIC_PASSWORD = PASSWORD;
export const PLATFORM_ADMIN_EMAIL = "breno@mayder.com.br";

export function syntheticEmail(testInfo: TestInfo, role: string) {
  const project = testInfo.project.name.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
  return `${role}-${project}-r${testInfo.repeatEachIndex}@example.test`;
}

export async function ensureUser(
  request: APIRequestContext,
  email: string,
  displayName: string,
) {
  const registration = await request.post("/api/auth/register", {
    data: { email, password: PASSWORD, display_name: displayName },
  });
  if (registration.ok()) {
    return registration.json();
  }
  expect(registration.status()).toBe(400);
  const login = await request.post("/api/auth/login", {
    data: { email, password: PASSWORD },
  });
  expect(login.ok()).toBe(true);
  return login.json();
}

export function bearer(accessToken: string) {
  return { Authorization: `Bearer ${accessToken}` };
}

export async function loginInBrowser(page: Page, email: string) {
  await page.goto("/");
  await page.getByRole("button", { name: "Login", exact: true }).click();
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Senha").fill(PASSWORD);
  const loginResponse = page.waitForResponse(
    (response) =>
      response.request().method() === "POST" &&
      new URL(response.url()).pathname === "/api/auth/login",
  );
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  expect((await loginResponse).status()).toBe(200);
  await expect(
    page.getByRole("heading", { name: "Visão geral", exact: true }),
  ).toBeVisible();
}

export async function openSection(page: Page, section: string, heading: string) {
  await page.goto(`/?section=${encodeURIComponent(section)}`);
  await expect(page.getByRole("heading", { name: heading, exact: true }).first()).toBeVisible();
}
