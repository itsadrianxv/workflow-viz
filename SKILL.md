---
name: workflow-viz
description: Use when Codex needs to decide whether code is expensive to understand and would benefit from visual documentation, especially for workflow-heavy, branching, orchestration, async, stateful, or AI-generated code, or when scanning a repository for hotspots that deserve PlantUML-backed docs.
---

# Workflow Viz

## 概述

当代码理解速度明显慢于生成速度时，用这个 skill 识别高理解成本文件，并产出以图片为主的单文件洞察文档。

这一版的重点不再是“先讲系统总体架构”，而是“先回答这个文件最难懂的是什么”。默认逻辑是：

- 先识别文件角色
- 再按角色给固定前三张图
- 最后再根据分支、状态、异步、数据流等强信号补图

## 默认规则

只要进入生成流程，就默认遵守这些规则：

- PlantUML 图中的用户可见关键词必须用中文。
- 类名、方法名、函数名、文件名等专属名词保留代码命名。
- 每个生成的 `.puml` 默认以以下头部开始，除非用户明确要求其他主题：

```puml
@startuml
!theme materia
```

- 默认按暗色环境查看 SVG：无背景的文字和线条使用白色，浅色图形里的文字保留深色。
- 文档以图为主，说明文字尽量紧贴图片。
- 默认优先级来自角色模板，而不是统一的架构图三连。

## 图种体系

核心图种：

- `sequence`
- `activity`
- `domain-structure`
- `boundary-context`
- `state`
- `data-flow`

补充图种：

- `branch-decision`
- `async-concurrency`
- `object-snapshot`

说明：

- `domain-structure` 面向文件局部结构，通常可用简化类图表达。
- `boundary-context` 面向文件局部边界，不再等同于系统总体架构图。
- 旧的 `architecture-context`、`architecture-modules`、`architecture-dependencies` 只作为兼容和清理历史产物的概念保留，不再是默认阅读起点。

## 角色模板

当前只区分这 7 类角色：

- 应用服务：`sequence` -> `activity` -> `boundary-context`
- 领域服务：`domain-structure` -> `boundary-context` -> `activity`
- 实体：`domain-structure` -> `boundary-context` -> `state`
- 聚合根：`state` -> `boundary-context` -> `domain-structure`
- 仓储：`boundary-context` -> `data-flow` -> `sequence`
- 基础设施适配器：`sequence` -> `boundary-context` -> `data-flow`
- 工作流编排：`sequence` -> `activity` -> `boundary-context`

如果信号足够强，可以在默认模板上提权：

- 分支和守卫复杂：补 `branch-decision`
- 状态迁移明显：提权或补 `state`
- 异步和并发明显：补 `async-concurrency`
- 映射和转换链明显：提权或补 `data-flow`
- 实体或聚合根存在明显关键快照：补 `object-snapshot`

## 三层模型

### 第 1 层：会话级触发信号

先判断这轮任务是否真的和“理解复杂流程代码”有关。

### 第 2 层：仓库级候选筛选

启用 skill 后，再决定先扫描哪些文件，不要一上来就全仓细读。

### 第 3 层：文件级理解成本评分

最后对候选文件做门控和评分，决定：

- 是否值得补图
- 是否直接进入生成
- 需要哪几类图

详细阈值和角色提示见 `references/heuristics.md`。

## 何时启用

这些情况应优先启用：

- 用户要理解流程复杂、协作复杂、异步复杂或状态复杂的代码。
- 用户明确提出“画图”“做可视化文档”“生成 PlantUML / SVG / Markdown”。
- 文件主流程、分支、协作者、状态迁移或并发顺序难以快速看懂。
- 文件明显属于工作流编排、应用服务、领域服务、实体、聚合根、仓储或基础设施适配器。
- 用户要扫描仓库，找出最值得补图的热点文件。
- 用户在处理 AI 生成代码，需要通过图降低理解门槛。

这些情况不要默认启用：

- 普通 CRUD、数据定义、常量表
- 只改局部样式、文案或一小段明显逻辑
- 目标只是快速修一个明确 bug，且没有流程理解瓶颈

## 工作流

### 1. 先扫描

```bash
python scripts/workflow_viz.py scan --repo-root <repo>
```

用户明确点名文件时：

```bash
python scripts/workflow_viz.py scan --repo-root <repo> --paths path/to/file.py
```

扫描结果至少要回答：

- 哪些文件理解成本高
- 为什么高
- 哪些函数贡献了主要复杂度
- 推荐补哪些图

### 2. 决定建议还是直接生成

- 用户明确要求“画图/生成文档”时，直接进入生成。
- 否则先汇报热点和理由，再等待确认。
- Plan Mode 只扫描和建议，不写 `md` / `puml` / `svg`。

### 3. 生成文档

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --render
```

显式指定文件时：

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --paths path/to/file.py --render
```

如需覆盖默认主题：

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --theme plain --render
```

如需禁用主题注入：

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --theme none --render
```

脚本负责：

- 评分并筛选热点
- 生成或更新 Markdown
- 生成或更新 PlantUML 源码
- 渲染 SVG
- 清理旧的 `*-architecture.*` 遗留产物

脚本不负责最终业务语义完稿。生成后要再读源码，把真实角色名、依赖名、条件和结论补齐。

## 输出规则

默认输出到目标仓库：

- `docs/workflow-viz/insights/<group>/analysis.md`
- `docs/workflow-viz/insights/<group>/<file>.md`
- `docs/workflow-viz/code/<slug>-<diagram>.puml`
- `docs/workflow-viz/charts/<slug>-<diagram>.svg`

默认阅读骨架：

- 先看角色模板对应的固定前三张图
- 再看按信号补出的额外建议图

## 文档写法

- 一页只讲一个热点文件。
- 开头先说明文件角色和推荐阅读顺序。
- 每张图都使用“图前说明 -> 图片 -> 图后解读”的结构。
- 不要把大段正文放在远离图的位置。
- 不要把源码路径、函数名说明、评分细节塞进图里。

## 参考资料

- 候选筛选、阈值和角色提示：`references/heuristics.md`
- 图类型选择：`references/diagram-selection.md`
- Markdown 结构规范：`references/markdown-template.md`
- PlantUML 运行时与预检：`references/runtime-setup.md`
