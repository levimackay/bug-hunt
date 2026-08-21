import { useRef, useState } from "react";
import { execCommand } from "../../api/investigations";
import type { ExecResult } from "../../api/types";
import { errorMessage } from "../../hooks/useAsync";

interface TerminalProps {
  investigationId: string;
}

const ALLOWED_COMMANDS = ["pytest", "python", "git", "ls", "cat", "grep", "find", "diff"];

interface HistoryEntry {
  input: string;
  result?: ExecResult;
  clientError?: string;
}

// Naive whitespace split — matches the sandbox's argv contract (no shell
// involved) and is enough for this milestone's commands; quoted arguments
// with embedded spaces are not supported and are out of scope here.
function parseArgv(input: string): string[] {
  return input.trim().split(/\s+/).filter(Boolean);
}

export function Terminal({ investigationId }: TerminalProps) {
  const [input, setInput] = useState("");
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [running, setRunning] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  async function runCommand(e: React.FormEvent) {
    e.preventDefault();
    const argv = parseArgv(input);
    if (argv.length === 0) return;
    setInput("");

    if (!ALLOWED_COMMANDS.includes(argv[0])) {
      setHistory((h) => [
        ...h,
        { input, clientError: `"${argv[0]}" is not allowlisted. Allowed: ${ALLOWED_COMMANDS.join(", ")}` },
      ]);
      queueScroll();
      return;
    }

    setRunning(true);
    try {
      const result = await execCommand(investigationId, argv);
      setHistory((h) => [...h, { input, result }]);
    } catch (error) {
      setHistory((h) => [...h, { input, clientError: errorMessage(error) }]);
    } finally {
      setRunning(false);
      queueScroll();
    }
  }

  function queueScroll() {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
    });
  }

  return (
    <div className="flex h-full flex-col">
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-3 py-2 font-mono text-xs">
        {history.length === 0 && (
          <p className="text-ink-faint">Allowlisted: {ALLOWED_COMMANDS.join(", ")}</p>
        )}
        {history.map((entry, i) => (
          <div key={i} className="mb-2">
            <div className="text-ink">
              <span className="text-accent">$</span> {entry.input}
            </div>
            {entry.clientError && <div className="text-diff-remove">{entry.clientError}</div>}
            {entry.result && (
              <>
                {entry.result.stdout && (
                  <pre className="whitespace-pre-wrap text-ink-dim">{entry.result.stdout}</pre>
                )}
                {entry.result.stderr && (
                  <pre className="whitespace-pre-wrap text-sev-medium">{entry.result.stderr}</pre>
                )}
                <div className={entry.result.exitCode === 0 ? "text-diff-add" : "text-diff-remove"}>
                  exit {entry.result.exitCode}
                </div>
              </>
            )}
          </div>
        ))}
      </div>
      <form onSubmit={runCommand} className="flex items-center gap-2 border-t border-border px-3 py-2">
        <span className="font-mono text-xs text-accent">$</span>
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={running}
          placeholder="pytest tests/"
          className="flex-1 bg-transparent font-mono text-xs text-ink outline-none placeholder:text-ink-faint disabled:opacity-50"
        />
      </form>
    </div>
  );
}
