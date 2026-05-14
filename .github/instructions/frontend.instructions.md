# Frontend Instructions

## Scope
Build the UI in **Next.js App Router + TypeScript + Tailwind + shadcn/ui**.

## Frontend Mission
The frontend is a **professional research dashboard**, not a toy interface. It must communicate:
- what dataset was used,
- what models were selected,
- what tasks were run,
- what results were observed,
- what evidence supports the result.

## Required Route Structure
- `/`
- `/datasets`
- `/experiments/new`
- `/experiments/[id]`
- `/compare`
- `/reports/[id]`
- `/settings`

## Required UI Blocks
1. Dataset picker / upload flow
2. Schema mapping flow
3. Experiment creation wizard
4. Model selection panel
5. Run status timeline
6. Metrics overview cards
7. Comparison table
8. Evidence panel
9. Report viewer
10. Error/empty/loading states for all above

## UI Standards
- Use consistent spacing and typography.
- No dense unreadable layouts.
- Every chart must have a textual interpretation.
- Every long-running action must expose progress.
- Every failure must have actionable next steps.

## Accessibility Standards
- keyboard navigable,
- semantic headings,
- aria labels for charts/controls,
- contrast-safe colors,
- visible focus states.

## Data Fetching Standards
- Frontend never knows provider secrets.
- Use typed fetch helpers or generated clients.
- Co-locate queries with route segments where sensible.
- All server/network errors must render an error boundary or explicit message.

## Component Design Rules
- Presentational components must be dumb where possible.
- Container/page components orchestrate data fetching.
- Shared components go into a reusable library only if reused at least twice.
- Do not create overly generic components early.

## Required States Per Page
Each page must implement:
- `loading`
- `success`
- `empty`
- `recoverable error`
- `non-recoverable error`

## Compare Page Requirements
The compare page must show:
- model names,
- task names,
- metrics,
- latency,
- notable strengths,
- notable weaknesses,
- recommended use case.

## Report Viewer Requirements
- Render markdown cleanly.
- Show metadata header.
- Support copy/export actions.
- Render references section distinctly.
- Support collapse/expand for provenance appendix.

## Frontend Testing Requirements
- component tests for key widgets,
- route-level tests for wizard flows,
- E2E for upload → run → report open,
- visual sanity checks for charts and tables.

## Frontend Anti-Patterns (Forbidden)
- direct model calls from browser,
- giant page files with all logic inline,
- untyped API parsing,
- optimistic UI without reconciliation,
- color-only meaning in charts.
