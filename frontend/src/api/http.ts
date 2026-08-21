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

async function handle(res: Response): Promise<unknown> {
  const contentType = res.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const body = isJson ? await res.json().catch(() => null) : await res.text();

  if (!res.ok) {
    const message =
      isJson && body && typeof body === "object" && "detail" in body
        ? String((body as { detail: unknown }).detail)
        : `${res.status} ${res.statusText}`;
    throw new ApiError(res.status, message, body);
  }

  return body;
}

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { Accept: "application/json" },
  });
  return handle(res) as Promise<T>;
}

// Server ambiguity (BUILD_SPEC does not pin content-type for text-ish endpoints
// like git diff or raw file content): try JSON first, fall back to raw text so
// either a `{content: string}` wrapper or a plain-text body works unmodified.
export async function getTextish(path: string): Promise<string> {
  const res = await fetch(`/api${path}`, {
    headers: { Accept: "application/json, text/plain" },
  });
  const body = await handle(res);
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

export async function postJson<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res) as Promise<T>;
}

export async function putJson<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  return handle(res) as Promise<T>;
}
