import { useState } from "react";
import { Link, Navigate, useLocation } from "react-router-dom";
import { AuthForm } from "../components/AuthForm";
import { useAuth } from "../auth/useAuth";
import { errorMessage } from "../hooks/useAsync";

export function Login() {
  const { status, login } = useAuth();
  const location = useLocation();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (status === "authenticated") {
    const from = (location.state as { from?: string } | null)?.from;
    return <Navigate to={from && from !== "/login" ? from : "/"} replace />;
  }

  async function handleSubmit(username: string, password: string) {
    setPending(true);
    setError(null);
    try {
      await login(username, password);
    } catch (caught) {
      setError(errorMessage(caught));
      setPending(false);
    }
  }

  return (
    <AuthForm
      heading="Sign in"
      intro="Pick up your open investigations where you left them."
      submitLabel="Sign in"
      pendingLabel="signing in…"
      pending={pending}
      error={error}
      onSubmit={handleSubmit}
      footer={
        <>
          No account yet?{" "}
          <Link to="/register" className="text-accent hover:underline">
            Create one
          </Link>
        </>
      }
    />
  );
}
