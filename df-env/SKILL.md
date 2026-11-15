---
name: df-env
description: dev-flow 的定位阶段。确定本次改动落在哪个工程、建出 codespec 目录骨架、定出 US 编号，产出 df_proj_dir、df_us_id、df_change_dir、df_spec_dir 四个变量。
---

df-env 只做三件事：**定工程**、**建目录**、**定 US 编号**。不写任何产物文件。

## 变量

| 变量 | 值 | 说明 |
|---|---|---|
| `df_proj_dir` | 工程根，绝对路径，`/` 分隔 | 重要!!，禁止丢弃 |
| `df_us_id` | `US-{YYYYMMddHHmmss}-{4位序号}-{功能名}` | 重要!!，禁止丢弃 |
| `df_change_dir` | `{df_proj_dir}/codespec/changes/{df_us_id}` | - |
| `df_spec_dir` | `{df_proj_dir}/codespec/specs` | - |

## 步骤

### 1. 定工程 df_proj_dir

**`df_proj_dir`已定义 → 跳过本步**，只校验目录还在。

抽线索：提示词里有显式路径且目录存在 → 直接进确认；否则先跑脚本拿全部候选目录的清单：

```bash
python "<本 skill 目录>/scripts/scan_projects.py" --root "{cwd}" --depth 4
```

输出一行紧凑 JSON，只有相对路径，**不打分**：

```json
{"root":"C:/projects/acme","dirs":["apps/admin","packages/order-service","packages/order-service/crates/ui","services/billing"],"truncated":false}
```

相关性由你判断：拿提示词里的模块名、技术栈词、路径片段去比 `dirs`，挑 2-4 个最相关的；都不相关、或提示词指向一个还不存在的位置时，再准备一个 `新建 - <推断的相对路径>`。候选、新建、当前工作目录合成同一题：

```js
AskUserQuestion({
  "questions": [
    {
      "header": "工程目录（可直接输入其他路径：绝对路径，或以 cwd 为基准的相对路径）",
      "question": "本次改动落在哪个目录？下面是我从 <N> 个工程目录里挑出的相关项。",
      "options": [
        {"label": "<相关候选 1>", "description": "df_proj_dir = <绝对路径>；依据：命中 <词>"},
        {"label": "<相关候选 2>", "description": "df_proj_dir = <绝对路径>；依据：命中 <词>"},
        {"label": "新建 - <推断的相对路径>", "description": "该位置还不存在，按这个位置新建一套"},
        {"label": "用当前工作目录", "description": "df_proj_dir = <cwd>"}
      ],
      "multiSelect": false
    }
  ]
})
```

用户直接输入路径时：`~` 展开、相对路径按 `{cwd}` 解析、`\\` 转 `/`、去尾斜杠，校验是目录，再把新路径填回这题重提。轮数上限 5，到顶只能选 `用当前工作目录`。

定案后当场写出值（绝对路径、`/` 分隔、无占位符）：

```
df_proj_dir = C:/projects/acme/packages/order-service
```

### 2. 建目录

一个脚本建齐 codespec 及其下的 specs、changes，幂等，不删任何已有内容：

```python
import os

base = r"{df_proj_dir}/codespec"
for d in (base, base + "/specs", base + "/changes"):
    os.makedirs(d, exist_ok=True)
```

跑完回读确认三个目录都在；失败就停在这里报错，不要带半套目录往下走。本步不设跳过：脚本幂等，跑一次比判断要不要跳过更省。

### 3. 定 US 编号 df_us_id

**已有 `df_us_id`（用户已指定某个 `US-*` 目录）→ 跳过本步**，只校验该目录存在。

**只读目录名**：列 `{df_proj_dir}/codespec/changes/` 下的 `US-*` 目录（第 2 步已建好），不打开任何产物文件。

相关性：目录名末段的功能名与提示词各切 token（中文按连续汉字、英文按单词），**交集非空即相关**，按命中 token 数排序，取 **0-3 个**。你自己按提示词生成一个新的 US 编号作为新建项。

```js
AskUserQuestion({
  "questions": [
    {
      "header": "US 编号（直接输入功能名即可新建，规则：保留中文与字母数字，空格转 -，不超 20 字）",
      "question": "这条需求归到哪个 US？下面是我挑出的相关变更，或新建一条。",
      "options": [
        {"label": "<相关目录名 1>", "description": "匹配：<命中词>"},
        {"label": "<相关目录名 2>", "description": "匹配：<命中词>"},
        {"label": "新建 - <生成的完整编号>", "description": "按提示词里的功能名补齐时间戳与 4 位序号"}
      ],
      "multiSelect": false
    }
  ]
})
```

没有相关目录时，这题只剩 `新建 - <编号>` 一项。

**这一题必须等用户回答，不许自己往下走**：

- 候选只有一个、或者一个都没有，也要问——不许因为"显然只有这一条"就直接定 `df_us_id`
- 用户没回答（跳过、只回了个表情、回了别的内容）→ 重新问这一题，不许用"新建"或"最近修改的"兜底
- `df_us_id` 定下之前，不许创建 US 目录、不许写任何产物

选候选 → `df_us_id` 即该目录名，目录已存在，跳过下面的补建。选新建或直接输入功能名 → 该输入即功能名，按下面规则补齐编号，不再多问一题：

- 时间戳：当前本地时间 `YYYYMMddHHmmss`
- 序号：已有 `US-*` 中 4 位序号最大值 +1，零填 4 位；无历史则 `0001`
- 功能名：保留中文与字母数字，空格转 `-`，去 `\ / : * ? " < > |`，连续 `-` 合并，超过 20 字截断

编号定下后补建 US 目录（幂等），再当场写出三个值：

```python
import os

os.makedirs(r"{df_proj_dir}/codespec/changes/{df_us_id}", exist_ok=True)
```

```
df_change_dir = {df_proj_dir}/codespec/changes/{df_us_id}
df_spec_dir   = {df_proj_dir}/codespec/specs/
```

## 边界

- **只建目录，不写产物**：不创建 `.md`、不填内容、不推进 `df_stage`（跑完仍是 `env`）。`spec.md`、`design.md`、`delta-spec.md`、`delta-design.md`、`task.md`、`validation.md` 全部由后续阶段创建与填充。
- **不落文件、不复述**：两个重要变量不写状态文件、不靠每步念叨；需要时从 `codespec/changes/US-*` 目录反推。
- **幂等**：重复跑不报错、不覆盖、不删除已存在的目录或文件。
- **候选只来自脚本**：相关性判断要在选项描述里写出依据（命中哪个词）；可以补 `新建`，但不能凭空编路径。
- **值不许凭记忆改写**：路径一律按目录反推的形态写，长路径不许截短。
- `df_change_dir` / `df_spec_dir` 永不单独提问，一律派生。
- 上层已有 `codespec/` 时只提示一行（父级另有规格，本次不与其共享），不改选。
- 路径展示给裸值，不加引号。
- **宿主没有 AskUserQuestion 时**：退回编号列表提问，不跳过提问。
