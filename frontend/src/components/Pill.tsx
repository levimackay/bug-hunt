interface PillProps {
  label: string;
  color: string;
}

export function Pill({ label, color }: PillProps) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-sm border border-border px-2 py-0.5 font-mono text-[11px] uppercase tracking-wide text-ink-dim"
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
      {label}
    </span>
  );
}

const SEVERITY_COLOR: Record<string, string> = {
  low: "var(--color-sev-low)",
  medium: "var(--color-sev-medium)",
  high: "var(--color-sev-high)",
  critical: "var(--color-sev-critical)",
};

export function SeverityPill({ severity }: { severity: string }) {
  const color = SEVERITY_COLOR[severity.toLowerCase()] ?? "var(--color-ink-faint)";
  return <Pill label={severity} color={color} />;
}

const STATUS_COLOR: Record<string, string> = {
  not_started: "var(--color-status-not-started)",
  in_progress: "var(--color-status-in-progress)",
  resolved: "var(--color-status-resolved)",
};

const STATUS_LABEL: Record<string, string> = {
  not_started: "Not started",
  in_progress: "In progress",
  resolved: "Resolved",
};

export function StatusPill({ status }: { status: string }) {
  const key = status.toLowerCase();
  const color = STATUS_COLOR[key] ?? "var(--color-ink-faint)";
  const label = STATUS_LABEL[key] ?? status.replace(/_/g, " ");
  return <Pill label={label} color={color} />;
}
