interface SkillBarProps {
  name: string;
  masteryPct: number;
  compact?: boolean;
}

export function SkillBar({ name, masteryPct, compact = false }: SkillBarProps) {
  const pct = Math.max(0, Math.min(100, masteryPct));
  return (
    <div className={compact ? "flex items-center gap-2" : "flex items-center gap-3"}>
      <span
        className={`shrink-0 truncate text-ink-dim ${compact ? "w-28 text-xs" : "w-40 text-sm"}`}
      >
        {name}
      </span>
      <div className="h-1.5 flex-1 bg-elevated">
        <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
      </div>
      <span
        className={`shrink-0 text-right font-mono text-ink ${compact ? "w-8 text-[11px]" : "w-10 text-xs"}`}
      >
        {pct}%
      </span>
    </div>
  );
}
