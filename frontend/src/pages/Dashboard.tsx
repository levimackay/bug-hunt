import type { ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { fetchTickets } from "../api/tickets";
import { fetchProfile } from "../api/profile";
import type { PlayerProfile, TicketSummary } from "../api/types";
import { useAsync, type AsyncState } from "../hooks/useAsync";
import { AsyncBoundary } from "../components/AsyncBoundary";
import { SeverityPill, StatusPill } from "../components/Pill";
import { SkillBar } from "../components/SkillBar";
import { TopBar } from "../components/TopBar";
import { useAuth } from "../auth/useAuth";

// Mirrors the backend progression constant in SCORING_AND_SCENARIOS_SPEC; used
// only to draw the bar toward the next level, never to compute the level itself.
const XP_PER_LEVEL = 500;

const OPEN_STATUSES = new Set(["investigating", "in_progress", "submitted", "in_review"]);
const DIFFICULTY_ORDER = ["intern", "junior", "engineer", "senior", "staff"];

function difficultyRank(difficulty: string): number {
  const index = DIFFICULTY_ORDER.indexOf(difficulty.toLowerCase());
  return index === -1 ? DIFFICULTY_ORDER.length : index;
}

// Scenario ids read like `bug-1842-profile-upload`; the ticket ref is the part
// an engineer would actually say out loud.
function ticketRef(id: string): string {
  const match = /^bug-(\d+)/i.exec(id);
  return match ? `BUG-${match[1]}` : id;
}

function greeting(date: Date): string {
  const hour = date.getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function ticketHref(ticket: TicketSummary): string {
  return ticket.investigationId
    ? `/investigations/${ticket.investigationId}`
    : `/tickets/${ticket.id}`;
}

function pickRecommended(tickets: TicketSummary[]): TicketSummary | null {
  const unresolved = tickets.filter((ticket) => ticket.status !== "resolved");
  const fresh = unresolved.filter((ticket) => !OPEN_STATUSES.has(ticket.status));
  const pool = fresh.length > 0 ? fresh : unresolved;
  if (pool.length === 0) return null;
  return [...pool].sort(
    (a, b) => difficultyRank(a.difficulty) - difficultyRank(b.difficulty) || a.id.localeCompare(b.id),
  )[0];
}

function Panel({
  title,
  meta,
  children,
}: {
  title: string;
  meta?: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="border border-border bg-surface">
      <header className="flex items-center justify-between gap-3 border-b border-border px-3 py-2">
        <h2 className="font-mono text-[11px] uppercase tracking-wide text-ink-faint">{title}</h2>
        {meta && <div className="font-mono text-[11px] text-ink-faint">{meta}</div>}
      </header>
      {children}
    </section>
  );
}

function ProgressPanel({ state }: { state: AsyncState<PlayerProfile> }) {
  if (state.status !== "success") {
    return (
      <Panel title="Your progress">
        <p className="px-3 py-4 font-mono text-xs text-ink-faint">
          {state.status === "loading" ? "loading…" : "progress unavailable"}
        </p>
      </Panel>
    );
  }

  const profile = state.data;
  const intoLevel = profile.totalXp % XP_PER_LEVEL;
  const topSkills = [...profile.skills].sort((a, b) => b.masteryPct - a.masteryPct).slice(0, 3);

  return (
    <Panel
      title="Your progress"
      meta={
        <Link to="/profile" className="hover:text-ink">
          full profile →
        </Link>
      }
    >
      <div className="px-3 py-3">
        <div className="flex items-baseline gap-2 font-mono">
          <span className="text-2xl text-ink">Lvl {profile.level}</span>
          <span className="text-ink-faint">·</span>
          <span className="text-sm text-ink-dim">{profile.totalXp.toLocaleString()} XP</span>
        </div>
        <div className="mt-2 h-1 bg-elevated">
          <div
            className="h-full bg-accent"
            style={{ width: `${(intoLevel / XP_PER_LEVEL) * 100}%` }}
          />
        </div>
        <p className="mt-1 font-mono text-[11px] text-ink-faint">
          {XP_PER_LEVEL - intoLevel} XP to level {profile.level + 1}
        </p>

        <div className="mt-4 flex flex-col gap-2">
          {topSkills.length === 0 ? (
            <p className="text-xs text-ink-faint">
              Resolve an investigation to start building skill mastery.
            </p>
          ) : (
            topSkills.map((skill) => (
              <SkillBar key={skill.name} name={skill.name} masteryPct={skill.masteryPct} compact />
            ))
          )}
        </div>
      </div>
    </Panel>
  );
}

export function Dashboard() {
  const navigate = useNavigate();
  const { username } = useAuth();
  const ticketsState = useAsync(fetchTickets, []);
  const profileState = useAsync(fetchProfile, []);

  return (
    <div className="flex h-full flex-col">
      <TopBar crumbs="Home" />
      <div className="flex-1 overflow-auto">
        <div className="mx-auto max-w-5xl px-6 py-8">
          <AsyncBoundary state={ticketsState}>
            {(tickets) => {
              const open = tickets.filter((ticket) => OPEN_STATUSES.has(ticket.status));
              const queue = [...tickets]
                .filter((ticket) => !OPEN_STATUSES.has(ticket.status))
                .sort(
                  (a, b) =>
                    Number(a.status === "resolved") - Number(b.status === "resolved") ||
                    difficultyRank(a.difficulty) - difficultyRank(b.difficulty) ||
                    a.id.localeCompare(b.id),
                );
              const resolvedCount = tickets.filter((t) => t.status === "resolved").length;
              const recommended = pickRecommended(tickets);

              return (
                <>
                  <header className="mb-6">
                    <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-ink-faint">
                      Nexus Engineering
                    </p>
                    <h1 className="mt-1 text-2xl font-medium text-ink">
                      {greeting(new Date())}
                      {username ? `, ${username}` : ""}
                    </h1>
                    <p className="mt-1 font-mono text-xs text-ink-dim">
                      {open.length} open · {resolvedCount} resolved · {queue.length} in the queue
                    </p>
                  </header>

                  <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_18rem]">
                    <div className="flex min-w-0 flex-col gap-4">
                      <Panel title="Open investigations" meta={String(open.length)}>
                        {open.length === 0 ? (
                          <p className="px-3 py-4 text-sm text-ink-faint">
                            Nothing in flight. Pick up a ticket from the queue.
                          </p>
                        ) : (
                          <ul>
                            {open.map((ticket) => (
                              <li key={ticket.id} className="border-b border-border/60 last:border-b-0">
                                <Link
                                  to={ticketHref(ticket)}
                                  className="flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2.5 hover:bg-elevated"
                                >
                                  <span className="w-20 shrink-0 font-mono text-xs text-ink-faint">
                                    {ticketRef(ticket.id)}
                                  </span>
                                  <span className="order-last w-full min-w-0 text-sm text-ink sm:order-none sm:w-auto sm:flex-1 sm:truncate">
                                    {ticket.title}
                                  </span>
                                  <StatusPill status={ticket.status} />
                                </Link>
                              </li>
                            ))}
                          </ul>
                        )}
                      </Panel>

                      <Panel title="Ticket queue" meta={String(queue.length)}>
                        {queue.length === 0 ? (
                          <p className="px-3 py-4 text-sm text-ink-faint">No tickets available.</p>
                        ) : (
                          <table className="w-full border-collapse text-left text-sm">
                            <tbody>
                              {queue.map((ticket) => (
                                <tr
                                  key={ticket.id}
                                  onClick={() => navigate(ticketHref(ticket))}
                                  className="cursor-pointer border-b border-border/60 last:border-b-0 hover:bg-elevated"
                                >
                                  <td className="w-20 whitespace-nowrap px-3 py-2.5 font-mono text-xs text-ink-faint">
                                    {ticketRef(ticket.id)}
                                  </td>
                                  <td className="px-3 py-2.5 text-ink">{ticket.title}</td>
                                  <td className="hidden px-3 py-2.5 sm:table-cell">
                                    <SeverityPill severity={ticket.severity} />
                                  </td>
                                  <td className="hidden px-3 py-2.5 font-mono text-xs uppercase text-ink-dim sm:table-cell">
                                    {ticket.difficulty}
                                  </td>
                                  <td className="px-3 py-2.5">
                                    <StatusPill status={ticket.status} />
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        )}
                      </Panel>
                    </div>

                    <div className="flex min-w-0 flex-col gap-4">
                      <Panel title="Recommended next">
                        {recommended === null ? (
                          <p className="px-3 py-4 text-sm text-ink-faint">
                            Everything is resolved. Nice.
                          </p>
                        ) : (
                          <div className="px-3 py-3">
                            <div className="mb-2 flex items-center gap-2">
                              <SeverityPill severity={recommended.severity} />
                              <span className="font-mono text-xs text-ink-faint">
                                {ticketRef(recommended.id)}
                              </span>
                            </div>
                            <p className="text-sm leading-snug text-ink">{recommended.title}</p>
                            <p className="mt-1 font-mono text-[11px] uppercase tracking-wide text-ink-dim">
                              {recommended.difficulty}
                            </p>
                            <Link
                              to={ticketHref(recommended)}
                              className="mt-3 block border border-accent bg-accent-dim/20 px-3 py-1.5 text-center font-mono text-xs text-ink hover:bg-accent-dim/40"
                            >
                              Open ticket
                            </Link>
                          </div>
                        )}
                      </Panel>

                      <ProgressPanel state={profileState} />
                    </div>
                  </div>
                </>
              );
            }}
          </AsyncBoundary>
        </div>
      </div>
    </div>
  );
}
