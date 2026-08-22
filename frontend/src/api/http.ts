import { getToken, notifyUnauthorized } from "../auth/token";

export class ApiError extends Error {
  status: number;
  body: unknown;

  constructor(status: number, message: string, body: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

export interface RequestOptions {
  // Login/register expect 401 to mean "bad credentials" and render it inline,
  // so they opt out of the global clear-token-and-redirect behavior.
  skipAuthRedirect?: boolean;
}

async function request(
  path: string,
  init: RequestInit,
  accept: string,
  options: RequestOptions = {},
): Promise<unknown> {
  const token = getToken();
  const headers: Record<string, string> = {
    Accept: accept,
    ...((init.headers as Record<string, string> | undefined) ?? {}),
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`/api${path}`, { ...init, headers });

  const contentType = res.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const body = isJson ? await res.json().catch(() => null) : await res.text();

  if (!res.ok) {
    if (res.status === 401 && !options.skipAuthRedirect) notifyUnauthorized();
    const message =
      isJson && body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `${res.status} ${res.statusText}`;
    throw new ApiError(res.status, message, body);
  }

  return body;
}

export async function getJson<T>(path: string, options?: RequestOptions): Promise<T> {
  return request(path, {}, "application/json", options) as Promise<T>;
}

// Server ambiguity (BUILD_SPEC does not pin content-type for text-ish endpoints
// like git diff or raw file content): try JSON first, fall back to raw text so
// either a `{content: string}` wrapper or a plain-text body works unmodified.
export async function getTextish(path: string): Promise<string> {
  const body = await request(path, {}, "application/json, text/plain");
  if (typeof body === "string") return body;
  if (body && typeof body === "object") {
    for (const key of ["content", "diff", "text"]) {
      if (key in body && typeof (body as Record<string, unknown>)[key] === "string") {
        return (body as Record<string, string>)[key];
      }
    }
  }
  return "";
}

export async function postJson<T>(
  path: string,
  payload: unknown,
  options?: RequestOptions,
): Promise<T> {
  return request(
    path,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "application/json",
    options,
  ) as Promise<T>;
}

export async function putJson<T>(
  path: string,
  payload: unknown,
  options?: RequestOptions,
): Promise<T> {
  return request(
    path,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    "application/json",
    options,
  ) as Promise<T>;
}
