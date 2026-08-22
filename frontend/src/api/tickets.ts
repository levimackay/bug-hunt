import { getJson } from "./http";
import type { SlackMessage, TicketDetail, TicketSummary } from "./types";

type RawRecord = Record<string, unknown>;

function str(raw: RawRecord, keys: string[], fallback = ""): string {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === "string") return value;
  }
  return fallback;
}

function normalizeSummary(raw: RawRecord): TicketSummary {
  const investigationId = str(raw, ["investigation_id", "investigationId"]);
  return {
    id: str(raw, ["id", "scenario_id"]),
    title: str(raw, ["title"]),
    severity: str(raw, ["severity"]),
    difficulty: str(raw, ["difficulty"]),
    status: str(raw, ["status"], "not_started"),
    investigationId: investigationId || undefined,
  };
}

function normalizeSlackThread(raw: unknown): SlackMessage[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((entry) => {
    const record = (entry ?? {}) as RawRecord;
    return {
      author: str(record, ["author"]),
      body: str(record, ["body", "text"]),
    };
  });
}

function normalizeDetail(raw: RawRecord): TicketDetail {
  const ticket = (raw["ticket"] as RawRecord | undefined) ?? raw;
  return {
    ...normalizeSummary(raw),
    reporter: str(ticket, ["reporter"], "Unknown"),
    body: str(ticket, ["body"]),
    slackThread: normalizeSlackThread(ticket["slack_thread"] ?? ticket["slackThread"]),
    repoName: str(raw, ["repo_name", "entry_service", "repoName"], "repo"),
  };
}

export async function fetchTickets(): Promise<TicketSummary[]> {
  const raw = await getJson<unknown>("/tickets");
  const list = Array.isArray(raw) ? raw : ((raw as RawRecord)?.["tickets"] as unknown[]) ?? [];
  return (list as RawRecord[]).map(normalizeSummary);
}

export async function fetchTicketDetail(scenarioId: string): Promise<TicketDetail> {
  const raw = await getJson<RawRecord>(`/tickets/${scenarioId}`);
  return normalizeDetail(raw);
}
