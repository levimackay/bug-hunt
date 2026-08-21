import { getJson } from "./http";
import type { PlayerProfile, SkillProgress } from "./types";

type RawRecord = Record<string, unknown>;

function str(raw: RawRecord, keys: string[], fallback = ""): string {
  for (const key of keys) {
    const value = raw[key];
    if (typeof value === "string") return value;
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

function normalizeSkill(raw: unknown): SkillProgress {
  const record = (raw ?? {}) as RawRecord;
  return {
    name: str(record, ["name"]),
    xp: num(record, ["xp"]),
    masteryPct: num(record, ["mastery_pct", "masteryPct"]),
  };
}

function normalizeProfile(raw: RawRecord): PlayerProfile {
  const skills = raw["skills"];
  return {
    totalXp: num(raw, ["total_xp", "totalXp"]),
    level: num(raw, ["level"], 1),
    skills: Array.isArray(skills) ? skills.map(normalizeSkill) : [],
  };
}

export async function fetchProfile(): Promise<PlayerProfile> {
  const raw = await getJson<RawRecord>("/profile");
  return normalizeProfile(raw);
}
