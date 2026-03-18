# Workflow Viz

让 coding agent 不只会生成代码，也更会帮助人理解代码。

`workflow-viz` 是一个面向 Codex 类 coding agent 的技能：当代码的理解成本明显高于线性阅读收益时，它会先识别哪些文件真正值得可视化，再生成一套以单文件理解为中心的 PlantUML + SVG + Markdown 文档。

和旧版不同，这一版不再默认“架构图优先”，而是使用按文件角色切换的 role-based 图模板：

- 应用服务、工作流编排优先看 `sequence`
- 领域服务优先看 `domain-structure`
- 实体优先看 `domain-structure`
- 聚合根优先看 `state`
- 仓储优先看 `boundary-context`
- 基础设施适配器优先看 `sequence`

## 图种模型

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

其中：

- `domain-structure` 通常可用简化类图表达文件局部结构
- `boundary-context` 用来描述局部边界、契约和依赖，不等同于系统总体架构图

## 默认产物目录

```text
docs/workflow-viz/insights/<group>/analysis.md
docs/workflow-viz/insights/<group>/<file>.md
docs/workflow-viz/code/
docs/workflow-viz/charts/
```

## 在 Claude Code 中使用

- 把仓库当作本地 marketplace 安装：先执行 `/plugin marketplace add <workflow-viz 仓库根目录>`，再执行 `/plugin install workflow-viz@hungyuk/workflow-viz-dev`
- 本项目已内置 `PostToolUse` hook；当 Claude 执行 `Write` 或 `Edit` 时，会通过 `hooks/run-hook.cmd` 触发 `hooks/post-tool-complexity-check`
- 若想主动触发，可以直接说：“请用 workflow-viz 扫描这个仓库里最值得可视化的热点文件。”

## 在 Codex 中使用

- 全局安装：`git clone https://github.com/itsadrianxv/workflow-viz.git "$env:USERPROFILE\\.codex\\skills\\workflow-viz"`
- 项目级安装：在项目根目录执行 `git clone https://github.com/itsadrianxv/workflow-viz.git .codex/skills/workflow-viz`
- 若想主动触发，可以直接说：“请用 workflow-viz 判断这个仓库里哪些文件值得可视化，并先 scan 再决定是否 generate。”

## 最小命令流

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

覆盖默认 PlantUML 主题：

```bash
python scripts/workflow_viz.py generate --repo-root <repo> --theme plain --render
python scripts/workflow_viz.py generate --repo-root <repo> --theme none --render
```

## MIT 许可证

本项目采用 [MIT License](LICENSE) 发布。
