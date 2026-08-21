import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchFileTree } from "../api/investigations";
import { useAsync } from "../hooks/useAsync";
import { AsyncBoundary } from "../components/AsyncBoundary";
import { TopBar } from "../components/TopBar";
import { FileTree } from "./workspace/FileTree";
import { Editor } from "./workspace/Editor";
import { Terminal } from "./workspace/Terminal";
import { GitPanel } from "./workspace/GitPanel";
import { HintsPanel } from "./workspace/HintsPanel";

type BottomTab = "terminal" | "git";

export function Workspace() {
  const { investigationId = "" } = useParams();
  const treeState = useAsync(() => fetchFileTree(investigationId), [investigationId]);
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [bottomTab, setBottomTab] = useState<BottomTab>("terminal");

  return (
    <div className="flex h-full flex-col">
      <TopBar
        crumbs={
          <div className="flex w-full items-center justify-between">
            <span className="font-mono text-xs">investigation {investigationId}</span>
            <Link
              to={`/investigations/${investigationId}/submit`}
              className="border border-accent bg-accent-dim/20 px-3 py-1 font-mono text-xs text-ink hover:bg-accent-dim/40"
            >
              Submit
            </Link>
          </div>
        }
      />
      <div className="flex flex-1 overflow-hidden">
        <div className="w-56 shrink-0">
          <AsyncBoundary state={treeState}>
            {(nodes) => <FileTree nodes={nodes} selectedPath={selectedPath} onSelect={setSelectedPath} />}
          </AsyncBoundary>
        </div>

        <div className="flex min-w-0 flex-1 flex-col">
          <div className="min-h-0 flex-1">
            <Editor investigationId={investigationId} path={selectedPath} />
          </div>
          <div className="flex h-72 shrink-0 flex-col border-t border-border">
            <div className="flex h-8 shrink-0 border-b border-border bg-surface">
              <TabButton active={bottomTab === "terminal"} onClick={() => setBottomTab("terminal")}>
                Terminal
              </TabButton>
              <TabButton active={bottomTab === "git"} onClick={() => setBottomTab("git")}>
                Git
              </TabButton>
            </div>
            <div className="min-h-0 flex-1">
              {bottomTab === "terminal" ? (
                <Terminal investigationId={investigationId} />
              ) : (
                <GitPanel investigationId={investigationId} />
              )}
            </div>
          </div>
        </div>

        <div className="w-72 shrink-0 border-l border-border">
          <HintsPanel investigationId={investigationId} />
        </div>
      </div>
    </div>
  );
}

function TabButton({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`border-r border-border px-3 font-mono text-xs uppercase tracking-wide ${
        active ? "bg-elevated text-ink" : "text-ink-faint hover:text-ink-dim"
      }`}
    >
      {children}
    </button>
  );
}
