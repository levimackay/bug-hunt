import { useState, type FormEvent, type ReactNode } from "react";

interface AuthFormProps {
  heading: string;
  intro: string;
  submitLabel: string;
  pendingLabel: string;
  pending: boolean;
  error: string | null;
  passwordHint?: string;
  minPasswordLength?: number;
  onSubmit: (username: string, password: string) => void;
  footer: ReactNode;
}

const FIELD_CLASS =
  "w-full border border-border bg-ground px-3 py-2 font-mono text-sm text-ink outline-none placeholder:text-ink-faint focus:border-accent";

export function AuthForm({
  heading,
  intro,
  submitLabel,
  pendingLabel,
  pending,
  error,
  passwordHint,
  minPasswordLength = 1,
  onSubmit,
  footer,
}: AuthFormProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (pending) return;
    onSubmit(username.trim(), password);
  }

  return (
    <div className="flex h-full items-center justify-center px-6 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-6">
          <span className="font-mono text-[13px] font-medium tracking-tight text-ink">
            bug<span className="text-accent">hunt</span>
          </span>
          <p className="mt-1 font-mono text-[11px] uppercase tracking-wide text-ink-faint">
            Nexus Engineering
          </p>
        </div>

        <form onSubmit={handleSubmit} className="border border-border bg-surface p-5">
          <h1 className="text-lg font-medium text-ink">{heading}</h1>
          <p className="mt-1 mb-5 text-sm text-ink-dim">{intro}</p>

          <label className="mb-4 block">
            <span className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-faint">
              Username
            </span>
            <input
              name="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              autoCapitalize="none"
              spellCheck={false}
              required
              className={FIELD_CLASS}
            />
          </label>

          <label className="block">
            <span className="mb-1.5 block font-mono text-[11px] uppercase tracking-wide text-ink-faint">
              Password
            </span>
            <input
              name="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={minPasswordLength > 1 ? "new-password" : "current-password"}
              minLength={minPasswordLength}
              required
              className={FIELD_CLASS}
            />
          </label>
          {passwordHint && (
            <p className="mt-1.5 font-mono text-[11px] text-ink-faint">{passwordHint}</p>
          )}

          {error && (
            <p
              role="alert"
              className="mt-4 border border-diff-remove/40 bg-diff-remove-bg px-3 py-2 font-mono text-xs text-diff-remove"
            >
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={pending}
            className="mt-5 w-full border border-accent bg-accent-dim/20 px-4 py-2 font-mono text-sm text-ink hover:bg-accent-dim/40 disabled:opacity-50"
          >
            {pending ? pendingLabel : submitLabel}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-ink-dim">{footer}</p>
      </div>
    </div>
  );
}
