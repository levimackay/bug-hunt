import { useParams } from "react-router-dom";
import { fetchScore } from "../api/investigations";
import { useAsync } from "../hooks/useAsync";
import { AsyncBoundary } from "../components/AsyncBoundary";
import { TopBar } from "../components/TopBar";
import type { Score } from "../api/types";

const CATEGORIES: { key: keyof Omit<Score, "overall">; label: string }[] = [
  { key: "rootCause", label: "Root cause" },
  { key: "fix", label: "Fix" },
  { key: "testing", label: "Testing" },
  { key: "investigation", label: "Investigation" },
  { key: "codeQuality", label: "Code quality" },
];

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.max(0, Math.min(100, value));
  return (
    <div className="flex items-center gap-3">
      <span className="w-32 shrink-0 text-sm text-ink-dim">{label}</span>
      <div className="h-1.5 flex-1 bg-elevated">
        <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-14 shrink-0 text-right font-mono text-xs text-ink">{value}/100</span>
    </div>
  );
}

export function ScoreView() {
  const { investigationId = "" } = useParams();
  const state = useAsync(() => fetchScore(investigationId), [investigationId]);

  return (
    <div className="flex h-full flex-col">
      <TopBar crumbs="Score" />
      <div className="flex-1 overflow-auto">
        <AsyncBoundary state={state}>
          {(score) =>
            score === null ? (
              <div className="mx-auto max-w-2xl px-6 py-8">
                <h1 className="mb-2 text-xl font-medium text-ink">Score breakdown</h1>
                <p className="text-sm text-ink-faint">
                  This investigation hasn't been resolved yet — no score available.
                </p>
              </div>
            ) : (
              <div className="mx-auto max-w-2xl px-6 py-8">
                <h1 className="mb-6 text-xl font-medium text-ink">Score breakdown</h1>

                <div className="mb-6 flex items-center justify-between border border-accent bg-accent-dim/10 px-4 py-3">
                  <span className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                    Overall
                  </span>
                  <span className="font-mono text-2xl text-accent">{score.overall}</span>
                </div>

                <div className="flex flex-col gap-3 border border-border bg-surface p-4">
                  {CATEGORIES.map(({ key, label }) => (
                    <ScoreBar key={key} label={label} value={score[key]} />
                  ))}
                </div>
              </div>
            )
          }
        </AsyncBoundary>
      </div>
    </div>
  );
}
