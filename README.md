# Workflow Viz

让 coding agent 不只是“会写代码”，也更会帮助人理解代码。

`workflow-viz` 是一个面向 Codex 类 coding agent 的技能：当代码的理解成本明显高于阅读收益时，它会先识别哪些文件真正值得可视化，再生成一套以架构图优先、图片优先的 PlantUML + SVG + Markdown 文档，帮助开发者更快建立心智模型。

## 为什么会有这个项目

在 vibe coding 时代，一个越来越明显的问题是：

- 代码生成速度已经常常超过人的理解速度
- 很多“看起来不长”的代码，其实比“大文件”更难读
- AI 生成代码尤其容易出现流程绕、分支深、协作多、异步重的情况
- 当开发者只能线性读代码时，很难快速建立“主流程、分支、协作者、状态、并发时序”的完整图景

结果就是：

- 改动变慢
- review 变难
- debug 变痛苦
- 团队对 AI 生成代码的不信任感上升

`workflow-viz` 就是为这个痛点而生的。

它不试图把所有代码都画成图，而是先回答一个更重要的问题：

“这段代码，真的值得可视化吗？”

## 它解决什么问题

`workflow-viz` 提供的是一套“先判断，再制图，再沉淀”的解决方案：

1. 先判断当前任务是否真的需要启用可视化理解流程
2. 再从仓库里筛出最值得分析的候选文件
3. 最后对候选文件做理解成本评分，决定是否建议生成文档

一旦进入生成流程，它会输出：

- PlantUML 源码
- 渲染后的 SVG 图
- 以图片为主的 Markdown 洞察文档
- 总览索引页

默认产物目录：

```text
docs/workflow-viz/insights/
docs/workflow-viz/code/
docs/workflow-viz/charts/
```

## 这个 skill 的特点

### 1. 不是“把代码画出来”，而是“挑值得画的代码”

很多可视化工具的问题在于：只要给代码，就开始画。

`workflow-viz` 更关心的是：

- 这段代码是不是高理解成本
- 它难在结构、协作、异步，还是状态迁移
- 该补哪几张图，才真正有帮助

### 2. 触发依据不靠代码行数

它默认使用静态启发式来评估理解成本，而不是简单地看文件长短。

重点考虑：

- 圈复杂度
- 嵌套深度与分支密度
- 异常 / 重试 / 降级路径
- 跨模块协作和调用扇出
- 异步 / 并发模式
- 状态迁移
- 编排型命名特征

这让它更适合处理那些“行数不大，但真的很难懂”的 AI 生成代码。

### 3. 三层模型更适合 agent 使用

`workflow-viz` 不是一上来就扫全仓。

它把决策拆成三层：

- 第 1 层：会话级触发信号
- 第 2 层：仓库级候选筛选
- 第 3 层：文件级理解成本评分

这能让 agent 在真实协作里更克制、更精准，也更省上下文。

### 4. 架构优先，而不是只画流程

当前版本默认优先生成一组架构图：

- `architecture-context`
- `architecture-modules`
- `architecture-dependencies`

然后再补：

- `activity`
- `sequence`
- `branch-decision`
- `state`
- `async-concurrency`
- `data-flow`

这意味着它不是只告诉你“代码怎么跑”，而是先帮助你理解“它在系统里是什么、和谁协作、职责怎么拆”。

### 5. 图片优先的文档输出

生成后的 Markdown 文档不是大段解释文字，而是以图为主、图前图后配少量说明的“洞察页”。

这类文档更适合：

- review
- onboarding
- AI 生成代码的二次理解
- 后续维护

## 快速开始

### 1. 先检查渲染环境

```bash
python scripts/workflow_viz.py doctor --repo-root <repo>
```

### 2. 先扫描热点

```bash
python scripts/workflow_viz.py scan --repo-root <repo>
```

只看某个文件时：

```bash
python scripts/workflow_viz.py scan --repo-root <repo> --paths path/to/file.py
```

### 3. 生成文档

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --render
```

如果你想指定 PlantUML 主题：

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --theme plain --render
```

如果你想关闭默认主题注入：

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --theme none --render
```

## 当前版本已经提供什么

- `doctor / scan / generate` 三个核心命令
- 默认输出到 `docs/workflow-viz/{insights,code,charts}`
- PlantUML 渲染运行时预检
- 面向多语言代码仓库的静态热点识别
- 架构优先的默认图组
- 中文图内标签与图片优先文档模板
- 对旧版单张 `architecture` 产物的兼容清理

## 为什么它适合开源使用

因为它解决的不是某个业务仓库的私有问题，而是一个越来越普遍的工程痛点：

“AI 能快速产出代码，但团队未必能同样快速理解代码。”

如果你也遇到这些情况，这个 skill 会很适合你：

- 你在用 Codex、Claude Code 或类似 coding agent
- 你正在维护大量 AI 生成代码
- 你觉得团队理解流程代码越来越慢
- 你希望把“画图”变成一个稳定、低摩擦、能持续更新的工程动作

## 可靠性

当前仓库已经包含针对关键行为的自动化测试，覆盖了：

- 默认输出目录
- 架构优先的推荐图组
- PlantUML 主题注入与关闭
- 图片优先 Markdown 结构
- 旧产物清理逻辑
- 文档与参考文件的一致性

## 一句话总结

`workflow-viz` 不是一个“代码转流程图”玩具。

它更像是一个给 coding agent 配的“代码理解加速器”：
先判断哪里值得可视化，再把复杂流程沉淀成真正对人有帮助的文档资产。
