# EduMind New Frontend Architecture

## Goals

The rebuilt frontend is a clean React application built with Vite, TypeScript, React Router, Zustand, Tailwind CSS v4, and local shadcn/ui-style components. The previous Vue implementation remains in `frontend-legacy` for rollback. During the React rewrite it was used as a read-only layout and information-architecture reference; the React implementation does not import Vue code, reuse Vue styles, or depend on legacy runtime assets.

The frontend talks to the API gateway only. It does not call internal microservices directly.

## Stack

- Runtime: React 19, Vite, TypeScript.
- UI: local shadcn/ui-style copy-paste primitives, Tailwind CSS v4 design tokens, Lucide icons.
- Routing: React Router route objects with compatibility redirects.
- State: Zustand stores for auth, role, UI, selected files, and live task state.
- Transport: typed `fetch` client, multipart upload helper, SSE progress helper.
- Testing: Vitest, React Testing Library, and Playwright smoke tests.

## Directory Layout

```text
frontend/
  src/
    components/
      ui/          # local shadcn/ui-style primitives and variants
      layout/      # app shell, navigation, responsive containers
      patterns/    # domain workflow blocks
    config/        # navigation, feature registry, environment
    lib/           # API client, SSE helper, utilities, errors
    pages/         # route-level screens
    router/        # route table, redirects, protected route wrapper
    stores/        # Zustand auth, workspace, and task modules
    styles/        # Tailwind entry and design tokens
    tests/         # unit, component, and e2e smoke tests
```

## Route Strategy

The new route tree separates authentication from the protected app shell:

- `/auth` handles login and registration.
- `/` opens the dashboard.
- `/files` opens the unified file library and RAG workspace.
- `/workspace/chat`, `/workspace/quiz`, `/workspace/paper`, `/workspace/lesson-plan`, `/workspace/slides`, `/workspace/smartnotes`, and `/workspace/podcast` host AI workflows.
- `/records` shows generated history and learning records.
- Historical URLs redirect into the new tree, including `/chat`, `/quiz`, `/teacher/paper`, `/teacher/file-library`, `/lesson-plan`, `/slides`, `/smart-notes`, and `/podcast`.
- Route-level pages are loaded through `React.lazy` and `Suspense` so the main bundle stays below Vite's large-chunk warning threshold.

## State Model

- `auth`: token, user, restore, login, register, logout.
- `workspace`: current role, selected material IDs, local file filters.
- `tasks`: current SSE/WebSocket task progress by kind and ID.
Theme state is stored directly by the app shell under a namespaced localStorage key. Workspace state that must survive reloads is persisted by Zustand, and auth token access is centralized so request headers remain consistent.

## API Strategy

`frontend/src/lib/api.ts` exposes typed functions:

- Auth: `login`, `register`, `logout`, `me`.
- Files/RAG: `listFiles`, `uploadFiles`, `deleteFile`, `rebuildFileIndex`, `ragSearch`.
- Chat: `listChats`, `getChat`.
- Generation: `startWorkflow` for chat, quiz, paper, lesson plan, slides, smart notes, and podcast.
- Records and feature hubs: `listRecords`, `wrongbookSummary`, `listFlashcards`, `listTeachingVideos`, `searchBilibili`, and related typed helpers.

Long-running endpoints return `events` URLs. The frontend subscribes with `subscribeTaskEvents`, updates `tasks`, and renders progress without depending on a persistent WebSocket connection.

## UI Architecture

Pages use the same high-level composition:

1. Route page loads data and owns page-specific mutation handlers.
2. Pattern components render workflow-specific blocks.
3. UI primitives provide accessibility, variants, focus states, and theme tokens.
4. Stores carry cross-page session, role, selected files, and task progress.

This keeps each page compact and makes feature workflows reusable across teacher and student contexts.

## Implemented Layout Contract

The new React frontend preserves the stable layout relationships users already know:

- App shell: persistent left sidebar, role switcher, account area, recent chats, and a compact top header.
- Workspace pages: left auxiliary column for learning/teaching folder and history, plus a main agent conversation area with bottom composer.
- File library: upload panel, file statistics, learning/teaching interaction folder, searchable file list, RAG probe, and preview sheet.
- Dashboard: project entry, teacher/student role switching, workflow cards, and project information tabs.
- Feature hubs: read-only record panels for history pages; text-input features such as Bilibili search use the agent conversation pattern.

## Design System

The design system is implemented with local shadcn/Radix primitives and Tailwind tokens:

- Color: low-saturation warm gray surfaces with brown-orange primary accents; deep blue is no longer used as the visual base.
- Radius: primitives use compact 5px to 6px radii, with fewer large rounded rectangle card surfaces.
- Interaction: all primary actions use native button semantics, visible focus rings, loading states, and icon+text labels.
- Responsiveness: desktop uses the persistent sidebar; mobile falls back to the shadcn Sheet sidebar and single-column page flows.
- Data display: tables, badges, tabs, selects, sheets, skeletons, alerts, and progress bars use shared shadcn components.
- Agent pattern: text-input workflows use a consistent message list, context panel, task progress block, and composer.

## Verification

- `npm --prefix frontend run lint` checks TypeScript/React rules with shadcn primitive export exceptions.
- `npm --prefix frontend run test` runs Vitest unit tests for environment, navigation, and workspace state.
- `npm --prefix frontend run build` runs TypeScript project references and Vite production build with route-level chunks.
- `npm --prefix frontend run test:e2e` starts Vite and runs Playwright against mocked API responses. It covers desktop dashboard/workspace/file RAG flows, captures screenshots, checks runtime console/page errors, and verifies the mobile file library has no horizontal overflow.
- `npm --prefix frontend-legacy run build` verifies the rollback frontend remains buildable.
- `start-edumind.ps1 -CheckOnly -NoPause -NoDockerWindow` validates the default legacy-frontend Docker compose path.
- `start-edumind-new-frontend.ps1 -CheckOnly -NoPause -NoDockerWindow` validates the new React frontend Docker compose path.

## Rollback

To return to the old frontend:

1. Move or delete the new `frontend`.
2. Move `frontend-legacy` back to `frontend`.
3. Rebuild the frontend Docker image.

No backend migration is required for rollback because the API gateway contract is preserved.
