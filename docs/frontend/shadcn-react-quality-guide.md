# EduMind React shadcn/ui Quality Guide

## Scope

This guide is the required reference before adding or changing the rebuilt React frontend. The previous Vue frontend is preserved in `frontend-legacy` for rollback. It may be read only to preserve stable product information architecture, route coverage, and sidebar entry names; it must not be used as a styling, visual design, interaction-detail, CSS, or implementation-code source for the new frontend.

## Official Resource Index

- shadcn/ui AI index: https://ui.shadcn.com/llms.txt
- shadcn/ui docs: https://ui.shadcn.com
- shadcn/ui themes: https://ui.shadcn.com/themes
- shadcn/ui blocks and examples: https://ui.shadcn.com/blocks
- Tailwind CSS v4 docs: https://tailwindcss.com/docs
- Radix UI primitives: https://www.radix-ui.com/primitives
- React Router docs: https://reactrouter.com
- Zustand docs: https://zustand-demo.pmnd.rs

The project uses the React shadcn/ui copy-paste model. Components in `frontend/src/components/ui` are local source files and may be extended only through typed variants, CSS variables, and composition.

## shadcn/ui v4 Source Index

The official v4 website is a full Next.js project. When implementing new UI, use these official paths as the reference map:

- Official registry index: https://ui.shadcn.com/r/index.json
- GitHub v4 app: https://github.com/shadcn-ui/ui/tree/main/apps/v4
- v4 app pages: `apps/v4/app`
- Blocks page: `apps/v4/app/(app)/blocks/page.tsx`
- Charts page: `apps/v4/app/(app)/charts/charts.tsx`
- Docs page: `apps/v4/app/(app)/docs/[[...slug]]`
- Site shell and navigation: `apps/v4/components/site-header.tsx`, `apps/v4/components/main-nav.tsx`, `apps/v4/components/mobile-nav.tsx`
- Preview and registry viewers: `apps/v4/components/component-preview.tsx`, `apps/v4/components/block-viewer.tsx`, `apps/v4/components/chart-display.tsx`
- Base UI source: `apps/v4/registry/new-york-v4/ui/{component}.tsx`
- Base UI raw source: `https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/new-york-v4/ui/{component}.tsx`
- Blocks source: `apps/v4/registry/new-york-v4/blocks/{block-name}`
- Charts source: `apps/v4/registry/new-york-v4/charts/{chart-name}.tsx`
- Examples source: `apps/v4/registry/new-york-v4/examples`

GitHub cloning can be unreliable on some networks, so direct raw GitHub URLs and the public registry index are accepted sources for implementation checks.

## Official Component Inventory

The v4 registry currently exposes more than the older 41-component shorthand. EduMind tracks the current registry and groups components by purpose:

- Display and feedback: `alert`, `avatar`, `badge`, `card`, `empty`, `item`, `kbd`, `marker`, `skeleton`, `spinner`, `sonner`.
- Layout and containers: `aspect-ratio`, `carousel`, `collapsible`, `resizable`, `scroll-area`, `separator`, `sidebar`.
- Navigation: `breadcrumb`, `menubar`, `navigation-menu`, `pagination`, `tabs`.
- Actions: `button`, `button-group`, `toggle`, `toggle-group`.
- Forms: `calendar`, `checkbox`, `combobox`, `field`, `form`, `input`, `input-group`, `input-otp`, `label`, `native-select`, `radio-group`, `select`, `slider`, `switch`, `textarea`.
- Overlays: `alert-dialog`, `context-menu`, `dialog`, `drawer`, `dropdown-menu`, `hover-card`, `popover`, `sheet`, `tooltip`.
- Data and AI patterns: `chart`, `attachment`, `bubble`, `message`, `message-scroller`.
- Utility patterns: `accordion`, `command`, `direction`, `progress`, `table`.

EduMind does not need to copy all registry files at once. It should add local primitives only when a route or feature block actually uses them.

## Official Blocks And Charts

Use official blocks as complete composition references, not just as visual inspiration:

- Dashboard: `dashboard-01`.
- Login: `login-01` to `login-05`.
- Signup: `signup-01` to `signup-05`.
- Sidebar: `sidebar-01` to `sidebar-16`.

Use charts for real operational information only:

- Area charts: trend and activity over time.
- Bar charts: comparison across workflows, document types, or generated artifacts.
- Line charts: progress and mastery over time.
- Pie/radial charts: bounded distribution summaries.
- Radar charts: multi-dimension capability or weak-point comparison.
- Tooltip variants: dense explainable charts where the user needs exact values.

EduMind chart use cases include file indexing status, RAG chunk coverage, recent generation activity, quiz mastery, weak-point distribution, and task latency.

## Research Notes

The official shadcn/ui examples are polished because they do not treat UI as isolated widgets. The same primitives are recombined with different density, hierarchy, alignment, data states, and responsive behavior. The rebuilt EduMind frontend follows that pattern:

- Pages are assembled from primitives, feature blocks, and route-level layouts.
- Repeated regions are generated from typed data arrays rather than hard-coded fragments.
- Variants express role, tone, loading, disabled, destructive, and selected states.
- Long-running AI work exposes pending, streaming, success, failure, empty, and retry states.
- Desktop and mobile are designed separately through responsive composition, not by squeezing one layout.

## Component Coverage

### Base UI Components

Local React components live in `frontend/src/components/ui`. The current committed set is intentionally small and only includes primitives used by the new app:

