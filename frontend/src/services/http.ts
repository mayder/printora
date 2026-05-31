export async function readApiError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload?.detail === "string") {
      return payload.detail;
    }
    if (typeof payload?.message === "string") {
      return payload.message;
    }
  } catch {
    // Fall back to the HTTP status below when the body is not JSON.
  }
  return `Erro ${response.status}`;
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
  return (await response.json()) as T;
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
