interface DiffViewProps {
  diff: string;
}

type LineKind = "add" | "remove" | "hunk" | "meta" | "context";

function classify(line: string): LineKind {
  if (line.startsWith("@@")) return "hunk";
  if (line.startsWith("+++") || line.startsWith("---") || line.startsWith("diff ") || line.startsWith("index ")) {
    return "meta";
  }
  if (line.startsWith("+")) return "add";
  if (line.startsWith("-")) return "remove";
  return "context";
}

const LINE_STYLE: Record<LineKind, string> = {
  add: "bg-diff-add-bg text-diff-add",
  remove: "bg-diff-remove-bg text-diff-remove",
  hunk: "text-accent",
  meta: "text-ink-faint",
  context: "text-ink-dim",
};

export function DiffView({ diff }: DiffViewProps) {
  if (!diff.trim()) {
    return <p className="p-4 text-sm text-ink-faint">No diff to display.</p>;
  }
  const lines = diff.split("\n");
  return (
    <pre className="overflow-x-auto font-mono text-xs leading-5">
      {lines.map((line, i) => (
        <div key={i} className={`px-3 whitespace-pre ${LINE_STYLE[classify(line)]}`}>
          {line.length ? line : " "}
        </div>
      ))}
    </pre>
  );
}