- Actions: `Button`, `Toggle`, `ToggleGroup`, and typed variants.
- Form: `Input`, `Textarea`, `Label`, `Select`, `Checkbox`, and form wrappers.
- Layout: `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`.
- Navigation: `Sidebar`, `Tabs`, `SegmentedControl`, and `Breadcrumb`.
- Overlays: `DropdownMenu`, `Sheet`, `Drawer`, and `Tooltip`.
- Feedback: `Alert`, `Badge`, `Progress`, `Skeleton`, and `Sonner`.
- Display: `Table`, `Avatar`, and chart primitives.

If a feature needs `Dialog`, `Sheet`, `Tooltip`, `ScrollArea`, `Command`, `Toast`, or chart primitives, add them as local shadcn/ui-style source files first, then compose them into route or pattern components.

### Functional Blocks

Composed blocks live in `frontend/src/components/patterns`:

- `MaterialPicker`: multi-file selection with RAG health.
- `AgentConversationPanel`: reusable agent message list, context panel, progress block, quick prompts, and composer.
- `MaterialPicker`: multi-file selection with RAG health and selected material summary.
- `GenerationConsole`: prompt, parameters, progress stream, generated output.
- `MetricGrid`: data-driven dashboard metrics.

Route pages provide additional composed surfaces:

- `DashboardPage`: project overview, role context, workflow cards, and implementation notes.
- `WorkspacePage`: agent-mode workflows for chat, quiz, paper, lesson plan, slides, smart notes, and podcast.
- `FileLibraryPage`: batch upload, file table, RAG query preview, material selection, and preview sheet.
- `RecordsPage`: unified history layout for chats, quizzes, papers, lesson plans, and slides.
- `FeatureHubPage`: compatibility route surface for secondary feature URLs; text-input features such as Bilibili search use the agent pattern.

### Charts

Charts stay lightweight unless a workflow needs deep interaction. Use accessible CSS/SVG summaries first:

- Mastery trend sparkline.
- File indexing status distribution.
- Generation throughput and recent activity summaries.

Every chart includes a text summary and must not rely on color alone.

## Composition Rules

1. Build from `ui` primitives to `patterns` to route pages.
2. Keep API and persistence in `frontend/src/lib` and `frontend/src/stores`; route components orchestrate but do not own transport details.
3. Keep navigation, workflow cards, metrics, and record rows data-driven.
4. Use Zustand for session, role, UI preferences, selected materials, and task progress.
5. Use React Router route objects and redirects for stable historical URLs such as `/chat`, `/teacher/paper`, `/files`, and `/quiz`.
6. Use SSE as the default long-task progress channel and keep WebSocket-compatible URLs in the API model.
7. Treat mobile as a first-class layout: sheet navigation, stacked workflow panes, full-width controls, no hidden primary actions.
8. Use icons from `lucide-react`; icon-only controls require labels or tooltips.

## AI Implementation Rules

Before generating a page, identify its official reference pattern:

- Dashboard: `dashboard-01`.
- Authentication: `login-03`, `login-04`, and `signup-*`.
- App navigation: `sidebar-*`.
- Data visualization: `charts/*`.
- Forms and dense inputs: `examples/form-*`, `examples/input-group-*`, `examples/field-*`.

Then follow these rules:

1. Design the data shape before JSX. Navigation, cards, tables, charts, and workflow actions must be generated from typed arrays.
2. Prefer composition over inheritance. Compose primitives into stable feature blocks rather than creating page-specific controls.
3. Keep state centralized in feature stores or route-level hooks.
4. Cover loading, empty, error, success, disabled, and partial-success states.
5. Use component variants deliberately; do not use one button/card style everywhere.
6. Use official primitives for dialogs, tabs, labels, progress, tooltips, switches, and scroll areas before custom controls.
7. Use the legacy Vue frontend only to confirm route coverage, labels, and durable layout relationships; do not reference or imitate its styles, detailed interactions, CSS, or implementation.

## Visual Direction

EduMind is an academic production cockpit with a low-saturation warm-gray and brown-orange surface language inspired by the Hiyo codex login/dashboard style:

- Canvas: near-black warm gray in dark mode and muted warm gray in light mode, with flat work surfaces and restrained borders.
- Accents: brown-orange for primary actions, stone for neutral information, amber for pending attention, crimson for destructive states.
- Shape: 5px to 6px radii, crisp dividers, compact controls, and fewer standalone rounded rectangle cards.
- Density: quiet dashboard density, suitable for repeated daily work.
- Typography: system sans-serif with tabular numerals for counts and timers.
- Motion: short opacity/translate transitions only where state changes need continuity; respect reduced motion.

Avoid deep-blue primary themes, green-dominant palettes, dominant purple or blue gradients, decorative blobs, nested cards, marketing hero sections, oversized dashboard typography, and any visual motif from the legacy frontend.

## Quality Checklist

- All controls have visible focus states and accessible names.
- Touch targets are at least 44px high.
- No horizontal scrolling at 375px width.
- Empty, loading, error, disabled, streaming, and success states are present.
- Text wraps inside buttons, cards, sidebars, and tables.
- Color is never the only status indicator.
- Light and dark themes both use semantic CSS variables.
- Route-level code is split by feature where practical.
- Unit tests cover stores, routing helpers, and API request construction.
- Playwright smoke tests cover desktop dashboard/workspace/file RAG and mobile file-library overflow.
