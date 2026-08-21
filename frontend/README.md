# Bug Hunt — Frontend

Vite + React + TypeScript + Tailwind CSS + Monaco Editor client for the Bug Hunt
debugging-practice simulator. Talks to the FastAPI backend under `/api`
(proxied to `http://localhost:8000` in dev — see `vite.config.ts`).

## Scripts

- `npm run dev` — start the dev server
- `npm run build` — type-check (`tsc -b`) and produce a production build
- `npm run lint` — ESLint
- `npm run preview` — preview the production build

## Structure

- `src/api/` — typed REST client, one module per resource (`tickets`, `investigations`, `files`), each normalizing whatever shape the backend returns into stable frontend types (see the assumptions noted inline where BUILD_SPEC.md is ambiguous).
- `src/pages/` — one file per route: `Dashboard`, `TicketDetail`, `Workspace`, `Submit`, `PrView`, `ReviewView`.
- `src/pages/workspace/` — the IDE view's subcomponents: `FileTree`, `Editor`, `Terminal`, `GitPanel`, `HintsPanel`.
- `src/components/` — shared presentational pieces (`DiffView`, `Pill`, `TopBar`, `AsyncBoundary`).
- `src/hooks/useAsync.ts` — small fetch-on-mount hook shared by every page that loads data.

Monaco is loaded via `@monaco-editor/react`'s default CDN loader rather than
self-hosted — self-hosting via Vite's `?worker` imports did not resolve
cleanly under this project's Vite/Rolldown toolchain, and bundling all of
`monaco-editor`'s languages inflates the build by ~4MB. Revisit if offline dev
without network access to the CDN becomes a requirement.
