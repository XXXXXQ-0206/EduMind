# shadcn/ui Official Source Research Audit

## Research Scope

The React rewrite uses shadcn/ui as a composition and quality reference rather than copying the old Vue frontend. This audit records the official source locations used by agents before UI implementation and keeps a durable reference map for later feature work.

## Official Sources

- Official site: `https://ui.shadcn.com`
- Official AI index: `https://ui.shadcn.com/llms.txt`
- Official registry JSON: `https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry.json`
- Official GitHub repository: `https://github.com/shadcn-ui/ui`
- v4 app root: `https://github.com/shadcn-ui/ui/tree/main/apps/v4`
- v4 registry source root: `https://github.com/shadcn-ui/ui/tree/main/apps/v4/registry/new-york-v4`
- v4 UI primitive source pattern: `https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/new-york-v4/ui/{component}.tsx`
- v4 block source pattern: `https://github.com/shadcn-ui/ui/tree/main/apps/v4/registry/new-york-v4/blocks/{block-name}`
- v4 examples source pattern: `https://github.com/shadcn-ui/ui/tree/main/apps/v4/registry/new-york-v4/examples/{example-name}.tsx`

## Registry Snapshot

The v4 registry JSON was read from the official raw GitHub endpoint during the frontend rewrite audit. The registry groups the current published resources as follows:

| Registry type | Count |
|---|---:|
| `registry:ui` | 54 |
| `registry:block` | 97 |
| `registry:example` | 238 |
| `registry:internal` | 13 |
| `registry:theme` | 5 |
| `registry:style` | 2 |
| `registry:hook` | 1 |
| `registry:lib` | 1 |

These counts are intentionally recorded as a source snapshot, not as a requirement to vendor every component into EduMind. EduMind vendors local primitives only when the application needs them.

## Patterns Applied In EduMind

| Official pattern family | EduMind implementation |
|---|---|
| Dashboard and dense app shell | `frontend/src/pages/dashboard-page.tsx`, `frontend/src/components/layout/app-shell.tsx` |
| Sidebar and mobile navigation | data-driven `navSections` plus desktop sidebar and mobile drawer in `app-shell.tsx` |
| Login/signup | `frontend/src/pages/auth-page.tsx` |
| Cards, badges, buttons, forms, tables | local primitives in `frontend/src/components/ui` |
| Data-driven workflow panels | `frontend/src/components/patterns/generation-console.tsx` |
| File and RAG material selection | `frontend/src/pages/file-library-page.tsx`, `frontend/src/components/patterns/material-picker.tsx` |
| Records and secondary feature routes | `frontend/src/pages/records-page.tsx`, `frontend/src/pages/feature-hub-page.tsx` |

## Agent Usage Rule

Before adding new UI primitives or route-level surfaces, agents should:

1. Check this file for the official source path pattern.
2. Check `docs/frontend/shadcn-react-quality-guide.md` for EduMind design rules.
3. Add only the primitives needed by the feature.
4. Keep the feature data-driven and preserve mobile behavior at 375px width.
