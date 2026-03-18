# 图类型选择

## 设计原则

`workflow-viz` 现在默认服务于单文件理解，不再把“系统总体架构”当作统一第一问题。

选择逻辑分两层：

1. 先按文件角色给固定前三张图
2. 再按状态、异步、分支、数据流等强信号补图或提权

## 核心图种

- `sequence`
- `activity`
- `domain-structure`
- `boundary-context`
- `state`
- `data-flow`

## 补充图种

- `branch-decision`
- `async-concurrency`
- `object-snapshot`

## 角色模板

### 应用服务

- `sequence`
- `activity`
- `boundary-context`

### 领域服务

- `domain-structure`
- `boundary-context`
- `activity`

### 实体

- `domain-structure`
- `boundary-context`
- `state`

### 聚合根

- `state`
- `boundary-context`
- `domain-structure`

### 仓储

- `boundary-context`
- `data-flow`
- `sequence`

### 基础设施适配器

- `sequence`
- `boundary-context`
- `data-flow`

### 工作流编排

- `sequence`
- `activity`
- `boundary-context`

## 按条件增加或提权

### `branch-decision`

满足以下任一情况时增加：

- 条件分支明显多
- 守卫逻辑多
- 提前返回或短路路径多
- 异常或降级路径与正常路径交织

### `state`

当存在明显状态迁移时增加或提权：

- 生命周期阶段明显
- `state` / `status` / `phase` / `mode` 切换明显
- 激活、暂停、恢复、过期、关闭等模式变化明显

### `async-concurrency`

当异步复杂性明显时增加：

- `async/await`
- Promise 链
- 事件驱动
- queue / worker / scheduler
- thread / lock / channel / semaphore
- timeout / retry / backoff
- fan-out / fan-in / gather / race

### `data-flow`

当跨模块协作或数据变换明显时增加或提权：

- 输入在多个协作者之间流转
- 数据变换链较长
- 存在明显聚合、拆分、归并、序列化、映射过程

### `object-snapshot`

当实体或聚合根需要解释某个关键业务时刻的对象形态时增加。

## 命名迁移

旧的架构图三连不再是默认模板：

- `architecture-context` -> 语义上迁移到 `boundary-context`
- `architecture-modules` -> 语义上迁移到 `domain-structure`
- `architecture-dependencies` -> 并入 `boundary-context`
