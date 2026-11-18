---
name: df-init
description: dev-flow 的编排入口。先调用 df-env 定位工程与 US 编号，再按阶段顺序驱动 proposal 到 solver，持有并推进 df_stage，支持中断后续跑。
---

df-init 是唯一**持有并推进 `df_stage`** 的地方，其余 skill 只读。它自己不产出规格、设计、任务或代码——只决定"下一步该谁做"，并在每一阶段验收通过后把状态推进一格。

## 变量

| 变量 | 来源 | 说明 |
|---|---|---|
| `df_proj_dir` | `df-env` | 重要!!，禁止丢弃 |
| `df_us_id` | `df-env` | 重要!!，禁止丢弃 |
| `df_change_dir` | 派生 | `{df_proj_dir}/codespec/changes/{df_us_id}` |
| `df_spec_dir` | 派生 | `{df_proj_dir}/codespec/specs` |
| `df_stage` | 本 skill 推断与推进 | 不落文件，每次进场重建 |

`df_stage` 的取值与顺序：

```
env --> proposal --> delta-spec --> delta-design --> arch --> task --> scope --> validation --> solver --> review --> done
```

## 步骤

### 1. 定位（调用 df-env）

`df_proj_dir` 或 `df_us_id` 缺失时，先调用 `df-env`：它负责扫候选目录、建 `codespec` 骨架、定 US 编号。两个都有就跳过。

### 2. 重建 df_stage

进场第一件事是按磁盘现状推断进度，不依赖记忆——`df_stage` 从不落盘：

| 磁盘现状 | `df_stage` |
|---|---|
| `{df_change_dir}` 不存在 | `env` |
| 基线 spec（`specs/spec.md` 或 `specs/<capability>/spec.md`）一份都没有、或 `design.md` 缺失 | `proposal`（建基线形态） |
| 基线齐备，但 `proposal.md` 缺失或不是 `done` | `proposal`（仅盘问形态） |
| `delta-spec.md` 缺失或不是 `done` | `delta-spec` |
| `delta-design.md` 缺失或不是 `done` | `delta-design` |
| `docs/arch_{df_us_id}.md` 不在，且 `docs/arch.md` 里也没有 `df-arch:{df_us_id}` 标记 | `arch` |
| `task.md` 缺失或不是 `done` | `task` |
| `scope.md` 缺失或不是 `done` | `scope` |
| `validation.md` 缺失或不是 `done` | `validation` |
| `task.md` 里仍有非`完成`的任务 | `solver` |
| `review.md` 缺失或不是 `done` | `review` |
| 以上全部满足 | `done` |

判据只有一条：**产物在、且自报 `status: done`**。缺一个字段就按上一阶段算，宁可重跑一次，也不要带着半成品往下走。

扫描面只有 `changes/US-*`：已归档到 `changes/archive/` 的变更不再参与推断，也不会出现在总览里。

### 3. 总览与选择

扫 `{df_proj_dir}/codespec/changes/` 下所有 `US-*` 目录，对每条用第 2 步的规则推断阶段，列一张表（编号 / 功能名 / 当前阶段 / 完成度）。然后提一题：

```js
AskUserQuestion({
  "questions": [
    {
      "header": "从哪条开始（也可直接输入 US 编号）",
      "question": "下面是在飞的变更，选一条继续，或新建一条。",
      "options": [
        {"label": "<US 编号 1> - <功能名>", "description": "当前阶段：<df_stage>，剩余：<还剩几步>"},
        {"label": "<US 编号 2> - <功能名>", "description": "当前阶段：<df_stage>，剩余：<还剩几步>"},
        {"label": "新建一条", "description": "交给 df-env 定工程与编号，从 env 阶段开始"}
      ],
      "multiSelect": false
    }
  ]
})
```

**这一题不许省略**：在飞变更只有一条时也要问，不许因为"只剩一条"就直接进入该阶段；用户没明确选中某条之前，不许调用任何阶段 skill。

### 4. 逐阶段驱动

从 `df_stage` 指向的阶段开始，按顺序调用对应 skill：

| 阶段 | 调用的 skill | 进入条件 |
|---|---|---|
| `proposal` | `df-proposal` | 基线缺失，**或 `proposal.md` 缺失/未 done** |
| `delta-spec` | `df-delta-spec` | 基线已 `done` |
| `delta-design` | `df-delta-design` | `delta-spec.md` 已 `done` |
| `arch` | `df-arch` | `delta-design.md` 已 `done` |
| `task` | `df-task` | `docs/arch_{df_us_id}.md` 已生成且 `README.md` 已更新 |
| `scope` | `df-scope` | `task.md` 已 `done` |
| `validation` | `df-validation` | `scope.md` 已 `done` |
| `solver` | `df-solver` | `validation.md` 已 `done` |
| `review` | `df-review` | 全部任务完成且基线已合并 |

