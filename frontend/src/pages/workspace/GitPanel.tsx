import { useState } from "react";
import { fetchGitDiff, fetchGitLog } from "../../api/investigations";
import { useAsync, errorMessage } from "../../hooks/useAsync";
import { AsyncBoundary } from "../../components/AsyncBoundary";
import { DiffView } from "../../components/DiffView";

interface GitPanelProps {
  investigationId: string;
}

export function GitPanel({ investigationId }: GitPanelProps) {
  const logState = useAsync(() => fetchGitLog(investigationId), [investigationId]);
  const [selectedSha, setSelectedSha] = useState<string | null>(null);
  const [diff, setDiff] = useState<string | null>(null);
  const [diffError, setDiffError] = useState<string | null>(null);

  async function selectCommit(sha: string) {
    setSelectedSha(sha);
    setDiff(null);
    setDiffError(null);
    try {
      const text = await fetchGitDiff(investigationId, sha);
      setDiff(text);
    } catch (error) {
      setDiffError(errorMessage(error));
    }
  }

  return (
    <div className="flex h-full">
      <div className="w-64 shrink-0 overflow-y-auto border-r border-border">
        <AsyncBoundary state={logState}>
          {(commits) => (
            <ul>
              {commits.map((commit) => (
                <li key={commit.sha}>
                  <button
                    type="button"
                    onClick={() => selectCommit(commit.sha)}
                    className={`block w-full border-b border-border/60 px-3 py-2 text-left ${
                      selectedSha === commit.sha ? "bg-elevated" : "hover:bg-elevated"
                    }`}
                  >
                    <div className="truncate text-xs text-ink">{commit.message}</div>
                    <div className="mt-0.5 font-mono text-[11px] text-ink-faint">
                      {commit.sha.slice(0, 7)} · {commit.author}
                    </div>
                  </button>
                </li>
              ))}
              {commits.length === 0 && (
                <li className="px-3 py-4 text-xs text-ink-faint">No commits.</li>
              )}
            </ul>
          )}
        </AsyncBoundary>
      </div>
      <div className="flex-1 overflow-auto">
        {!selectedSha && (
          <div className="p-4 text-sm text-ink-faint">Select a commit to view its diff.</div>
        )}
        {diffError && <div className="p-4 text-sm text-diff-remove">{diffError}</div>}
        {selectedSha && diff !== null && <DiffView diff={diff} />}
        {selectedSha && diff === null && !diffError && (
          <div className="p-4 font-mono text-sm text-ink-faint">loading diff…</div>
        )}
      </div>
    </div>
  );
}
