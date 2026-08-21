import { useEffect, useRef, useState } from "react";
import MonacoEditor from "@monaco-editor/react";
import { fetchFileContent, writeFileContent } from "../../api/investigations";
import { errorMessage } from "../../hooks/useAsync";

interface EditorProps {
  investigationId: string;
  path: string | null;
}

type SaveState = "idle" | "pending" | "saving" | "saved" | "error";

const LANGUAGE_BY_EXT: Record<string, string> = {
  py: "python",
  js: "javascript",
  jsx: "javascript",
  ts: "typescript",
  tsx: "typescript",
  json: "json",
  yaml: "yaml",
  yml: "yaml",
  md: "markdown",
  toml: "ini",
  cfg: "ini",
  sh: "shell",
};

function languageFor(path: string): string {
  const ext = path.split(".").pop() ?? "";
  return LANGUAGE_BY_EXT[ext] ?? "plaintext";
}

// 800ms balances "feels live" against hammering PUT on every keystroke —
// long enough to cover a typical pause between edits, short enough that a
// tab switch or exec run rarely races an unsaved change.
const AUTOSAVE_DELAY_MS = 800;

export function Editor({ investigationId, path }: EditorProps) {
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [error, setError] = useState<string | null>(null);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const latestContent = useRef<string>("");

  useEffect(() => {
    if (!path) return;
    let cancelled = false;
    setLoading(true);
    setSaveState("idle");
    fetchFileContent(investigationId, path)
      .then((text) => {
        if (cancelled) return;
        setContent(text);
        latestContent.current = text;
      })
      .catch((err: unknown) => {
        if (!cancelled) setError(errorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [investigationId, path]);

  function scheduleSave(next: string) {
    latestContent.current = next;
    setSaveState("pending");
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      if (!path) return;
      setSaveState("saving");
      writeFileContent(investigationId, path, latestContent.current)
        .then(() => setSaveState("saved"))
        .catch((err: unknown) => {
          setError(errorMessage(err));
          setSaveState("error");
        });
    }, AUTOSAVE_DELAY_MS);
  }

  useEffect(() => {
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, []);

  if (!path) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-ink-faint">
        Select a file to view its contents.
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-8 shrink-0 items-center justify-between border-b border-border bg-surface px-3">
        <span className="font-mono text-xs text-ink-dim">{path}</span>
        <SaveIndicator state={saveState} />
      </div>
      <div className="flex-1">
        {loading ? (
          <div className="p-4 font-mono text-sm text-ink-faint">loading…</div>
        ) : (
          <MonacoEditor
            height="100%"
            theme="vs-dark"
            language={languageFor(path)}
            value={content}
            onChange={(value) => {
              const next = value ?? "";
              setContent(next);
              scheduleSave(next);
            }}
            options={{
              fontFamily: "IBM Plex Mono, monospace",
              fontSize: 13,
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
            }}
          />
        )}
      </div>
      {error && <div className="border-t border-border px-3 py-1 text-xs text-diff-remove">{error}</div>}
    </div>
  );
}

function SaveIndicator({ state }: { state: SaveState }) {
  const label: Record<SaveState, string> = {
    idle: "",
    pending: "unsaved",
    saving: "saving…",
    saved: "saved",
    error: "save failed",
  };
  const color: Record<SaveState, string> = {
    idle: "text-ink-faint",
    pending: "text-sev-medium",
    saving: "text-ink-dim",
    saved: "text-diff-add",
    error: "text-diff-remove",
  };
  if (!label[state]) return null;
  return <span className={`font-mono text-[11px] ${color[state]}`}>{label[state]}</span>;
}
