# Markdown Page Template

Use one Markdown file per analyzed source file.

- If the current run emits exactly one Markdown file, place it at `docs/workflow-viz/insights/<group>/analysis.md`.
- If the current run emits multiple Markdown files, place them at `docs/workflow-viz/insights/<group>/<file>.md`.
- Do not generate `index.md` or other overview Markdown pages.

Recommended structure:

```md
# Hotspot Insight: <file title>

- Source file: `<relative/path>`
- Trigger reasons: `<1-3 summary bullets>`
- Score: `<score>`
- Entrypoint: `<entrypoint>`

<Short lead-in paragraph explaining what to inspect first>

## Architecture Pack

### Architecture Context
Pre-chart note: explain what question this chart answers.
![Architecture Context](../../charts/<slug>-architecture-context.svg)

Post-chart note: call out the roles, boundaries, and relationships to verify.

### Architecture Modules
Pre-chart note: explain how the module split helps clarify responsibilities.
![Architecture Modules](../../charts/<slug>-architecture-modules.svg)

Post-chart note: call out which boundaries must stay clean.

### Architecture Dependencies
Pre-chart note: explain why dependency coordination deserves its own view.
![Architecture Dependencies](../../charts/<slug>-architecture-dependencies.svg)

Post-chart note: explain which collaborators are critical.

## Activity

### Main Activity
Pre-chart note: explain how to read the main path.
![Activity](../../charts/<slug>-activity.svg)

Post-chart note: call out key inputs, conditions, and outputs.

## Sequence

### Main Sequence
Pre-chart note: explain which collaboration timing to focus on.
![Sequence](../../charts/<slug>-sequence.svg)

Post-chart note: explain who triggers, who responds, and where timing risks sit.

<Short closing paragraph reminding the reader to verify real business semantics in source>
```

Writing rules:

- Keep the page image-first.
- Keep explanatory text close to the chart it explains.
- Prefer the three architecture charts before flow-oriented diagrams.
- Keep chart filenames stable so repeat generation updates the same assets.
- Do not bury charts under long narrative sections.
