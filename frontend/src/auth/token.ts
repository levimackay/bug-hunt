const TOKEN_KEY = "bughunt.token";
const USERNAME_KEY = "bughunt.username";

function read(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string | null): void {
  try {
    if (value === null) window.localStorage.removeItem(key);
    else window.localStorage.setItem(key, value);
  } catch {
    // Storage can be unavailable (private mode, blocked cookies); the in-memory
    // copy below still carries the session for the life of the tab.
  }
}

let token: string | null = read(TOKEN_KEY);
let username: string | null = read(USERNAME_KEY);

export function getToken(): string | null {
  return token;
}

export function getStoredUsername(): string | null {
  return username;
}

export function setSession(nextToken: string, nextUsername: string): void {
  token = nextToken;
  username = nextUsername;
  write(TOKEN_KEY, nextToken);
  write(USERNAME_KEY, nextUsername);
}

export function rememberUsername(nextUsername: string): void {
  username = nextUsername;
  write(USERNAME_KEY, nextUsername);
}

export function clearSession(): void {
  token = null;
  username = null;
  write(TOKEN_KEY, null);
  write(USERNAME_KEY, null);
}

let unauthorizedHandler: (() => void) | null = null;

export function setUnauthorizedHandler(handler: (() => void) | null): void {
  unauthorizedHandler = handler;
}

export function notifyUnauthorized(): void {
  clearSession();
  if (unauthorizedHandler) {
    unauthorizedHandler();
    return;
  }
  if (window.location.pathname !== "/login") window.location.assign("/login");
}
