import type { ReactNode } from "react";
import type { AsyncState } from "../hooks/useAsync";
import { errorMessage } from "../hooks/useAsync";

interface AsyncBoundaryProps<T> {
  state: AsyncState<T>;
  children: (data: T) => ReactNode;
}

export function AsyncBoundary<T>({ state, children }: AsyncBoundaryProps<T>) {
  if (state.status === "loading") {
    return <div className="p-6 font-mono text-sm text-ink-faint">loading…</div>;
  }
  if (state.status === "error") {
    return (
      <div className="border border-diff-remove/40 bg-diff-remove-bg p-4 font-mono text-sm text-diff-remove">
        {errorMessage(state.error)}
      </div>
    );
  }
  return <>{children(state.data)}</>;
}
