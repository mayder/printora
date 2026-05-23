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

export async function apiRequest<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T> {
  const response = await fetch(input, init);
  if (!response.ok) {
    throw new Error(await readApiError(response));
  }
  return (await response.json()) as T;
}

export async function apiOptional<T>(input: RequestInfo | URL, init?: RequestInit): Promise<T | null> {
  const response = await fetch(input, init);
  if (!response.ok) {
    return null;
  }
  return (await response.json()) as T;
}

export async function apiResponse(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  return fetch(input, init);
}
