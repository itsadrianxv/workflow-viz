# Markdown Page Template

Use one Markdown file per analyzed source file.

- If the current run emits exactly one Markdown file, place it at `docs/workflow-viz/insights/<group>/analysis.md`.
- If the current run emits multiple Markdown files, place them at `docs/workflow-viz/insights/<group>/<file>.md`.
- Do not generate `index.md` or other overview Markdown pages.

Recommended structure:

```md
# Hotspot Insight: <file title>

- Source file: `<relative/path>`
- File role: `<role>`
- Trigger reasons: `<1-3 summary bullets>`
- Score: `<score>`
- Entrypoint: `<entrypoint>`

<Short lead-in paragraph explaining why this role uses this reading order>

## Recommended Reading Order

- 1. `<diagram 1>`
- 2. `<diagram 2>`
- 3. `<diagram 3>`

## Top Three Diagrams

### Sequence
Pre-chart note: explain which runtime collaboration to focus on.
![Sequence](../../charts/<slug>-sequence.svg)

Post-chart note: explain who triggers, who responds, and where timing risks sit.

### Boundary Context
Pre-chart note: explain which local contracts or dependencies matter first.
![Boundary Context](../../charts/<slug>-boundary-context.svg)

Post-chart note: call out the interfaces, boundaries, and collaborators to verify.

### Domain Structure
Pre-chart note: explain which local concepts and relationships matter.
![Domain Structure](../../charts/<slug>-domain-structure.svg)

Post-chart note: explain which responsibilities or invariants must stay clean.

## Supplemental Diagrams

### Activity
Pre-chart note: explain how to read the main path.
![Activity](../../charts/<slug>-activity.svg)

Post-chart note: call out key inputs, conditions, and outputs.

<Short closing paragraph reminding the reader to verify real business semantics in source>
```

Writing rules:

- Keep the page image-first.
- Keep explanatory text close to the chart it explains.
- Start from the role-based top three, not from an architecture pack.
- Keep chart filenames stable so repeat generation updates the same assets.
- Do not bury charts under long narrative sections.
