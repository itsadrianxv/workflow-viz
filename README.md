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

这个仓库已经带了 Claude Code plugin 和 hook：

- plugin 清单在 `.claude-plugin/plugin.json`
- marketplace 清单在 `.claude-plugin/marketplace.json`
- hook 配置在 `hooks/hooks.json`
- Windows 入口脚本在 `hooks/run-hook.cmd`

最推荐的用法，是把仓库当作本地 marketplace 安装：

```text
/plugin marketplace add <workflow-viz 仓库根目录>
/plugin install workflow-viz@hungyuk/workflow-viz-dev
```

如果你只是想本地调试或临时试用，也可以直接在仓库根目录启动：

```bash
claude --plugin-dir .
```

安装后建议补两项运行条件：

- Claude Code 版本至少为 `1.0.33`
- 在 Claude 的运行环境里可以找到 `bash` 和 `python3`

当前 hook 会在 `Write` / `Edit` 后通过 `hooks/run-hook.cmd` 调用 `hooks/post-tool-complexity-check`。它只分析刚修改的代码文件；当理解成本评分达到 60 分以上时，会向 Claude 注入额外上下文，提醒它考虑使用 `workflow-viz`。它不会自动改源码，也不会未经确认就直接生成文档。

插件更新后，运行 `/reload-plugins` 或直接重启 Claude Code。

在 Claude Code 里可以直接这样提：

- “用 workflow-viz 扫描这个仓库里最值得可视化的热点文件。”
- “对 `src/foo.py` 运行 workflow-viz，并把结果生成到 `docs/workflow-viz`。”
- “先 scan，再决定要不要 generate。”

想进一步自定义 plugin / hook 配置，可以参考 Claude Code 官方文档：

- [Plugins](https://docs.claude.com/en/docs/claude-code/plugins)
- [Hooks](https://docs.claude.com/en/docs/claude-code/hooks)

## 在 Codex 中使用

这个项目本质上也是一个 Codex skill。最简单的接入方式，是把整个仓库放到 Codex 的 skill 目录里，并保留 `SKILL.md`、`references/`、`scripts/` 的相对路径关系。

Windows 上常见位置是：

```powershell
$target = "$env:USERPROFILE\\.codex\\skills\\workflow-viz"
```

把仓库放好后重启 Codex。之后只要在对话里明确提到 `workflow-viz`，或者直接描述“扫描热点”“生成架构优先文档”这类任务，Codex 就能按 `SKILL.md` 中的规则调用这个项目。

如果你的 Codex 版本使用 `~/.agents/skills` 做发现目录，也可以把当前仓库做一个软链接或目录联接到 `~/.agents/skills/workflow-viz`。

在 Codex 里常见的用法是：

- “扫描这个仓库里理解成本最高的文件。”
- “为这个 orchestrator / workflow 文件生成 architecture-first 的可视化文档。”
- “先用 workflow-viz 判断值不值得画，再决定是否生成。”

需要注意的是：Codex 主要使用这个仓库里的 `SKILL.md` 和 Python 脚本，不会自动读取 `.claude-plugin` 下面的 Claude Code hook。换句话说，Claude 的 `PostToolUse` 提示增强是 Claude 专用能力，Codex 侧默认还是走显式 skill 调用。

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
