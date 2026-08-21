import { Link, useParams } from "react-router-dom";
import { fetchPr } from "../api/investigations";
import { useAsync } from "../hooks/useAsync";
import { AsyncBoundary } from "../components/AsyncBoundary";
import { DiffView } from "../components/DiffView";
import { TopBar } from "../components/TopBar";

export function PrView() {
  const { investigationId = "" } = useParams();
  const state = useAsync(() => fetchPr(investigationId), [investigationId]);

  return (
    <div className="flex h-full flex-col">
      <TopBar crumbs="Pull request" />
      <div className="flex-1 overflow-auto">
        <AsyncBoundary state={state}>
          {(pr) => (
            <div className="mx-auto max-w-3xl px-6 py-8">
              <h1 className="mb-2 text-xl font-medium text-ink">{pr.title || "Untitled PR"}</h1>
              <p className="mb-6 whitespace-pre-wrap text-sm leading-relaxed text-ink-dim">
                {pr.description}
              </p>

              {pr.files.length > 0 && (
                <section className="mb-6">
                  <h2 className="mb-2 font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                    Files changed ({pr.files.length})
                  </h2>
                  <ul className="border border-border bg-surface">
                    {pr.files.map((file) => (
                      <li key={file} className="border-b border-border/60 px-3 py-1.5 font-mono text-xs text-ink-dim last:border-b-0">
                        {file}
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <section className="mb-6 border border-border bg-surface">
                <h2 className="border-b border-border px-3 py-2 font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                  Diff
                </h2>
                <DiffView diff={pr.diff} />
              </section>

              <Link
                to={`/investigations/${investigationId}/review`}
                className="inline-block border border-border-strong px-3 py-1.5 font-mono text-xs text-ink hover:border-accent"
              >
                View review
              </Link>
            </div>
          )}
        </AsyncBoundary>
      </div>
    </div>
  );
}
