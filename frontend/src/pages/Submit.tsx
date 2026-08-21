import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { submitInvestigation } from "../api/investigations";
import type { SubmitResult } from "../api/types";
import { errorMessage } from "../hooks/useAsync";
import { TopBar } from "../components/TopBar";

const FIELDS: { key: keyof FormState; label: string; placeholder: string }[] = [
  { key: "whatWasBroken", label: "What was broken", placeholder: "The validation function rejected..." },
  { key: "why", label: "Why", placeholder: "The refactor in commit ... dropped the .lower() call..." },
  { key: "whatChanged", label: "What changed", placeholder: "Restored case-insensitive comparison and..." },
  { key: "howVerified", label: "How verified", placeholder: "Ran pytest tests/, added a regression test..." },
];

interface FormState {
  prTitle: string;
  whatWasBroken: string;
  why: string;
  whatChanged: string;
  howVerified: string;
}

const EMPTY_FORM: FormState = {
  prTitle: "",
  whatWasBroken: "",
  why: "",
  whatChanged: "",
  howVerified: "",
};

export function Submit() {
  const { investigationId = "" } = useParams();
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = Object.values(form).every((v) => v.trim().length > 0);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await submitInvestigation(investigationId, form);
      setResult(res);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <TopBar crumbs="Submit" />
      <div className="flex-1 overflow-auto">
        <div className="mx-auto max-w-2xl px-6 py-8">
          <h1 className="mb-6 text-xl font-medium text-ink">Open a pull request</h1>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div>
              <label className="mb-1 block font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                PR title
              </label>
              <input
                value={form.prTitle}
                onChange={(e) => setForm((f) => ({ ...f, prTitle: e.target.value }))}
                placeholder="Fix case-sensitive extension check in upload validation"
                className="w-full border border-border bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent"
              />
            </div>

            {FIELDS.map(({ key, label, placeholder }) => (
              <div key={key}>
                <label className="mb-1 block font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                  {label}
                </label>
                <textarea
                  value={form[key]}
                  onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
                  placeholder={placeholder}
                  rows={3}
                  className="w-full resize-y border border-border bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent"
                />
              </div>
            ))}

            <button
              type="submit"
              disabled={!canSubmit || submitting}
              className="mt-2 border border-accent bg-accent-dim/20 px-4 py-2 font-mono text-sm text-ink hover:bg-accent-dim/40 disabled:opacity-50"
            >
              {submitting ? "submitting…" : "Submit for review"}
            </button>
          </form>

          {error && <p className="mt-4 text-sm text-diff-remove">{error}</p>}

          {result && (
            <div
              className={`mt-6 border p-4 ${
                result.passed ? "border-diff-add/40 bg-diff-add-bg" : "border-diff-remove/40 bg-diff-remove-bg"
              }`}
            >
              <p className={`font-mono text-sm ${result.passed ? "text-diff-add" : "text-diff-remove"}`}>
                {result.passed ? "Hidden tests passed" : "Hidden tests failed"}
              </p>
              {result.message && <p className="mt-1 text-sm text-ink-dim">{result.message}</p>}
              <div className="mt-3 flex gap-3">
                <Link
                  to={`/investigations/${investigationId}/pr`}
                  className="border border-border-strong px-3 py-1.5 font-mono text-xs text-ink hover:border-accent"
                >
                  View PR
                </Link>
                <Link
                  to={`/investigations/${investigationId}/review`}
                  className="border border-border-strong px-3 py-1.5 font-mono text-xs text-ink hover:border-accent"
                >
                  View review
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
