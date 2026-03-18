---
name: workflow-viz
description: Use when Codex needs to decide whether code is expensive to understand and would benefit from visual documentation, especially for workflow-heavy, branching, orchestration, async, stateful, or AI-generated code, or when scanning a repository for hotspots that deserve PlantUML-backed docs.
---

# Workflow Viz

## 概述

当代码的理解速度明显慢于生成速度时，用这个 skill 识别高理解成本文件，并沉淀成以图片为主的可维护洞察文档。

这里的重点不是“把所有代码都画出来”，而是优先挑出真正难建立心智模型的热点，再补一组架构图和流程图，让后续维护者先看图、再回源码。

## 默认规则

只要进入生成流程，就默认遵守这 5 条：

- PlantUML 图中的用户可见关键词必须用中文。
- 图中的类名、方法名、函数名、文件名等专属名词保留代码命名，不要翻译或重写风格。
- 架构图是默认重点，每个热点文件至少先生成 3 张：`architecture-context`、`architecture-modules`、`architecture-dependencies`。
- 每个生成的 `.puml` 默认以以下头部开始，除非用户明确要求其他主题：

```puml
@startuml
!theme materia
```

- 默认按暗色环境查看 SVG，前景文字和线条统一使用白色，避免插入深色文档后看不清。
- 文档以图为主。除开头和结尾允许少量引导文字外，其余文字都应紧贴在图的前后，用于解释图中内容。

## 三层模型

把判断拆成三层，不要混在一起：

### 第 1 层：会话级触发信号

先判断这一轮任务是否真的和“理解复杂流程代码”有关。

### 第 2 层：仓库级候选筛选

启用 skill 后，再决定先扫描哪些文件，不要一上来就全仓细读。

### 第 3 层：文件级理解成本评分

最后才对候选文件做门控和评分，决定：

- 是否值得补图
- 是否直接进入生成
- 需要哪几类图

详细阈值和排除规则见 `references/heuristics.md`。

## 何时启用

这些情况应优先启用：

- 用户要理解流程复杂、协作复杂、异步复杂或状态复杂的代码。
- 用户明确提出“画图”“做可视化文档”“生成 PlantUML / SVG / Markdown”。
- 代码不一定很长，但主流程、分支、协作者、状态迁移或并发顺序难以快速看懂。
- 文件或符号明显带有 `workflow`、`orchestrator`、`pipeline`、`controller`、`handler`、`dispatch` 等编排特征。
- 用户要扫描仓库，找出最值得补图的热点文件。
- 用户在处理 AI 生成代码，需要通过图降低理解门槛。

这些情况不要默认启用：

- 只是普通 CRUD、数据定义、常量表。
- 用户只想改局部样式、文案或一小段明显逻辑。
- 目标只是快速修一个明确 bug，且没有流程理解瓶颈。

## 工作流

### 1. 先扫描

先运行：

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

### 3. 生成图优先文档

确认后运行：

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
- 刷新总览页
- 清理旧的单张 `*-architecture.*` 遗留产物

脚本不负责最终业务语义完稿。生成后要再读源码，把真实角色名、依赖名、条件和结论补齐。

## 输出规则

默认输出到目标仓库：

- `docs/workflow-viz/insights/<group>/analysis.md`锛氬彧鍦ㄦ湰杞彧鏈?1 涓?Markdown 鏃朵娇鐢?
- `docs/workflow-viz/insights/<group>/<file>.md`锛氬鏂囦欢鎵规涓嬫寜鏂囦欢鍚勮嚜鐢熸垚锛屼笉鍐嶇敓鎴?index.md`
- `docs/workflow-viz/code/<slug>-<diagram>.puml`
- `docs/workflow-viz/charts/<slug>-<diagram>.svg`

默认图组顺序：

- `architecture-context`：架构总览图
- `architecture-modules`：模块拆解图
- `architecture-dependencies`：依赖职责图
- `activity`：主流程活动图
- `sequence`：协作顺序图

按需补充：

- `branch-decision`
- `state`
- `async-concurrency`
- `data-flow`

## 文档写法

- 一页只讲一个热点文件。
- 先放少量开头引导，再进入架构图组三连。
- 每张图都使用“图前说明 -> 图片 -> 图后解读”的结构。
- 不要把大段正文放在远离图的位置。
- 不要把源码路径、函数名说明、评分细节塞进图里；这些信息放在图外文本即可。

## 参考资料

- 候选筛选、阈值和评分：`references/heuristics.md`
- 图类型选择：`references/diagram-selection.md`
- Markdown 结构规范：`references/markdown-template.md`
- PlantUML 运行时与预检：`references/runtime-setup.md`
