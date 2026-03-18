# Workflow Viz Role-Based Diagram Priority Design

## Background

The current `workflow-viz` skill and generator assume that every selected hotspot file should start with a fixed architecture pack:

- `architecture-context`
- `architecture-modules`
- `architecture-dependencies`

That framing no longer matches the intended use of this skill.

The generator now primarily creates one Markdown page per code file to help a maintainer understand that file. In this single-file reading mode, "system-wide architecture" is often not the first question the reader needs answered.

For DDD-style projects in particular, different file roles need different visual entry points:

- application services and workflow orchestrators are usually best understood through runtime collaboration
- domain services are often best understood through concept structure and local boundaries
- entities and aggregate roots often need state and invariant-focused documentation
- repositories and infrastructure adapters need boundary, mapping, and interaction views rather than generic architecture diagrams

This design replaces the universal architecture-first default with role-based diagram templates plus signal-based promotion rules.

## Goals

- Make diagram priority match the understanding needs of single-file documentation.
- Introduce role-specific default diagram templates for these file roles:
  - application service
  - domain service
  - entity
  - aggregate root
  - repository
  - infrastructure adapter
  - workflow orchestrator
- Replace architecture-first wording and defaults with a file-local understanding model.
- Keep diagram selection predictable by using stable role templates.
- Avoid rigidity by allowing strong code signals to promote or demote diagrams.
- Preserve the current strengths of the skill:
  - hotspot scanning
  - per-file Markdown output
  - PlantUML and SVG generation

## Non-Goals

- This change does not attempt to infer every DDD role perfectly for every codebase.
- This change does not add full repository-level or bounded-context-level overview documents.
- This change does not require all UML notations to be implemented immediately.
- This change does not require semantically perfect diagram content generation in the first implementation.
- This change does not attempt to redesign hotspot scoring from scratch.

## Core Decisions

### 1. Single-file understanding becomes the primary framing

The generator should optimize for the first questions a maintainer has when opening one file, not for a repository-wide architecture story.

Diagram priority should therefore answer questions such as:

- How does this file behave at runtime?
- What local structure does it define?
- What boundary does it live on?
- What state or lifecycle does it manage?
- How does data move through it?

### 2. Diagram semantics are separated from UML rendering style

The generator should prioritize semantic diagram types, not rigid notation names.

For example:

- `domain-structure` may be rendered as a simplified class diagram, optionally borrowing object-diagram ideas
- `boundary-context` may be rendered as a lightweight component diagram, package diagram, or dependency map

This keeps the selection model stable even if the actual PlantUML representation evolves later.

### 3. The architecture pack is retired as the universal default

The following existing diagram keys should no longer be treated as the universal first three diagrams:

- `architecture-context`
- `architecture-modules`
- `architecture-dependencies`

Migration intent:

- `architecture-context` is conceptually replaced by `boundary-context`
- `architecture-modules` is conceptually replaced by `domain-structure`
- `architecture-dependencies` is absorbed into `boundary-context`

The first implementation may retain compatibility shims internally where helpful, but user-facing guidance should move to the new names and concepts.

## Diagram Taxonomy

### Core diagrams

These diagrams are eligible for the fixed top-three template of each role:

- `sequence`
  - answers runtime collaboration order
- `activity`
  - answers main flow progression and control skeleton
- `domain-structure`
  - answers local domain concepts, relationships, boundaries, and responsibilities
- `boundary-context`
  - answers exposed contracts, dependencies, ports, adapters, and local context
- `state`
  - answers lifecycle and state transitions
- `data-flow`
  - answers mapping, transformation, aggregation, and delivery paths

### Supplemental diagrams

These diagrams are never the universal default and are added only when strong signals justify them:

- `branch-decision`
- `async-concurrency`
- `object-snapshot`

## Role-Based Default Templates

Each detected file role receives a fixed ordered top-three template before any promotion rules are applied.

### Application service

- `sequence`
- `activity`
- `boundary-context`

Reasoning:
Application services are usually understood first by runtime coordination, then by flow skeleton, then by their contracts and dependencies.

### Domain service

- `domain-structure`
- `boundary-context`
- `activity`

Reasoning:
Domain services often encapsulate business concepts and rules more than orchestration. Their structure and boundary usually matter before detailed runtime sequencing.

### Entity

- `domain-structure`
- `boundary-context`
- `state`

Reasoning:
A normal entity should default to local structure first. State remains important but should not dominate unless real lifecycle complexity is present.

### Aggregate root

- `state`
- `boundary-context`
- `domain-structure`

Reasoning:
Aggregate roots often carry lifecycle and invariant pressure and should default to a state-first explanation.

### Repository

- `boundary-context`
- `data-flow`
- `sequence`

Reasoning:
Repositories are best understood first through the contract they expose, then by object mapping, then by runtime interaction with storage.

### Infrastructure adapter

- `sequence`
- `boundary-context`
- `data-flow`

Reasoning:
Adapters are usually read first as integrations with external systems, then as boundary realizations, then as transformation layers.

### Workflow orchestrator

