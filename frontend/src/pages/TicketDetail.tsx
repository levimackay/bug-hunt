import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { fetchTicketDetail } from "../api/tickets";
import { createInvestigation } from "../api/investigations";
import { useAsync, errorMessage } from "../hooks/useAsync";
import { AsyncBoundary } from "../components/AsyncBoundary";
import { SeverityPill, StatusPill } from "../components/Pill";
import { TopBar } from "../components/TopBar";

export function TicketDetail() {
  const { scenarioId = "" } = useParams();
  const navigate = useNavigate();
  const state = useAsync(() => fetchTicketDetail(scenarioId), [scenarioId]);
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState<string | null>(null);

  async function startInvestigation() {
    setStarting(true);
    setStartError(null);
    try {
      const result = await createInvestigation(scenarioId);
      navigate(`/investigations/${result.investigationId}`);
    } catch (error) {
      setStartError(errorMessage(error));
      setStarting(false);
    }
  }

  return (
    <div className="flex h-full flex-col">
      <TopBar crumbs="Ticket detail" />
      <div className="flex-1 overflow-auto">
        <AsyncBoundary state={state}>
          {(ticket) => (
            <div className="mx-auto max-w-3xl px-6 py-8">
              <div className="mb-3 flex items-center gap-2">
                <SeverityPill severity={ticket.severity} />
                <StatusPill status={ticket.status} />
                <span className="font-mono text-xs text-ink-faint">{ticket.id}</span>
              </div>
              <h1 className="mb-1 text-2xl font-medium text-ink">{ticket.title}</h1>
              <p className="mb-6 font-mono text-xs text-ink-faint">
                repo: {ticket.repoName} · reported by {ticket.reporter}
              </p>

              <section className="mb-6 border border-border bg-surface p-4">
                <h2 className="mb-2 font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                  Bug report
                </h2>
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{ticket.body}</p>
              </section>

              {ticket.slackThread.length > 0 && (
                <section className="mb-8 border border-border bg-surface p-4">
                  <h2 className="mb-3 font-mono text-[11px] uppercase tracking-wide text-ink-faint">
                    Slack thread
                  </h2>
                  <ul className="flex flex-col gap-3">
                    {ticket.slackThread.map((message, i) => (
                      <li key={i} className="text-sm">
                        <span className="font-medium text-ink">{message.author}</span>
                        <p className="mt-0.5 text-ink-dim">{message.body}</p>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <button
                type="button"
                onClick={startInvestigation}
                disabled={starting}
                className="border border-accent bg-accent-dim/20 px-4 py-2 font-mono text-sm text-ink hover:bg-accent-dim/40 disabled:opacity-50"
              >
                {starting ? "starting…" : "Start investigation"}
              </button>
              {startError && <p className="mt-2 text-sm text-diff-remove">{startError}</p>}
            </div>
          )}
        </AsyncBoundary>
      </div>
    </div>
  );
}
