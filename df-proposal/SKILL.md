---
name: df-proposal
description: dev-flow 的基线阶段。扫描整个工程后，在 specs 目录里建立全局的 spec.md 与 design.md（含架构图）；只创建不演进，改动一律走 delta，基线由实现后合并。
---

df-proposal 只做一件事：**把整个工程固化成规格基线**——`spec.md`（要什么）与 `design.md`（怎么做，含架构与图形）。不改代码。

基线是**整个工程**的，不是本次需求的：`spec.md` 写工程现在具备的全部能力，`design.md` 写工程现在的架构与依赖。

## 变量

| 变量 | 用途 | 说明 |
|---|---|---|
| `df_proj_dir` | 工程根，扫描与落盘的根 | 重要!!，禁止丢弃 |
| `df_us_id` | 本次变更编号 | 重要!!，禁止丢弃 |
| `df_spec_dir` | `{df_proj_dir}/codespec/specs`，两个基线文件的落点 | - |

变量缺失或对不上时，先跑一次 `df-env` 补齐再用。

## 步骤

### 1. 判基线

基线由"spec 一侧 + design.md"组成。spec 一侧有两种布局，都算合法：

- 单文件：`{df_spec_dir}/spec.md`（默认，单模块或小工程）
- 按能力拆分：`{df_spec_dir}/<capability>/spec.md`，每个能力一份（工程有 3 个及以上模块时推荐）

| 情况 | 动作 |
|---|---|
| 两份都缺 | **新建**：走完整流程 |
| 只缺一份 | **补齐**：只写缺的那份，另一份原样不动 |
| 都在、都 `status: done` | **停手**：基线只读。任何改动——包括结构性修改——都走 delta；基线只在实现完成后由合并步骤更新 |
| 都在，但 `status` 不是 `done` | **补正**：先把 frontmatter 补成 `done`、按回读校验修结构，**正文不动**；补完回到上一行重新判 |

判定"完成"只认 frontmatter 的 `status: done`。文件存在不等于完成——这条也是阶段推断的依据，两边口径必须一致，否则一个要求重跑、一个拒绝写，流程会互锁。



### 2. 扫描项目

先跑脚本拿事实底图，已跳过 `codespec`、`node_modules`、`vendor`、`target`、`dist` 等目录，只统计源码、配置、文档扩展名：

```bash
python "<本 skill 目录>/scripts/scan_project.py" --root "{df_proj_dir}" --limit 3000
```

输出一行紧凑 JSON：`files`、`exts`、`dirs`（按文件数排序的前 20 个目录）、`docs`（含 `docs/adr/`）。

据此再读关键文件，别凭空想象架构：

- 既有文档：README、CONTEXT、`docs/` 下的架构说明；`docs/adr/` 里已记录的决策，新结论不得与之冲突
- 每个主要模块的入口文件（`main` / `lib` / `index` / 模块根）
- 构建清单（Cargo.toml / package.json / go.mod / pom.xml 等），判断模块划分与依赖方向

把事实底图先讲给用户听——目录、模块、依赖方向、已有 ADR——再进盘问。

### 3. 按 df-grill 盘问（方向受限）

使用 `df-grill` 的方法盘问——设计树、一轮问完前沿、每轮给推荐、事实自己查、只走 AskUserQuestion。

**着力点是冲突，不是既有代码。** 既有代码怎么写的、现有架构长什么样，都是你自己查的事实，不拿去问用户。每条问题都要能写成这个形状：

```
现在是 X（附 文件:行 或现有 spec/design 的章节），本次要变成 Y，冲突在 Z，你选哪边？
```

典型冲突：

- 与现有 `### Requirement:` 规定的行为互相矛盾
- 新组件会打破现有依赖方向，或与 `docs/adr/` 里已记录的决策冲突
- 数据所有权或公共接口要跨模块转移
- 现有契约、配置、错误码不兼容：留旧行为还是直接改
- 目录与分层要重排，牵动既有模块的引用

不许问：既有代码怎么实现、某个模块是干什么的、要不要顺手重构——没有冲突就不问。

方向另外被下面这张表限死：每个问题都必须能落进 `spec.md` 或 `design.md` 的某一节，落不进的不许问。

| 方向 | 落点 | 要问出什么 |
|---|---|---|
| 能力名与边界 | `spec.md` 的 `# <能力名> Specification`、`## Purpose` | 覆盖哪个能力、为谁解决什么问题（Purpose 至少 50 字符） |
| 目标 / 非目标 | `design.md` 的 `## Goals / Non-Goals` | 要达到什么；**明确不做什么** |
| 可验收需求 | `spec.md` 的 `## Requirements` | 每条一句话 SHALL + 至少一个 WHEN/THEN 场景 |

| 关键取舍与风险 | `design.md` 的 `## Decisions`、`## Risks / Trade-offs` | 选了什么、为什么、否掉哪些替代；已知风险与代价 |

**不许问**：实现细节（改哪个文件/函数、依赖版本）、排期与人力、测试与 CI 细节、提交与分支规范、运营与商业决策。

