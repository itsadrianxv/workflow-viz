# Workflow Viz Insights Grouping Design

## Background

The current `workflow-viz` generator writes Markdown files directly under `docs/workflow-viz/insights/`, typically as a flat set of files such as `<slug>.md` plus `index.md`.

This structure has two problems for the next phase of the skill:

1. The `insights` directory becomes crowded as more analyses are generated.
2. Aggregated guide pages are not the current priority; the immediate goal is to produce strong per-file explanations.

The design below changes the output model so Markdown artifacts are organized into analysis-scoped subdirectories, while preserving the existing `code/` and `charts/` layout for PlantUML and SVG outputs.

## Goals

- Place generated Markdown under one or more well-named subdirectories inside `docs/workflow-viz/insights/`.
- Support generating documentation for one file or many files in the same run.
- Generate one explanation Markdown file per analyzed code file.
- Stop generating `index.md` and any overview or guide-style Markdown pages.
- Keep names readable and stable.
- Avoid numbered Markdown filenames such as `01-foo.md`, `1.foo.md`, or hash-like suffixes.
- Reuse an existing subdirectory when the current analysis scope matches it closely enough.

## Non-Goals

- No cross-file relationship document is introduced in this change.
- No group-level overview Markdown is introduced in this change.
- `docs/workflow-viz/code/` and `docs/workflow-viz/charts/` are not moved in this change.
- This change does not attempt to fully solve long-term historical versioning of analysis outputs.

## Core Decisions

### 1. Markdown outputs move into analysis-scoped subdirectories

Generated Markdown files will no longer be written directly under `docs/workflow-viz/insights/`.

Instead, the generator will create one or more subdirectories under `docs/workflow-viz/insights/`, based on a runtime grouping analysis of the selected files.

Examples:

```text
docs/workflow-viz/insights/payment/handler.md
docs/workflow-viz/insights/payment/rules.md
docs/workflow-viz/insights/auth-token/auth-token.md
docs/workflow-viz/insights/order-handler/analysis.md
```

### 2. One Markdown file per analyzed code file

Each analyzed source file gets exactly one explanation Markdown document.

The generated Markdown should explain that file only. It should not attempt to serve as:

- a repository overview
- a batch summary
- a group summary
- a cross-file guide

### 3. Remove overview-style Markdown artifacts

The generator will stop producing:

- `docs/workflow-viz/insights/index.md`
- `docs/workflow-viz/insights/<slug>.md`
- any other aggregated Markdown page intended as a reading guide or table of contents

This change intentionally narrows the output surface to per-file analysis pages only.

## Runtime Grouping Model

When multiple files are selected in one run, the generator should first decide how many logical documentation groups exist.

### Grouping rule

Files that are logically related should share one `insights` subdirectory.

Files that are effectively independent should use separate subdirectories.

This is a runtime judgment, not a rigid path-only rule.

### Signals for "related"

The generator should weigh signals such as:

- common parent directory or module prefix
- similar role hints or workflow responsibilities
- filenames that clearly belong to the same workflow or responsibility cluster
- evidence that the files are part of the same conceptual module

### Signals for "independent"

The generator should prefer separate subdirectories when:

- files sit in unrelated domains
- directory structure suggests different modules or bounded contexts
- names and role hints do not suggest a shared workflow
- grouping them would create a vague or misleading directory name

### Result of grouping

If multiple related files are selected, create one shared subdirectory for that group.

If multiple unrelated files are selected, create multiple subdirectories, one per logical group.

There is no requirement that the number of subdirectories equal the number of input files. The count is determined by the runtime grouping analysis.

## Naming Rules

### Subdirectory naming

Each group receives a readable, stable directory name.

Rules:

- Prefer a semantic module or workflow name.
- For a single-file group, derive the directory name from the file's semantics.
- Avoid generic names such as `index`, `main`, `utils`, or `types` when used alone.
- If a file stem is too generic, combine it with parent context, such as `payment-handler`.
- Do not add timestamps, numeric prefixes, or hash suffixes.

### Markdown naming

Markdown naming depends on the size of the current batch:

- If the entire run produces exactly one Markdown file, name it `analysis.md`.
- If the run produces more than one Markdown file, each file gets a stable semantic filename such as `<file-slug>.md`.

Examples:

```text
Single-file run:
docs/workflow-viz/insights/order-handler/analysis.md

Multi-file related run:
docs/workflow-viz/insights/payment/handler.md
docs/workflow-viz/insights/payment/rules.md

Multi-file unrelated run:
docs/workflow-viz/insights/payment-handler/payment-handler.md
docs/workflow-viz/insights/auth-token/auth-token.md
```

## Reuse and Update Behavior

If a newly analyzed group maps cleanly onto an existing `insights` subdirectory, the generator should reuse that directory and update the Markdown files inside it.

Expected behavior:

- Same file or same logical group should tend to reuse the same directory.
- Re-generation should overwrite the current Markdown artifact for that file.
- Reuse should favor stability and readability over perfect historical separation.

## Cleanup Rules

The generator should stop writing legacy aggregated Markdown artifacts.

For files affected by the current run, the generator may clean up legacy outputs that clearly belong to the previous flat layout, including:

- `docs/workflow-viz/insights/index.md`
- `docs/workflow-viz/insights/<slug>.md`

Cleanup must stay conservative:

- only remove artifacts that the generator can confidently identify as its own legacy outputs
- do not remove unrelated or user-authored Markdown files

## Asset Layout

This design changes Markdown placement only.

The following remain unchanged:

- PlantUML files under `docs/workflow-viz/code/`
- SVG charts under `docs/workflow-viz/charts/`

Because Markdown files now live one directory deeper, Markdown image links must be updated accordingly, for example:

```md
![Architecture Context](../../charts/<slug>-architecture-context.svg)
```

## Error Handling and UX Expectations

The generator should continue to support:

- explicit multi-file selection
- scan-driven selection of multiple files

The presence of multiple files must not trigger overview-page generation.

Instead, the generator should:

- group files at runtime
- create the needed subdirectories
- emit one Markdown file per analyzed source file

## Testing Expectations

Implementation should be covered by tests for at least the following cases:

1. Single-file generation writes `analysis.md` inside one generated subdirectory.
2. Multi-file generation with related files writes multiple per-file Markdown files into one shared subdirectory.
3. Multi-file generation with unrelated files writes Markdown files into multiple subdirectories.
4. No `index.md` is generated.
5. Markdown filenames contain no numbering.
6. Markdown chart links are valid for the new directory depth.
7. Legacy flat-layout Markdown cleanup remains conservative.

## Documentation Impact

The following documents will need updates after implementation:

- `SKILL.md`
- `README.md`
- `README_EN.md`
- any reference docs that describe output layout or Markdown paths

Those updates should describe:

- the grouped `insights` subdirectory layout
- the removal of overview Markdown
- the `analysis.md` special case for single-file runs
- the per-file naming behavior for multi-file runs

## Open Future Direction

Cross-file relationship explanations are intentionally deferred.

Future work may introduce:

- relationship-level diagrams
- group-level guide pages
- richer grouping heuristics or metadata

That work should build on this grouped-directory model rather than reintroducing a flat `insights` layout.
