export type TicketStatus = "not_started" | "in_progress" | "resolved" | (string & {});

export interface TicketSummary {
  id: string;
  title: string;
  severity: string;
  difficulty: string;
  status: TicketStatus;
}

export interface SlackMessage {
  author: string;
  body: string;
}

export interface TicketDetail extends TicketSummary {
  reporter: string;
  body: string;
  slackThread: SlackMessage[];
  repoName: string;
}

export interface CreateInvestigationResult {
  investigationId: string;
  status?: string;
}

export type FileKind = "file" | "dir";

export interface FileNode {
  name: string;
  path: string;
  type: FileKind;
  children?: FileNode[];
}

export interface ExecResult {
  argv: string[];
  stdout: string;
  stderr: string;
  exitCode: number;
}

export interface CommitSummary {
  sha: string;
  author: string;
  message: string;
  date: string;
}

export interface SubmitPayload {
  prTitle: string;
  whatWasBroken: string;
  why: string;
  whatChanged: string;
  howVerified: string;
}

export interface SubmitResult {
  passed: boolean;
  prId: string;
  message: string;
}

export interface PrView {
  title: string;
  description: string;
  diff: string;
  files: string[];
}

export interface ReviewComment {
  author: string;
  body: string;
  resolved: boolean;
}

export interface Hint {
  index: number;
  text: string;
  costXp: number;
}

export interface Score {
  rootCause: number;
  fix: number;
  testing: number;
  investigation: number;
  codeQuality: number;
  overall: number;
}

export interface SkillProgress {
  name: string;
  xp: number;
  masteryPct: number;
}

export interface PlayerProfile {
  totalXp: number;
  level: number;
  skills: SkillProgress[];
}