**收口条件**：五个方向各至少一条已定结论、且没有悬空的"关键取舍"，才停止盘问进入写盘。仍有可事后补的空白时不许静默——落到文字里标 `假设：<内容>`，交付时点名。

### 4. 写 spec.md

按 `templates/spec.md` 填，落盘到 `{df_spec_dir}/spec.md`。**全局口径**：

- 只写工程**已经具备**的能力；全篇现在时，不出现"将要""改为""新增"
- 工程有多个模块时，按模块组织 `### Requirement:`，一节一个可观测契约
- 模块达到 3 个以上时，建议按能力拆成多份 `specs/<capability>/spec.md`（每份自带 Purpose 与 Requirements）；拆不拆先问一句，别自作主张改动已有布局

硬性要求（openspec 校验口径）：

- 必须有 `## Purpose` 与 `## Requirements`；`## Purpose` 至少 50 字符
- 每条需求写成 `### Requirement: <名字>`，正文用 `SHALL` 陈述
- **每条需求至少一个 `#### Scenario:`**，场景体固定 `- **WHEN** ...` / `- **THEN** ...`
- 模板里的 `<...>` 与 HTML 注释全部替换为真实内容，不留一处

### 5. 写 design.md

按 `templates/design.md` 填，落盘到 `{df_spec_dir}/design.md`，**七节齐全**，全部描述现有架构。

唯一例外是绿地项目：工程里还没有实现时，基线写已确定的目标架构，并在 `## Context` 首行写明 `尚未实现`。

1. `## Context` —— 现状与约束，不重复 spec 的动机
2. `## Goals / Non-Goals` —— 两段都要，非目标不能省
3. `## Decisions` —— 决策 + 理由 + 被否掉的替代方案；该决策若已在 `docs/adr/` 记录，写链接加一句摘要即可，不复述全文（ADR 是事实源）
4. `## Risks / Trade-offs` —— 已知风险与取舍

**架构与图不在本文件**：上下文、分层、组件、时序、部署、UML 成文在 `docs/arch_{US}.md`，并按 US 合并进 `docs/arch.md`。design.md 写决策，别重复画图。

**图一律用 Mermaid 代码块**，并遵守三条：

- 至少要有一张系统架构图（`flowchart`）和一张依赖/组件图（`flowchart` 或 `classDiagram`）
- 节点名必须是扫描结果或实读文件里真实存在的目录、crate、包、类型，不许画想象中的组件
- 边的方向 = 代码里真实的依赖方向（谁 `use` 谁），不是"看起来合理"的方向

### 6. 回读校验

写完立刻回读两份文件：

- 每个 spec 文件：`## Purpose`（≥ 50 字符）、`## Requirements` 齐备，且每个 `### Requirement:` 后至少一个 `#### Scenario:`
- `design.md`：四节齐全（Context / Goals-Non-Goals / Decisions / Risks-Trade-offs）
- 每个 ```mermaid 围栏都闭合，且至少一张架构图 + 一张依赖图
- 抽查图里 3 个节点名，必须能在扫描结果或实读文件中找到
- 正文不得出现"将要/改为/新增"；基线只描述已成立的事实
- frontmatter `status` 改成 `done`
- 任一不满足 → 就地补齐再看；补不上就报出缺哪节，不要让半成品留在磁盘上

### 7. 简报与确认

收尾前输出一段简报（不超过 8 行），然后在同一条消息里提一题。简报至少包含：

- 落盘路径：`spec.md`、`design.md`
- 能力与需求条数；design 七节齐备，架构图与依赖图各几张
- 绿地项目点名 `尚未实现`；说明基线只创建、未演进（本次改动走 delta）
- 仍然存在的假设（没有就写"无"）

```js
AskUserQuestion({
  "questions": [
    {
      "header": "验收（要改什么就直接输入）",
      "question": "简报如上，符合你的要求吗？不符合就直接输入要改的地方。",
      "options": [
        {"label": "符合", "description": "两份基线定稿"}
      ],
      "multiSelect": false
    }
  ]
})
```

- 只有两类回答：`符合`，或用户直接输入修改意见
- 用户输入 → 按意见改 → 重新出简报 → 再问一次
- **迭代上限 3 轮**；到顶仍未确认，列出未达成项并停手，不再自行修改

## 边界

- **只写两个基线文件**：`{df_spec_dir}/spec.md`、`{df_spec_dir}/design.md`。不写 `delta-spec.md`、`delta-design.md`、`task.md`、`validation.md`。
- **基线只有一个写者**：本 skill 只负责创建与补正；实现之后的合并由那一步独占，本 skill 不再改基线。
- **不许用"文件已存在"当停手理由**：只有 `status: done` 才算定稿；不 done 就必须补正，否则 proposal 阶段永远推不动。
- **扫描只读**：不改任何被扫描的文件，不生成缓存。
- **不改代码**：本 skill 只产出文档。
- **不推进 `df_stage`**。
- **提问只用 AskUserQuestion**，方向受第 3 步表格约束。
- **不留占位符**：任何 `<...>`、`<!-- -->`、`TODO` 出现在落盘文件里都算未完成。
- **宿主没有 AskUserQuestion 时**：退回编号列表提问，不跳过提问。
