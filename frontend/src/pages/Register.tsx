import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { AuthForm } from "../components/AuthForm";
import { useAuth } from "../auth/useAuth";
import { errorMessage } from "../hooks/useAsync";

const MIN_PASSWORD_LENGTH = 8;

export function Register() {
  const { status, register } = useAuth();
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (status === "authenticated") return <Navigate to="/" replace />;

  async function handleSubmit(username: string, password: string) {
    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Password must be at least ${MIN_PASSWORD_LENGTH} characters.`);
      return;
    }
    setPending(true);
    setError(null);
    try {
      await register(username, password);
    } catch (caught) {
      setError(errorMessage(caught));
      setPending(false);
    }
  }

  return (
    <AuthForm
      heading="Create account"
      intro="Your investigations, XP and skill mastery are tracked per account."
      submitLabel="Create account"
      pendingLabel="creating…"
      pending={pending}
      error={error}
      passwordHint={`At least ${MIN_PASSWORD_LENGTH} characters.`}
      minPasswordLength={MIN_PASSWORD_LENGTH}
      onSubmit={handleSubmit}
      footer={
        <>
          Already have an account?{" "}
          <Link to="/login" className="text-accent hover:underline">
            Sign in
          </Link>
        </>
      }
    />
  );
}
