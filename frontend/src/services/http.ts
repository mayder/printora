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
    if (window.location.port && window.location.port !== "8085") {
      return new URL(input, "http://127.0.0.1:8085").toString();
    }
  }
  return input;
}

export async function apiRequest<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(apiInput(input), init);
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return (await response.json()) as T;
}

export async function apiOptional<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T | null> {
  const response = await fetch(apiInput(input), init);
  if (!response.ok) {
    return null;
  }
  return (await response.json()) as T;
}

export async function apiResponse(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  return fetch(apiInput(input), init);
}
