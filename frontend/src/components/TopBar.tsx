import { Link } from "react-router-dom";
import type { ReactNode } from "react";

interface TopBarProps {
  crumbs?: ReactNode;
}

export function TopBar({ crumbs }: TopBarProps) {
  return (
    <header className="flex h-11 shrink-0 items-center gap-3 border-b border-border bg-surface px-4">
      <Link to="/" className="font-mono text-[13px] font-medium tracking-tight text-ink">
        bug<span className="text-accent">hunt</span>
      </Link>
      {crumbs && (
        <>
          <span className="text-ink-faint">/</span>
          <div className="flex items-center gap-2 truncate text-[13px] text-ink-dim">{crumbs}</div>
        </>
      )}
    </header>
  );
}
