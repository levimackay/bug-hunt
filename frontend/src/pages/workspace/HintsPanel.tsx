import { useState } from "react";
import { revealNextHint } from "../../api/investigations";
import type { Hint } from "../../api/types";
import { errorMessage } from "../../hooks/useAsync";

interface HintsPanelProps {
  investigationId: string;
}

// The API only returns a hint's cost_xp once it has already been revealed
// (POST hints/next) — nothing in the contract exposes the upcoming hint's
// cost beforehand, so the reveal button can't show a price up front. Cost is
// shown on each hint after it's revealed instead.
export function HintsPanel({ investigationId }: HintsPanelProps) {
  const [hints, setHints] = useState<Hint[]>([]);
  const [loading, setLoading] = useState(false);
  const [exhausted, setExhausted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function revealNext() {
    setLoading(true);
    setError(null);
    try {
      const hint = await revealNextHint(investigationId);
      setHints((h) => [...h, hint]);
    } catch (err) {
      setExhausted(true);
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <h2 className="border-b border-border px-3 py-2 font-mono text-[11px] uppercase tracking-wide text-ink-faint">
        Hints
      </h2>
      <div className="flex-1 overflow-y-auto px-3 py-2">
        {hints.length === 0 && <p className="text-xs text-ink-faint">No hints revealed yet.</p>}
        <ol className="flex flex-col gap-3">
          {hints.map((hint, i) => (
            <li key={i} className="border border-border bg-surface p-2.5">
              <div className="mb-1 font-mono text-[11px] text-sev-medium">-{hint.costXp} XP</div>
              <p className="text-sm text-ink-dim">{hint.text}</p>
            </li>
          ))}
        </ol>
      </div>
      <div className="border-t border-border p-3">
        <button
          type="button"
          onClick={revealNext}
          disabled={loading || exhausted}
          className="w-full border border-border-strong bg-elevated px-3 py-1.5 font-mono text-xs text-ink hover:border-accent disabled:opacity-50"
        >
          {exhausted ? "No more hints" : loading ? "revealing…" : "Reveal next hint"}
        </button>
        {error && !exhausted && <p className="mt-1 text-xs text-diff-remove">{error}</p>}
      </div>
    </div>
  );
}
