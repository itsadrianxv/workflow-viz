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

默认产物目录：

```text
docs/workflow-viz/insights/<group>/analysis.md
docs/workflow-viz/insights/<group>/<file>.md
docs/workflow-viz/code/
docs/workflow-viz/charts/
```

## 在 Claude Code 中使用

- 把仓库当作本地 marketplace 安装：先执行 `/plugin marketplace add <workflow-viz 仓库根目录>`，再执行 `/plugin install workflow-viz@hungyuk/workflow-viz-dev`。
- 本项目已内置 `PostToolUse` hook；当 Claude 执行 `Write` 或 `Edit` 时，会通过 `hooks/run-hook.cmd` 触发 `hooks/post-tool-complexity-check`。
- 若想主动触发，可以直接说：“请用 workflow-viz 扫描这个仓库里最值得可视化的热点文件。”

## 在 Codex 中使用

- 全局安装：`git clone https://github.com/itsadrianxv/workflow-viz.git "$env:USERPROFILE\\.codex\\skills\\workflow-viz"`。
- 项目级安装：在项目根目录执行 `git clone https://github.com/itsadrianxv/workflow-viz.git .codex/skills/workflow-viz`。
- 若想主动触发，可以直接说：“请用 workflow-viz 判断这个仓库里哪些文件值得可视化，并先 scan 再决定是否 generate。”

## 最小命令流

无论你从 Claude Code 还是 Codex 进入，底层调用的都是同一个 CLI：

```bash
python scripts/workflow_viz.py doctor --repo-root <repo>
python scripts/workflow_viz.py scan --repo-root <repo>
python scripts/workflow_viz.py generate --repo-root <repo> --render
```

只看某个文件时：

```bash
python scripts/workflow_viz.py scan --repo-root <repo> --paths path/to/file.py
python scripts/workflow_viz.py generate --repo-root <repo> --paths path/to/file.py --render
```

如果你想覆盖默认 PlantUML 主题：

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --theme plain --render
python scripts/workflow_viz.py generate --repo-root <repo> --theme none --render
```

默认输出仍然在：

- `docs/workflow-viz/insights/<group>/analysis.md` 或 `docs/workflow-viz/insights/<group>/<file>.md`
- `docs/workflow-viz/code/`
- `docs/workflow-viz/charts/`

## MIT 许可证

本项目采用 [MIT License](LICENSE) 发布。

你可以在保留版权声明和许可声明的前提下使用、复制、修改、分发和再授权本项目，这也让它更适合被集成进团队内部工具链或二次封装成自己的 agent 工作流。
