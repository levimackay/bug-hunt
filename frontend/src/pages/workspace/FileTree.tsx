import { useState } from "react";
import type { FileNode } from "../../api/types";

interface FileTreeProps {
  nodes: FileNode[];
  selectedPath: string | null;
  onSelect: (path: string) => void;
}

export function FileTree({ nodes, selectedPath, onSelect }: FileTreeProps) {
  return (
    <div className="flex h-full flex-col overflow-y-auto border-r border-border bg-surface">
      <h2 className="border-b border-border px-3 py-2 font-mono text-[11px] uppercase tracking-wide text-ink-faint">
        Files
      </h2>
      <div className="flex-1 py-1">
        {nodes.length === 0 && <p className="px-3 py-2 text-xs text-ink-faint">Empty workspace.</p>}
        {nodes.map((node) => (
          <TreeNode key={node.path} node={node} depth={0} selectedPath={selectedPath} onSelect={onSelect} />
        ))}
      </div>
    </div>
  );
}

function TreeNode({
  node,
  depth,
  selectedPath,
  onSelect,
}: {
  node: FileNode;
  depth: number;
  selectedPath: string | null;
  onSelect: (path: string) => void;
}) {
  const [open, setOpen] = useState(depth < 1);

  if (node.type === "dir") {
    return (
      <div>
        <button
          type="button"
          onClick={() => setOpen((v) => !v)}
          style={{ paddingLeft: `${depth * 12 + 12}px` }}
          className="flex w-full items-center gap-1.5 py-1 text-left font-mono text-xs text-ink-dim hover:bg-elevated"
        >
          <span className="w-3 text-ink-faint">{open ? "▾" : "▸"}</span>
          {node.name}
        </button>
        {open &&
          node.children?.map((child) => (
            <TreeNode key={child.path} node={child} depth={depth + 1} selectedPath={selectedPath} onSelect={onSelect} />
          ))}
      </div>
    );
  }

  const isSelected = node.path === selectedPath;
  return (
    <button
      type="button"
      onClick={() => onSelect(node.path)}
      style={{ paddingLeft: `${depth * 12 + 24}px` }}
      className={`block w-full truncate py-1 text-left font-mono text-xs ${
        isSelected ? "bg-elevated text-ink" : "text-ink-dim hover:bg-elevated hover:text-ink"
      }`}
    >
      {node.name}
    </button>
  );
}
