# Workflow Viz

Help coding agents do more than generate code. Help them make code understandable.

`workflow-viz` is a skill for Codex-style coding agents. When the cost of understanding code is higher than the value of reading it line by line, it identifies which files truly deserve visualization, then generates role-based PlantUML, SVG, and Markdown docs centered on single-file understanding.

This version is no longer architecture-first by default. It now chooses the top diagrams by file role:

- application services and workflow orchestrators usually start with `sequence`
- domain services usually start with `domain-structure`
- entities usually start with `domain-structure`
- aggregate roots usually start with `state`
- repositories usually start with `boundary-context`
- infrastructure adapters usually start with `sequence`

## Diagram Taxonomy

Core diagrams:

- `sequence`
- `activity`
- `domain-structure`
- `boundary-context`
- `state`
- `data-flow`

Supplemental diagrams:

- `branch-decision`
- `async-concurrency`
- `object-snapshot`

`domain-structure` is usually rendered as a simplified class-style diagram for file-local structure. `boundary-context` focuses on local contracts and dependencies rather than whole-system architecture.

## Default Output Layout

```text
docs/workflow-viz/insights/<group>/analysis.md
docs/workflow-viz/insights/<group>/<file>.md
docs/workflow-viz/code/
docs/workflow-viz/charts/
```

- Single-file runs write `analysis.md`
- Multi-file runs group related files, then write one Markdown file per source file
- No overview Markdown page is generated

## Minimal CLI Flow

```bash
python scripts/workflow_viz.py doctor --repo-root <repo>
python scripts/workflow_viz.py scan --repo-root <repo>
python scripts/workflow_viz.py generate --repo-root <repo> --render
```

Target a specific file:

```bash
python scripts/workflow_viz.py scan --repo-root <repo> --paths path/to/file.py
python scripts/workflow_viz.py generate --repo-root <repo> --paths path/to/file.py --render
```

Override the default theme:

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --theme plain --render
python scripts/workflow_viz.py generate --repo-root <repo> --theme none --render
```

## License

This project is released under the [MIT License](LICENSE).
