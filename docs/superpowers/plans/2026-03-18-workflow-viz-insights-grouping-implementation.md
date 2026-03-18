# Workflow Viz Insights Grouping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update `workflow-viz` so Markdown outputs are grouped into analysis-derived subdirectories under `docs/workflow-viz/insights/`, remove overview-style Markdown outputs, and apply the new single-file vs multi-file naming rules.

**Architecture:** Keep PlantUML and SVG assets in the existing top-level `code/` and `charts/` directories, but route Markdown generation through a new grouping layer that decides which `insights` subdirectory each analyzed file belongs to. Replace flat Markdown output with per-group directories, conservative cleanup of legacy flat files, and relative chart links that work from the deeper directory structure.

**Tech Stack:** Python 3, `pathlib`, `unittest`, repository Markdown docs

---

### Task 1: Lock in expected behavior with failing tests

**Files:**
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/tests/test_workflow_viz.py`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/scripts/workflow_viz.py`

- [ ] **Step 1: Add tests for the new grouping and naming behavior**

Add or replace tests so they describe:
- single-file generation writes `analysis.md` inside one generated `insights/<group>/` directory
- related multi-file generation writes multiple Markdown files into one shared group directory
- unrelated multi-file generation writes Markdown files into multiple group directories
- no `index.md` is generated
- chart links use `../../charts/...`

- [ ] **Step 2: Run the focused tests to verify they fail**

Run: `python -m pytest tests/test_workflow_viz.py -q`
Expected: FAIL because current implementation still writes flat Markdown files and still generates `index.md`

- [ ] **Step 3: Implement only enough grouping helpers to satisfy the first failing assertions**

Add small helper functions in `scripts/workflow_viz.py` for:
- identifying generic file stems
- choosing a semantic directory name
- computing Markdown filenames for single-file and multi-file batches

- [ ] **Step 4: Run the focused tests again**

Run: `python -m pytest tests/test_workflow_viz.py -q`
Expected: still FAIL, but on later assertions once helper behavior begins to match the tests

- [ ] **Step 5: Commit the red-phase test changes once behavior is captured**

Run:
```bash
git add tests/test_workflow_viz.py scripts/workflow_viz.py
git commit -m "test: 补充洞察文档分组输出测试"
```

### Task 2: Route Markdown output through runtime grouping

**Files:**
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/scripts/workflow_viz.py`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/tests/test_workflow_viz.py`

- [ ] **Step 1: Write or extend a failing test for runtime grouping decisions**

Cover at least:
- shared parent/module signals group files together
- unrelated paths split into separate groups
- directory naming avoids generic names like `index` or `main`

- [ ] **Step 2: Run only the relevant tests and verify failure**

Run: `python -m pytest tests/test_workflow_viz.py -k "group or generate_docs" -q`
Expected: FAIL with missing grouping helpers or wrong output locations

- [ ] **Step 3: Implement minimal runtime grouping and Markdown writing**

Update generation flow to:
- derive one or more `insights` subdirectories from the selected results
- write one Markdown file per analyzed file
- name the file `analysis.md` only when the whole batch emits exactly one Markdown file
- otherwise use semantic per-file filenames without numbering
- stop writing `index.md`

- [ ] **Step 4: Run the relevant tests and verify they pass**

Run: `python -m pytest tests/test_workflow_viz.py -k "group or generate_docs" -q`
Expected: PASS

- [ ] **Step 5: Commit the grouping implementation**

Run:
```bash
git add scripts/workflow_viz.py tests/test_workflow_viz.py
git commit -m "feat: 实现洞察文档按分组子目录输出"
```

### Task 3: Add cleanup and compatibility behavior

**Files:**
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/scripts/workflow_viz.py`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/tests/test_workflow_viz.py`

- [ ] **Step 1: Add a failing test for legacy Markdown cleanup**

Cover conservative removal of:
- `docs/workflow-viz/insights/index.md`
- legacy flat `docs/workflow-viz/insights/<slug>.md`

while leaving unrelated files untouched

- [ ] **Step 2: Run the cleanup-focused test and verify failure**

Run: `python -m pytest tests/test_workflow_viz.py -k "cleanup or legacy" -q`
Expected: FAIL because legacy flat Markdown is not cleaned under the new rules

- [ ] **Step 3: Implement minimal cleanup logic**

Add cleanup that:
- removes generator-owned legacy flat Markdown for files in the current run
- does not remove nested Markdown files or unrelated user-authored files

- [ ] **Step 4: Run the cleanup-focused test and verify it passes**

Run: `python -m pytest tests/test_workflow_viz.py -k "cleanup or legacy" -q`
Expected: PASS

- [ ] **Step 5: Commit the cleanup behavior**

Run:
```bash
git add scripts/workflow_viz.py tests/test_workflow_viz.py
git commit -m "fix: 清理旧版平铺洞察文档输出"
```

### Task 4: Update docs to match the new output model

**Files:**
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/SKILL.md`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/README.md`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/README_EN.md`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/references/markdown-template.md`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/references/runtime-setup.md`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/tests/test_workflow_viz.py`

- [ ] **Step 1: Add or adjust documentation assertions first**

Update documentation tests to expect:
- grouped `insights/<subdir>/...` Markdown layout
- no `index.md`
- `analysis.md` only for single-file runs
- semantic filenames for multi-file runs

- [ ] **Step 2: Run the documentation-focused tests to verify failure**

Run: `python -m pytest tests/test_workflow_viz.py -k "documentation" -q`
Expected: FAIL because current docs still describe the flat layout

- [ ] **Step 3: Update the docs minimally and consistently**

Revise all user-facing docs so they describe:
- runtime grouping of Markdown outputs
- batch-sensitive Markdown naming
- unchanged `code/` and `charts/` locations

- [ ] **Step 4: Run the documentation-focused tests again**

Run: `python -m pytest tests/test_workflow_viz.py -k "documentation" -q`
Expected: PASS

- [ ] **Step 5: Commit the documentation updates**

Run:
```bash
git add SKILL.md README.md README_EN.md references/markdown-template.md references/runtime-setup.md tests/test_workflow_viz.py
git commit -m "docs: 更新洞察文档输出结构说明"
```

### Task 5: Final verification and delivery

**Files:**
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/scripts/workflow_viz.py`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/tests/test_workflow_viz.py`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/SKILL.md`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/README.md`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/README_EN.md`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/references/markdown-template.md`
- Modify: `C:/Users/hungyuk/.codex/skills/workflow-viz/references/runtime-setup.md`

- [ ] **Step 1: Run the full targeted test suite**

Run: `python -m pytest tests/test_workflow_viz.py -q`
Expected: PASS

- [ ] **Step 2: Run a representative generate command against a temp repo fixture if needed**

Run an existing local verification path or rely on the tested `generate_docs` unit path if no CLI fixture exists.
Expected: generated Markdown lives under grouped `insights` subdirectories and assets remain in `code/` and `charts/`

- [ ] **Step 3: Inspect the diff for unintended output changes**

Run: `git diff --stat`
Expected: only script, tests, and documentation changes related to grouped Markdown output

- [ ] **Step 4: Create the implementation commit**

Run:
```bash
git add scripts/workflow_viz.py tests/test_workflow_viz.py SKILL.md README.md README_EN.md references/markdown-template.md references/runtime-setup.md
git commit -m "feat: 调整洞察文档分组与命名规则"
```

- [ ] **Step 5: Push the branch**

Run:
```bash
git push
```
