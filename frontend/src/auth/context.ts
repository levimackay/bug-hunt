import { createContext } from "react";

export type AuthStatus = "loading" | "authenticated" | "anonymous";

export interface AuthValue {
  status: AuthStatus;
  username: string;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

export const AuthContext = createContext<AuthValue | null>(null);