推进规则：

- 每阶段由**它自己**出简报并问用户验收；用户点`符合`之后，df-init 才把 `df_stage` 推进一格
- 用户输入修改意见 → 交回该阶段迭代，`df_stage` 保持不动
- 阶段产物已 `done` → 跳过该阶段，直接进入下一格（可重复多次）
- `proposal` 阶段有两条路：基线缺失就建基线（写 `spec.md` / `design.md`），基线齐备就只盘问、只写 `proposal.md`——**两种情况都要有 `proposal.md`**
- **不许跳阶段**，也不许因为"看起来没必要"而跳过 validation
- 任一阶段报错或阻塞 → 停下并报告卡在哪，不擅自换路

### 5. 收尾汇报

`df_stage` 到 `done` 时输出一份总汇（不超过 8 行）：

- 本次变更：`{df_us_id}` 与其功能名
- 产物的路径与最终状态（proposal / spec 侧 / design.md / delta-spec / delta-design / arch / task / scope / validation / review）
- 任务完成情况：`完成/总数`，阻塞项点名
- 评审结论：`review.md` 的分档分布与"严重剩余 0"
- 基线是否已合并（spec 侧每个文件与 `design.md` 的 `status`）
- 遗留项（来自 `validation.md`）

这一步不再问验收——每个阶段已经问过了，重复提问只会让用户厌烦。若用户要改，回第 4 步重进对应阶段。

汇报之前先把架构文档合并掉——不合并就归档，本次架构信息会随 change 目录一起被埋起来：

```bash
python "<本 skill 目录>/scripts/merge_arch.py" --proj "{df_proj_dir}" --us "{df_us_id}"
```

- 把 `docs/arch_{df_us_id}.md` 按 `<!-- df-arch:<US> -->` 标记追加进 `docs/arch.md`，随后删除 per-US 文件
- 幂等：标记已存在时只做删除，不重复追加
- 退出码非 0 就停下报告，**不要带着未合并的架构去归档**
- 合并成功后在总汇里加一行"架构已并入 `docs/arch.md`"

汇报之后提一问，只关于归档：

```js
AskUserQuestion({
  "questions": [
    {
      "header": "归档（也可直接输入保留理由）",
      "question": "这条变更已完成，是否归档？归档后它不再出现在在飞列表里，磁盘上仍保留在 changes/archive/ 下。",
      "options": [
        {"label": "归档 (Recommended)", "description": "changes/<US> 移到 changes/archive/<US>，六份产物原样保留"},
        {"label": "暂不归档", "description": "继续留在在飞列表，之后可再归档"}
      ],
      "multiSelect": false
    }
  ]
})
```

归档用脚本，不手搬目录：

```bash
python "<本 skill 目录>/scripts/archive_change.py" --proj "{df_proj_dir}" --us "{df_us_id}"
```

- 退出码 0 才算归档成功；目标已存在或源目录不在都返回非 0 并说明原因
- 归档不是删除：产物一份不少，只是离开 `changes/US-*` 扫描面
- 归档后不再对这条变更调用任何阶段 skill；要改就开新 US

## 边界

- **只编排，不产出**：不写 `spec.md`、`design.md`、`delta-*`、`task.md`、`validation.md`，也不写代码。
- **只有本 skill 推进 `df_stage`**：其他 skill 只读，不许自行推进。
- **不落盘 `df_stage`**：每步都从磁盘重建，不靠记忆也不写状态文件。
- **不跳阶段、不并行阶段**：阶段之间有产物依赖，跳步只会让下游读到半成品。
- **归档只移动目录**：不删产物、不改 status，也不动已合并的基线。
- **评审后基线必须再一致**：`df-review` 若有触及需求/结构的代码改动，先让上游更新 delta，再让 `df-solver` 重跑合并。
- **架构合并归本 skill**：`df-arch` 只写 per-US 的 `arch_{US}.md`，合并进 `docs/arch.md` 与删除源文件都在收尾这里做。
- **提问只用 AskUserQuestion**。
- **宿主没有 AskUserQuestion 时**：退回编号列表提问，不跳过提问。
