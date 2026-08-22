import { getJson, postJson } from "./http";
import type { AuthSession } from "./types";

type RawRecord = Record<string, unknown>;

function str(raw: RawRecord, keys: string[], fallback = ""): string {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === "string") return value;
  }
  return fallback;
}

function normalizeSession(raw: RawRecord): AuthSession {
  return {
    token: str(raw, ["token", "access_token", "accessToken"]),
    username: str(raw, ["username"]),
  };
}

export async function registerUser(username: string, password: string): Promise<AuthSession> {
  const raw = await postJson<RawRecord>(
    "/auth/register",
    { username, password },
    { skipAuthRedirect: true },
  );
  return normalizeSession(raw);
}

export async function loginUser(username: string, password: string): Promise<AuthSession> {
  const raw = await postJson<RawRecord>(
    "/auth/login",
    { username, password },
    { skipAuthRedirect: true },
  );
  return normalizeSession(raw);
}

export async function logoutUser(): Promise<void> {
  await postJson("/auth/logout", {}, { skipAuthRedirect: true });
}

export async function fetchMe(): Promise<string> {
  const raw = await getJson<RawRecord>("/auth/me");
  return str(raw, ["username"]);
}
