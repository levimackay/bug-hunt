import { ApiError, getJson, getTextish, postJson, putJson } from "./http";
import { normalizeFileTree } from "./files";
import type {
  CommitSummary,
  CreateInvestigationResult,
  ExecResult,
  FileNode,
  Hint,
  PrView,
  ReviewComment,
  Score,
  SubmitPayload,
  SubmitResult,
} from "./types";

type RawRecord = Record<string, unknown>;

function str(raw: RawRecord, keys: string[], fallback = ""): string {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === "string") return value;
    if (typeof value === "number") return String(value);
  }
  return fallback;
}

function num(raw: RawRecord, keys: string[], fallback = 0): number {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === "number") return value;
  }
  return fallback;
}

export async function createInvestigation(scenarioId: string): Promise<CreateInvestigationResult> {
  const raw = await postJson<RawRecord>("/investigations", { scenario_id: scenarioId });
  const status = str(raw, ["status"]);
  return {
    investigationId: str(raw, ["investigation_id", "investigationId", "id"]),
    status: status || undefined,
  };
}

export async function fetchFileTree(investigationId: string): Promise<FileNode[]> {
  const raw = await getJson<unknown>(`/investigations/${investigationId}/files`);
  const list = Array.isArray(raw) ? raw : (raw as RawRecord)?.["files"];
  return normalizeFileTree(list);
}

export async function fetchFileContent(investigationId: string, path: string): Promise<string> {
  return getTextish(`/investigations/${investigationId}/files/${encodeURIComponent(path)}`);
}

export async function writeFileContent(
  investigationId: string,
  path: string,
  content: string,
): Promise<void> {
  await putJson(`/investigations/${investigationId}/files/${encodeURIComponent(path)}`, { content });
}

export async function execCommand(investigationId: string, argv: string[]): Promise<ExecResult> {
  const raw = await postJson<RawRecord>(`/investigations/${investigationId}/exec`, { argv });
  return {
    argv,
    stdout: str(raw, ["stdout"]),
    stderr: str(raw, ["stderr"]),
    exitCode: Number(raw["exit_code"] ?? raw["exitCode"] ?? raw["returncode"] ?? 0),
  };
}

function normalizeCommit(raw: RawRecord): CommitSummary {
  return {
    sha: str(raw, ["sha", "hash", "commit"]),
    author: str(raw, ["author", "author_name"]),
    message: str(raw, ["message", "summary", "subject"]),
    date: str(raw, ["date", "timestamp", "authored_date"]),
  };
}

export async function fetchGitLog(investigationId: string): Promise<CommitSummary[]> {
  const raw = await getJson<unknown>(`/investigations/${investigationId}/git/log`);
  const list = Array.isArray(raw) ? raw : ((raw as RawRecord)?.["commits"] as unknown[]) ?? [];
  return (list as RawRecord[]).map(normalizeCommit);
}

export async function fetchGitDiff(investigationId: string, sha: string): Promise<string> {
  return getTextish(`/investigations/${investigationId}/git/diff/${sha}`);
}

// Explanation fields are composed into markdown sections rather than sent
// individually, since the API contract (per BUILD_SPEC review_criteria) takes
// a single pr_description string. Backend can re-split on these headers if it
// needs the fields structured; documented in the frontend build report.
function composeDescription(payload: SubmitPayload): string {
  return [
    "## What was broken",
    payload.whatWasBroken.trim(),
    "",
    "## Why",
    payload.why.trim(),
    "",
    "## What changed",
    payload.whatChanged.trim(),
    "",
    "## How verified",
    payload.howVerified.trim(),
  ].join("\n");
}

export async function submitInvestigation(
  investigationId: string,
  payload: SubmitPayload,
): Promise<SubmitResult> {
  const raw = await postJson<RawRecord>(`/investigations/${investigationId}/submit`, {
    pr_title: payload.prTitle,
    pr_description: composeDescription(payload),
  });
  return {
    passed: Boolean(raw["passed"] ?? raw["pass"] ?? false),
    prId: str(raw, ["pr_id", "prId"]),
    message: str(raw, ["message"]),
  };
}

export async function fetchPr(investigationId: string): Promise<PrView> {
  const raw = await getJson<RawRecord>(`/investigations/${investigationId}/pr`);
  const files = raw["files"];
  return {
    title: str(raw, ["title"]),
    description: str(raw, ["description"]),
    diff: str(raw, ["diff"]),
    files: Array.isArray(files) ? files.map(String) : [],
  };
}

function normalizeReviewComment(raw: RawRecord): ReviewComment {
  return {
    author: str(raw, ["author"]),
    body: str(raw, ["body", "comment"]),
    resolved: Boolean(raw["resolved"] ?? false),
  };
}

export async function fetchReview(investigationId: string): Promise<ReviewComment[]> {
  const raw = await getJson<unknown>(`/investigations/${investigationId}/review`);
  const list = Array.isArray(raw) ? raw : ((raw as RawRecord)?.["comments"] as unknown[]) ?? [];
  return (list as RawRecord[]).map(normalizeReviewComment);
}

export async function revealNextHint(investigationId: string): Promise<Hint> {
  const raw = await postJson<RawRecord>(`/investigations/${investigationId}/hints/next`, {});
  return {
    index: Number(raw["index"] ?? raw["hint_index"] ?? 0),
    text: str(raw, ["text", "hint"]),
    costXp: Number(raw["cost_xp"] ?? raw["costXp"] ?? 0),
  };
}

function normalizeScore(raw: RawRecord): Score {
  return {
    rootCause: num(raw, ["root_cause", "rootCause"]),
    fix: num(raw, ["fix"]),
    testing: num(raw, ["testing"]),
    investigation: num(raw, ["investigation"]),
    codeQuality: num(raw, ["code_quality", "codeQuality"]),
    overall: num(raw, ["overall"]),
  };
}

// null means "not resolved yet" (404), distinct from a real fetch error, so
// callers can render a plain not-scored-yet message instead of an error state.
export async function fetchScore(investigationId: string): Promise<Score | null> {
  try {
    const raw = await getJson<RawRecord>(`/investigations/${investigationId}/score`);
    return normalizeScore(raw);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) return null;
    throw error;
  }
}
