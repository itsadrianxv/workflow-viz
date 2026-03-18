# Workflow Viz Role-Based Diagram Priority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the architecture-first default diagram pack with role-based top-three templates and promotion rules for single-file workflow-viz outputs.

**Architecture:** Keep the existing hotspot scoring pipeline, but add role detection and a semantic diagram taxonomy layer between analysis and diagram recommendation. Update Markdown and reference docs so the user-facing model matches the new role-based selection behavior, while keeping initial PlantUML generation pragmatic and compatible.

**Tech Stack:** Python 3, pytest, Markdown docs, PlantUML text generation

---

### Task 1: Lock in failing tests for the new selection model

**Files:**
- Modify: `tests/test_workflow_viz.py`
- Test: `tests/test_workflow_viz.py`

- [ ] **Step 1: Write failing tests for role detection and top-three ordering**

Add tests that cover:
- application service defaults to `sequence -> activity -> boundary-context`
- domain service defaults to `domain-structure -> boundary-context -> activity`
- entity defaults to `domain-structure -> boundary-context -> state`
- aggregate root defaults to `state -> boundary-context -> domain-structure`
- repository defaults to `boundary-context -> data-flow -> sequence`
- infrastructure adapter defaults to `sequence -> boundary-context -> data-flow`
- workflow orchestrator defaults to `sequence -> activity -> boundary-context`
- strong state signals promote `state` for entities
- Markdown intro no longer hard-codes architecture-pack wording

- [ ] **Step 2: Run the focused tests and confirm they fail**

Run: `python -m pytest tests/test_workflow_viz.py -q`

Expected:
- failures mention missing role detection, old architecture diagram keys, or old Markdown framing

- [ ] **Step 3: Commit the failing-test change**

Run:
```bash
git add tests/test_workflow_viz.py
git commit -m "test: 补充角色化图优先级失败用例"
```

### Task 2: Implement role detection and semantic diagram recommendation

**Files:**
- Modify: `scripts/workflow_viz.py`
- Test: `tests/test_workflow_viz.py`

- [ ] **Step 1: Add file-role detection primitives**

Implement a role model that can classify these roles:
- application service
- domain service
- entity
- aggregate root
- repository
- infrastructure adapter
- workflow orchestrator

Use lightweight heuristics based on relative path, filename, imports, symbols, and entrypoint clues.

- [ ] **Step 2: Replace the fixed architecture pack with role templates**

Implement new semantic diagram keys and role templates:
- `sequence`
- `activity`
- `domain-structure`
- `boundary-context`
- `state`
- `data-flow`
- optional supplements: `branch-decision`, `async-concurrency`, `object-snapshot`

- [ ] **Step 3: Add promotion and demotion logic**

Apply signal-based promotions while keeping templates stable:
- entity state promotion
- repository boundary-first defaults
- adapter sequence-first defaults
- workflow async supplements

- [ ] **Step 4: Run focused tests and make them pass**

Run: `python -m pytest tests/test_workflow_viz.py -q`

Expected:
- new ordering tests pass
- no architecture-pack-first assumptions remain in tested behavior

- [ ] **Step 5: Commit the implementation**

Run:
```bash
git add scripts/workflow_viz.py tests/test_workflow_viz.py
git commit -m "feat: 引入按文件角色选择图优先级"
```

### Task 3: Update Markdown output framing and diagram generation compatibility

**Files:**
- Modify: `scripts/workflow_viz.py`
- Test: `tests/test_workflow_viz.py`

- [ ] **Step 1: Update Markdown page framing**

Change the generated intro so it:
- describes the detected file role when available
- explains the first three diagrams as a role-based reading path
- removes architecture-pack-first wording

- [ ] **Step 2: Add pragmatic PlantUML builders for new semantic diagram keys**

Ensure the new keys generate valid `.puml` outputs and can render cleanly, even if some first-pass builders reuse compatible structural patterns internally.

- [ ] **Step 3: Extend tests for Markdown and output file expectations**

Verify:
- new chart paths use semantic keys
- Markdown contains new framing text
- generated docs include the expected top-three keys for representative roles

- [ ] **Step 4: Run focused tests and confirm pass**

Run: `python -m pytest tests/test_workflow_viz.py -q`

- [ ] **Step 5: Commit the output-model change**

Run:
```bash
git add scripts/workflow_viz.py tests/test_workflow_viz.py
git commit -m "feat: 更新角色化图文输出骨架"
```

### Task 4: Update skill and reference documentation

**Files:**
- Modify: `SKILL.md`
- Modify: `README.md`
- Modify: `README_EN.md`
- Modify: `references/diagram-selection.md`
- Modify: `references/markdown-template.md`
- Modify: `references/heuristics.md`
- Modify: `references/runtime-setup.md`
- Test: `tests/test_workflow_viz.py`

- [ ] **Step 1: Update the skill narrative**

Document:
- single-file understanding as the primary framing
- the new core and supplemental diagram taxonomy
- role-based top-three defaults
- the retirement of the universal architecture pack

- [ ] **Step 2: Update README and reference docs**

Align all user-facing docs with:
- new diagram names
- role templates
- promotion rules
- Markdown examples using semantic keys

- [ ] **Step 3: Update documentation assertions in tests**

Adjust documentation tests so they verify the new terminology and reject architecture-first defaults.

- [ ] **Step 4: Run focused tests and confirm pass**

Run: `python -m pytest tests/test_workflow_viz.py -q`

- [ ] **Step 5: Commit the documentation update**

Run:
```bash
git add SKILL.md README.md README_EN.md references/diagram-selection.md references/markdown-template.md references/heuristics.md references/runtime-setup.md tests/test_workflow_viz.py
git commit -m "docs: 更新角色化图优先级说明"
```

### Task 5: Final verification

**Files:**
- Modify: none expected
- Test: `tests/test_workflow_viz.py`

- [ ] **Step 1: Run the full test suite**

Run: `python -m pytest -q`

Expected:
- all tests pass

- [ ] **Step 2: Run a representative generator command**

Run:
```bash
python scripts/workflow_viz.py scan --repo-root .
```

Expected:
- command completes successfully
- output includes recommended semantic diagram keys where applicable

- [ ] **Step 3: Review git diff for scope correctness**

Run:
```bash
git status --short
git diff --stat
```

Expected:
- only planned files changed
- no accidental edits

- [ ] **Step 4: Commit any final verification-only adjustments if needed**

If verification reveals a last small fix, commit it separately with an accurate message.