- `sequence`
- `activity`
- `boundary-context`

Reasoning:
Workflow files are typically orchestration-heavy and runtime-order-heavy, similar to application services but more likely to trigger async or state-related supplements.

## Promotion and Demotion Rules

Role templates define the default order. Strong code signals may then promote or demote diagrams.

### Promotion rules

- Promote `sequence` when:
  - collaborator count is high
  - ordered call chains are long
  - orchestration signals are strong
  - external runtime interaction is obvious

- Promote `activity` when:
  - process complexity is high
  - branch structure is important
  - collaborator count is lower than control-flow complexity

- Promote `state` when:
  - explicit lifecycle stages exist
  - state/status/phase/mode transitions are strong
  - aggregate behavior depends on entering or leaving states

- Promote `domain-structure` when:
  - the complexity is dominated by local concepts and relationships
  - aggregate boundaries or domain model organization are central

- Promote `boundary-context` when:
  - interface contracts or dependency boundaries are the main difficulty
  - repository or adapter behavior is largely defined by ports and dependencies

- Promote `data-flow` when:
  - DTO/domain/persistence mapping is prominent
  - transformation chains are long
  - aggregation or serialization steps are central

- Add `branch-decision` when:
  - guard clauses are numerous
  - short-circuit paths are common
  - exception, fallback, or degraded paths intertwine with the normal path

- Add `async-concurrency` when:
  - queue/worker/scheduler patterns exist
  - retries, timeouts, or fan-in/fan-out behavior exists
  - events or concurrency control patterns are visible

- Add `object-snapshot` when:
  - a concrete object or aggregate instance shape would materially clarify an entity or aggregate root

### Demotion rules

- Do not keep diagrams that have weak information density.
- If two diagrams answer nearly the same question, keep the more role-appropriate one.
- `branch-decision`, `async-concurrency`, and `object-snapshot` should not become universal top-three defaults.
- `data-flow` should not become the default first diagram in the first implementation.
- `boundary-context` should become the first diagram only when boundary understanding is clearly the main problem, such as repositories.

### Role-specific exception

Entities and aggregate roots must not be treated identically:

- entity: structure-first by default, state promoted only with strong lifecycle evidence
- aggregate root: state-first by default

## First Implementation Scope

The first implementation should focus on changes that are feasible inside the current generator:

1. Introduce the new semantic diagram keys:
   - `domain-structure`
   - `boundary-context`
   - `object-snapshot`

2. Introduce file-role detection heuristics for exactly these roles:
   - application service
   - domain service
   - entity
   - aggregate root
   - repository
   - infrastructure adapter
   - workflow orchestrator

3. Replace the fixed architecture-first `recommended_diagrams` ordering with role-based templates.

4. Update Markdown generation so the page intro reflects the selected top-three diagram group instead of hard-coded architecture wording.

5. Update user-facing docs and references to describe the new model.

6. Keep existing hotspot scoring unless a targeted adjustment is required for the new role signals.

## Compatibility Expectations

The first implementation does not need to immediately produce richly different PlantUML content for every new diagram key, but it must:

- expose the new diagram names in recommendation and documentation
- generate output files for the new keys
- stop describing architecture diagrams as the default universal reading path

Temporary compatibility is acceptable if needed, for example:

- `domain-structure` initially reusing simplified content patterns related to structure
- `boundary-context` initially reusing simplified dependency or local context patterns

However, user-facing documentation must reflect the new concepts, not the old architecture-first framing.

## Markdown Structure Expectations

Generated Markdown should no longer say:

- "先看下面这组架构图"
- "这一组图默认优先生成，用来回答它在系统哪里"

Instead, the intro should:

- name the detected role when available
- explain why the first three diagrams are prioritized for that role
- keep the page image-first

The page should still remain tightly image-centered, with only short text before and after each diagram.

## Testing Expectations

Implementation should include tests for at least:

1. Role detection returns the expected role for representative file names or code patterns.
2. Recommended diagram ordering follows the role template for each supported role.
3. Entity and aggregate root differ in the expected way.
4. Strong state signals promote `state` for entities when appropriate.
5. Repository defaults begin with `boundary-context`.
6. Infrastructure adapter defaults begin with `sequence`.
7. Markdown generation reflects the new file-local framing rather than architecture-pack wording.
8. Documentation files no longer present architecture-first as the universal default.

## Documentation Impact

The following files will need updates:

- `SKILL.md`
- `README.md`
- `README_EN.md`
- `references/diagram-selection.md`
- `references/markdown-template.md`
- `references/heuristics.md`
- `references/runtime-setup.md` if it references default diagram groups

These updates should describe:

- the role-based top-three model
- the new diagram taxonomy
- the retirement of the universal architecture pack
- the relationship between role templates and promotion rules

## Open Questions Deferred

These items are intentionally deferred and should not block the first implementation:

- whether to add finer-grained roles such as command handlers, sagas, policies, factories, or event handlers
- whether `object-snapshot` should later become a default diagram for some roles
- whether `data-flow` should be allowed to promote to first place in a future version
- whether role detection should become configurable by repository conventions
