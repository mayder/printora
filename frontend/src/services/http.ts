export async function readApiError(response: Response): Promise<string> {
  const clone = response.clone();
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") {
      if (payload.detail === "autenticação reforçada obrigatória para ação crítica") {
        return "Ação crítica bloqueada. Gere uma autorização em Conta > 2FA e autenticação reforçada e tente novamente.";
      }
      return readableApiError(payload.detail, response.status);
    }
    if (typeof payload?.message === "string") {
      return readableApiError(payload.message, response.status);
    }
  } catch {
    try {
      return readableApiError(await clone.text(), response.status);
    } catch {
      // Fall back to the HTTP status below.
    }
  }
  return `Erro ${response.status}`;
}

function readableApiError(message: string, status: number): string {
  const compact = message.replace(/\s+/g, " ").trim();
  const lower = compact.toLowerCase();
  if (
    lower.includes("error 524") ||
    lower.includes("cloudflare") ||
    lower.includes("cf-error") ||
    lower.includes("<!doctype") ||
    lower.includes("<html")
  ) {
    return "A requisição demorou mais que o limite do gateway. A impressora pode continuar executando; confira o histórico no Printora antes de repetir.";
  }
  if (!compact) {
    return `Erro ${status}`;
  }
  if (compact.length > 500) {
    return `${compact.slice(0, 497)}...`;
  }
  return compact;
}

const AUTH_TOKEN_KEY = "printora.authToken";
const STEP_UP_TOKEN_KEY = "printora.stepUpToken";

export function getStoredAuthToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function storeAuthToken(token: string | null): void {
  if (typeof window === "undefined") {
    return;
  }
  if (token) {
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(AUTH_TOKEN_KEY);
  }
}

export function getStoredStepUpToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  return window.localStorage.getItem(STEP_UP_TOKEN_KEY);
}

export function storeStepUpToken(token: string | null): void {
  if (typeof window === "undefined") {
    return;
  }
  if (token) {
    window.localStorage.setItem(STEP_UP_TOKEN_KEY, token);
  } else {
    window.localStorage.removeItem(STEP_UP_TOKEN_KEY);
  }
}

function apiInput(input: RequestInfo | URL): RequestInfo | URL {
  if (typeof input !== "string" || !input.startsWith("/")) {
    return input;
  }
  if (typeof window === "undefined") {
    return input;
  }
  const apiBaseUrl = import.meta.env.VITE_PRINTORA_API_BASE_URL;
  if (apiBaseUrl) {
    return new URL(input, apiBaseUrl).toString();
  }
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    if (window.location.port && window.location.port !== "8069") {
      return new URL(input, "http://127.0.0.1:8069").toString();
    }
  }
  return input;
}

function apiInit(init?: RequestInit): RequestInit | undefined {
  const token = getStoredAuthToken();
  if (!token) {
    return init;
  }
  const headers = new Headers(init?.headers);
  if (!headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return { ...init, headers };
}

export async function apiRequest<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(apiInput(input), apiInit(init));
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}

export async function apiOptional<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T | null> {
  const response = await fetch(apiInput(input), apiInit(init));
  if (!response.ok) {
    if (response.status === 401) {
      return null;
    }
    throw new Error(await readApiError(response));
  }
  return (await response.json()) as T;
}

export async function apiResponse(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  return fetch(apiInput(input), apiInit(init));
}
