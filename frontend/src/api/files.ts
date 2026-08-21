import type { FileKind, FileNode } from "./types";

type RawRecord = Record<string, unknown>;

function looksLikeDir(path: string): boolean {
  return path.endsWith("/");
}

/**
 * BUILD_SPEC does not pin whether GET /investigations/{id}/files returns a
 * nested tree or a flat path list, so this accepts either:
 *   - nested: [{ name, path, type: "file"|"dir", children?: [...] }]
 *   - flat:   ["tests/test_upload.py", "app/main.py", ...] or
 *             [{ path: "...", type?: "file"|"dir" }]
 * and always produces the same FileNode[] tree the FileTree component reads.
 */
export function normalizeFileTree(raw: unknown): FileNode[] {
  if (!Array.isArray(raw)) return [];

  const looksNested = raw.some(
    (entry) => entry && typeof entry === "object" && "children" in (entry as RawRecord),
  );
  if (looksNested) {
    return (raw as RawRecord[]).map(normalizeNestedNode);
  }

  const paths: { path: string; type?: FileKind }[] = raw.map((entry) => {
    if (typeof entry === "string") {
      return { path: entry.replace(/\/$/, ""), type: looksLikeDir(entry) ? "dir" : undefined };
    }
    const record = entry as RawRecord;
    const path = String(record["path"] ?? record["name"] ?? "");
    const type = record["type"] as FileKind | undefined;
    return { path, type };
  });

  return buildTreeFromPaths(paths);
}

function normalizeNestedNode(raw: RawRecord): FileNode {
  const path = String(raw["path"] ?? raw["name"] ?? "");
  const name = String(raw["name"] ?? path.split("/").pop() ?? path);
  const children = raw["children"];
  const type: FileKind = Array.isArray(children) || raw["type"] === "dir" ? "dir" : "file";
  return {
    name,
    path,
    type,
    children: Array.isArray(children) ? children.map((c) => normalizeNestedNode(c as RawRecord)) : undefined,
  };
}

function buildTreeFromPaths(paths: { path: string; type?: FileKind }[]): FileNode[] {
  const root: FileNode = { name: "", path: "", type: "dir", children: [] };

  for (const { path, type } of paths) {
    const segments = path.split("/").filter(Boolean);
    let cursor = root;
    segments.forEach((segment, i) => {
      const isLast = i === segments.length - 1;
      const currentPath = segments.slice(0, i + 1).join("/");
      let next = cursor.children?.find((c) => c.name === segment);
      if (!next) {
        next = {
          name: segment,
          path: currentPath,
          type: isLast ? (type ?? "file") : "dir",
          children: isLast && type !== "dir" ? undefined : [],
        };
        cursor.children = cursor.children ?? [];
        cursor.children.push(next);
      }
      cursor = next;
    });
  }

  return sortTree(root.children ?? []);
}

function sortTree(nodes: FileNode[]): FileNode[] {
  const sorted = [...nodes].sort((a, b) => {
    if (a.type !== b.type) return a.type === "dir" ? -1 : 1;
    return a.name.localeCompare(b.name);
  });
  for (const node of sorted) {
    if (node.children) node.children = sortTree(node.children);
  }
  return sorted;
}
