# Workflow Viz

Help coding agents do more than generate code. Help them make code understandable.

`workflow-viz` is a skill for Codex-style coding agents. When the cost of understanding code is higher than the value of reading it line by line, it identifies which files truly deserve visualization, then generates architecture-first PlantUML, SVG, and Markdown docs that help developers build the right mental model faster.

## Why this project exists

In the vibe coding era, one problem keeps getting worse:

- code generation is often faster than human comprehension
- some of the hardest code is not large code, but dense orchestration code
- AI-generated code is especially likely to become branch-heavy, collaboration-heavy, async-heavy, and difficult to reason about
- linear reading is a poor way to understand main flow, branching, collaborators, state transitions, and concurrency

The result is familiar:

- changes slow down
- reviews get harder
- debugging gets more expensive
- trust in AI-generated code drops

`workflow-viz` was built for exactly this pain.

It does not try to visualize everything. It starts with a more useful question:

"Is this code worth visualizing at all?"

## What it does

`workflow-viz` provides a three-step solution:

1. decide whether the current task should activate visualization at all
2. narrow the repository down to the best candidate files
3. score candidate files by comprehension cost before suggesting or generating docs

Once generation starts, it produces:

- PlantUML source files
- rendered SVG diagrams
- image-first Markdown insight pages
- an overview index page

Default output location:

```text
docs/workflow-viz/insights/<group>/analysis.md
docs/workflow-viz/insights/<group>/<file>.md
docs/workflow-viz/code/
docs/workflow-viz/charts/
```

- Single-file runs write only `analysis.md`
- Multi-file runs first decide runtime groups, then write one Markdown file per source file inside each group directory
- No `index.md` or other overview Markdown page is generated

## What makes it different

### 1. It does not visualize everything

Most code-to-diagram tools start drawing as soon as they see source code.

`workflow-viz` is more selective. It asks:

- is this code genuinely expensive to understand?
- is the pain structural, collaborative, asynchronous, or stateful?
- which diagrams would actually help a human understand it?

### 2. It does not rely on LOC as the primary trigger

The skill uses static heuristics to estimate comprehension cost instead of treating file length as the main signal.

It looks at things like:

- cyclomatic complexity
- nesting and branch density
- retry / fallback / exception paths
- cross-module fan-out
- async and concurrency patterns
- state transitions
- orchestration-style naming hints

That makes it especially useful for the kind of AI-generated code that is short, dense, and surprisingly hard to understand.

### 3. It uses a three-layer model that fits agent workflows

`workflow-viz` is not designed to scan the entire repository immediately.

It separates the decision into three layers:

- Layer 1: conversation-level activation signals
- Layer 2: repository-level candidate filtering
- Layer 3: file-level comprehension scoring

This keeps the agent more precise, more efficient, and less noisy in real collaboration.

### 4. It is architecture-first

The current version prioritizes an architecture pack by default:

- `architecture-context`
- `architecture-modules`
- `architecture-dependencies`

Then it adds:

- `activity`
- `sequence`
- `branch-decision`
- `state`
- `async-concurrency`
- `data-flow`

So the skill is not only about "how the code executes". It first helps people understand where the file sits in the system, how responsibilities are split, and how collaborators interact.

### 5. It produces image-first docs, not walls of text

The generated Markdown pages are designed around diagrams, with short text before and after each chart.

That makes them much more useful for:

- reviews
- onboarding
- AI-generated code handoff
- long-term maintenance

### 6. Chinese keywords, code names unchanged

Generic keywords inside diagrams are written in Chinese, while class names, method names, function names, and file names keep their original code naming without translation or style changes.

### 7. Dark-mode-friendly SVG output

Rendered SVGs now assume a dark viewing environment by default and force a white foreground for text and linework, so charts stay readable after being embedded into dark documents.

## Quick start

### 1. Check the rendering environment

```bash
python scripts/workflow_viz.py doctor --repo-root <repo>
```

### 2. Scan for hotspots

```bash
python scripts/workflow_viz.py scan --repo-root <repo>
```

To focus on one file:

```bash
python scripts/workflow_viz.py scan --repo-root <repo> --paths path/to/file.py
```

### 3. Generate docs

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --render
```

To override the default PlantUML theme:

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --theme plain --render
```

To disable theme injection:

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --theme none --render
```

## What the current version already includes

- `doctor / scan / generate` core commands
- default output under `docs/workflow-viz/{insights,code,charts}`, with Markdown grouped under `insights/<group>/`
- single-file runs write `analysis.md`; multi-file runs write one semantic Markdown filename per source file
- PlantUML runtime preflight checks
- multi-language static hotspot detection
- architecture-first default diagram packs
- Chinese in-diagram labels, preserved code names, and white foreground dark-mode SVG output
- cleanup for legacy single-`architecture` outputs

## Why this is worth using in open source

Because the problem is no longer niche.

Many teams now share the same pain:

"AI can produce code quickly, but teams still need a reliable way to understand it."

This skill is a strong fit if:

- you use Codex, Claude Code, or similar coding agents
- you maintain a growing amount of AI-generated code
- your team struggles to reason about orchestration-heavy code
- you want diagramming to become a repeatable engineering workflow, not a one-off manual effort

## Reliability

The repository already includes automated tests covering key behavior, including:

- the default output directory
- architecture-first recommended diagram packs
- PlantUML theme injection and disable behavior
- image-first Markdown layout
- legacy artifact cleanup
- consistency between the skill and its reference docs

## In one sentence

`workflow-viz` is not a toy "turn code into flowcharts" utility.

It is a comprehension accelerator for coding agents: first decide what deserves visualization, then turn high-friction code into maintainable visual documentation that humans can actually use.
