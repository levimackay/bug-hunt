import { useParams } from "react-router-dom";
import { fetchReview } from "../api/investigations";
import { useAsync } from "../hooks/useAsync";
import { AsyncBoundary } from "../components/AsyncBoundary";
import { TopBar } from "../components/TopBar";

export function ReviewView() {
  const { investigationId = "" } = useParams();
  const state = useAsync(() => fetchReview(investigationId), [investigationId]);

  return (
    <div className="flex h-full flex-col">
      <TopBar crumbs="Review" />
      <div className="flex-1 overflow-auto">
        <AsyncBoundary state={state}>
          {(comments) => (
            <div className="mx-auto max-w-2xl px-6 py-8">
              <h1 className="mb-6 text-xl font-medium text-ink">Review comments</h1>
              {comments.length === 0 && <p className="text-sm text-ink-faint">No review comments yet.</p>}
              <ul className="flex flex-col gap-3">
                {comments.map((comment, i) => (
                  <li key={i} className="border border-border bg-surface p-3">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="font-medium text-sm text-ink">{comment.author}</span>
                      <span
                        className={`font-mono text-[11px] uppercase ${
                          comment.resolved ? "text-diff-add" : "text-sev-medium"
                        }`}
                      >
                        {comment.resolved ? "resolved" : "open"}
                      </span>
                    </div>
                    <p className="text-sm text-ink-dim">{comment.body}</p>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </AsyncBoundary>
      </div>
    </div>
  );
}
