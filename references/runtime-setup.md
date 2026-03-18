# 运行时预检与渲染环境

## 默认策略

v1 不内置 PlantUML jar，也不依赖仓库外的手工长命令。

统一通过 `scripts/workflow_viz.py doctor` 预检运行时，再由脚本负责渲染。

默认生成产物位于 `docs/workflow-viz/insights`，并默认向每个 `.puml` 注入：

```puml
@startuml
!theme materia
```

如果用户明确要求其他主题，可通过 `generate --theme <name>` 覆盖；传 `--theme none` 时不注入主题。

## 检测顺序

PlantUML 调用方式按以下顺序解析：

1. `PLANTUML_COMMAND`
2. `PLANTUML_JAR`
3. `plantuml` 在 `PATH`
4. 常见本地 jar 路径

## 常见本地路径

脚本可尝试这些位置：

- `%USERPROFILE%\\tools\\plantuml\\plantuml.jar`
- `<repo>\\.tools\\plantuml\\plantuml.jar`
- `<repo>\\tools\\plantuml\\plantuml.jar`

## 预检要求

`doctor` 不只检查文件是否存在，还应实际尝试渲染一个最小 PlantUML 文件为 SVG。

只有真正渲染成功，才能认为环境可用。

## 缺失项时的补救

### 缺少 Java

提示安装 Java，并重新运行：

```bash
java -version
```

### 缺少 PlantUML

优先建议两种方式之一：

- 设置 `PLANTUML_JAR`
- 把 `plantuml` 加入 `PATH`

### 无法渲染

若 jar 存在但 SVG 渲染失败：

- 输出实际命令和错误信息
- 提示检查 Graphviz、Java 和 jar 版本
- 让用户先跑 `doctor` 修复，再执行 `generate --render`
