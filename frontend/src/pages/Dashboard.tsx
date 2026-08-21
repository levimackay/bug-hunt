import { useNavigate } from "react-router-dom";
import { fetchTickets } from "../api/tickets";
import { useAsync } from "../hooks/useAsync";
import { AsyncBoundary } from "../components/AsyncBoundary";
import { SeverityPill, StatusPill } from "../components/Pill";
import { TopBar } from "../components/TopBar";

export function Dashboard() {
  const navigate = useNavigate();
  const state = useAsync(fetchTickets, []);

  return (
    <div className="flex h-full flex-col">
      <TopBar crumbs="Tickets" />
      <div className="flex-1 overflow-auto">
        <AsyncBoundary state={state}>
          {(tickets) => (
            <table className="w-full border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-border text-[11px] uppercase tracking-wide text-ink-faint">
                  <th className="px-4 py-2 font-mono font-normal">ID</th>
                  <th className="px-4 py-2 font-normal">Title</th>
                  <th className="px-4 py-2 font-normal">Severity</th>
                  <th className="px-4 py-2 font-normal">Difficulty</th>
                  <th className="px-4 py-2 font-normal">Status</th>
                </tr>
              </thead>
              <tbody>
                {tickets.map((ticket) => (
                  <tr
                    key={ticket.id}
                    onClick={() => navigate(`/tickets/${ticket.id}`)}
                    className="cursor-pointer border-b border-border/60 hover:bg-elevated"
                  >
                    <td className="px-4 py-2.5 font-mono text-xs text-ink-faint">{ticket.id}</td>
                    <td className="px-4 py-2.5 text-ink">{ticket.title}</td>
                    <td className="px-4 py-2.5">
                      <SeverityPill severity={ticket.severity} />
                    </td>
                    <td className="px-4 py-2.5 font-mono text-xs uppercase text-ink-dim">
                      {ticket.difficulty}
                    </td>
                    <td className="px-4 py-2.5">
                      <StatusPill status={ticket.status} />
                    </td>
                  </tr>
                ))}
                {tickets.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-ink-faint">
                      No tickets available.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          )}
        </AsyncBoundary>
      </div>
    </div>
  );
}
