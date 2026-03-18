# Runtime Setup

## Default Strategy

`workflow-viz` does not bundle a PlantUML jar.

Use `python scripts/workflow_viz.py doctor --repo-root <repo>` to validate the rendering runtime before generating docs.

Default generated artifacts live under:

- `docs/workflow-viz/insights/<group>/analysis.md` or `docs/workflow-viz/insights/<group>/<file>.md`
- `docs/workflow-viz/code`
- `docs/workflow-viz/charts`

The generator now recommends semantic diagram keys such as:

- `sequence`
- `activity`
- `domain-structure`
- `boundary-context`
- `state`
- `data-flow`

Each generated `.puml` injects this theme by default:

```puml
@startuml
!theme materia
```

Use `generate --theme <name>` to override the theme, or `generate --theme none` to disable theme injection.

## Resolution Order

PlantUML runtime resolution prefers, in order:

1. `PLANTUML_COMMAND`
2. `plantuml` on `PATH`
3. `java -jar <path-to-plantuml.jar>`

If no runtime is available, `generate --render` should fail with a clear instruction to run `doctor`.
