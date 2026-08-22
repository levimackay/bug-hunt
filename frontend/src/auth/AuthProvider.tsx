import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../api/http";
import { fetchMe, loginUser, logoutUser, registerUser } from "../api/auth";
import { AuthContext, type AuthStatus } from "./context";
import {
  clearSession,
  getStoredUsername,
  getToken,
  rememberUsername,
  setSession,
  setUnauthorizedHandler,
} from "./token";

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [status, setStatus] = useState<AuthStatus>(() =>
    getToken() ? "loading" : "anonymous",
  );
  const [username, setUsername] = useState(() => getStoredUsername() ?? "");

  // Bumped on every session transition (login/register/logout/forced-out) so
  // a bootstrap fetchMe() that was already in flight for the previous session
  // can tell its result is stale and skip applying it.
  const sessionGeneration = useRef(0);

  useEffect(() => {
    setUnauthorizedHandler(() => {
      sessionGeneration.current += 1;
      setStatus("anonymous");
      setUsername("");
      navigate("/login", { replace: true });
    });
    return () => setUnauthorizedHandler(null);
  }, [navigate]);

  useEffect(() => {
    if (!getToken()) return;
    const generationAtStart = sessionGeneration.current;
    let cancelled = false;
    fetchMe()
      .then((me) => {
        if (cancelled || sessionGeneration.current !== generationAtStart) return;
        setUsername(me);
        rememberUsername(me);
        setStatus("authenticated");
      })
      .catch((error: unknown) => {
        if (cancelled || sessionGeneration.current !== generationAtStart) return;
        // A 401 has already cleared the session and redirected; anything else
        // (server down, network blip) shouldn't sign a valid session out.
        if (error instanceof ApiError && error.status === 401) return;
        setStatus("authenticated");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (name: string, password: string) => {
    const session = await loginUser(name, password);
    sessionGeneration.current += 1;
    setSession(session.token, session.username);
    setUsername(session.username);
    setStatus("authenticated");
  }, []);

  const register = useCallback(async (name: string, password: string) => {
    const session = await registerUser(name, password);
    sessionGeneration.current += 1;
    setSession(session.token, session.username);
    setUsername(session.username);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    sessionGeneration.current += 1;
    try {
      await logoutUser();
    } catch {
      // Server-side revocation is best effort; the local session is dropped
      // either way so the user is never stuck signed in.
    }
    clearSession();
    setUsername("");
    setStatus("anonymous");
    navigate("/login", { replace: true });
  }, [navigate]);

  const value = useMemo(
    () => ({ status, username, login, register, logout }),
    [status, username, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
