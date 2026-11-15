# dev-flow

> 一套把「想法」推成「已实现且可验收」的 skill 套件：从定位工程、盘问需求，到 delta 规格、架构文档、任务拆分、执行边界、实现、评审，最后把结果合并回基线。

dev-flow 是 13 个彼此独立的 skill，由一个编排入口串联。所有产物都是纯 Markdown，落在目标工程的 `codespec/` 目录里；不需要数据库、不需要服务、不绑定任何编辑器。

## 它解决什么

- **改动落在哪个工程**：多仓库/多模块工作区里，先定位再动手，避免把规格写进错误的地方
- **需求没说清就动手**：用设计树盘问，把隐含假设逼出来
- **规格与实现脱节**：`spec.md` 是长期基线，每次变更只写 delta，实现完成后合并回去
- **范围失控**：`scope.md` 定义可改白名单，执行与评审都按它逐文件核对
- **完成全凭自觉**：验收命令、评审证据、确定性校验脚本三道门

## 流水线

```
df-init（编排：持有 df_stage，按阶段驱动，可中断续跑）
  │
  ├─ df-env        定位工程、建 codespec 骨架、定 US 编号
  ├─ df-proposal   扫描整个工程，建立全局 spec.md / design.md
  ├─ df-delta-spec 本次变更的需求差异
  ├─ df-delta-design 本次变更的设计落点与基线差异
  ├─ df-arch       架构文档 docs/arch_{US}.md 与项目 README
  ├─ df-task       任务拆分（方式/依赖/验收命令/自测）
  ├─ df-scope      执行边界：可改白名单 / 明确不动 / 越界处置
  ├─ df-validation 文档级检查：遗漏、冲突、无法实现，分三档
  ├─ df-solver     并行实现（主 Agent / subagent / 后台），合并基线
  └─ df-review     双向代码评审：评审包、两轴检查、先验证再接受
```

三个可被任意 skill 调用的公共能力：

| skill | 用途 |
|---|---|
| `df-env` | 定位工程与 US 编号（变量缺失时先跑它） |
| `df-grill` | 设计树盘问；够格的决策可记 ADR |
| `df-tdd` | 红→绿循环、seam 约定、三个反模式 |

## 产物结构

```
<目标工程>/codespec/
  specs/
    spec.md                全局能力基线
    design.md              全局决策与风险
    <capability>/spec.md   可选：按能力拆分的规格
  changes/
    US-{时间戳}-{序号}-{功能名}/
      delta-spec.md        本次需求差异
      delta-design.md      本次设计落点
      task.md              任务清单与详情
      scope.md             执行边界
      validation.md        文档检查与处理记录
      review.md            评审意见与回归证据
    archive/               已归档的变更
<目标工程>/docs/
  arch_{US}.md             本次架构文档（收尾时并入 arch.md）
  arch.md                  合并后的架构文档
  adr/                     架构决策记录
```

## 安装

### 作为 DSH 插件（可从目录直接装）

```bash
dsh plugin --profile web add /path/to/dev-flow
# 再在 ~/.dsh/profiles/web/cordis.patch.yml 追加：
#   - id: dev-flow-skills
#     name: "dev-flow"
```

`index.js` 是一个 cordis 插件：扫描同级 `df-*/SKILL.md` 并注册成 skill provider，装的是 link 依赖，改文件即生效。

### 作为项目级 skill

把仓库根作为 skill root（`customSkillDirs`），或把每个 `df-*` 目录链接到 `.agents/skills/`：

```powershell
New-Item -ItemType Junction -Path .agents\skills\df-env -Target .\df-env
```

## 使用

```
/df-init            从这里开始：定位工程、选 US、按阶段推进
/df-grill           只想先把想法盘清楚时单独用
/df-tdd             TDD 规则（实现阶段被调用）
```

每个阶段结束都会出一份简报并等你确认；不符合就直接输入修改意见，最多迭代 3 轮。

## 自检脚本

```bash
python scripts/check_skills.py                  # 套件一致性：命名、指针、独立性、拷贝漂移
python df-validation/scripts/check.py --proj <工程> --us <US>   # 产物结构校验
```

`check.py` 在两处可用：`df-validation`（文档阶段）与 `df-solver`（合并基线后复检）；两份拷贝必须字节一致，`check_skills.py` 会拦。

## 设计原则

- **skill 之间不互相调用**：除编排入口外，每个 skill 只与文件打交道（`task.md`、`scope.md`…），换掉任何一个不影响其余
- **确定性优先**：能写成脚本校验的规则绝不留给模型肉眼判断
- **不落状态文件**：阶段状态从磁盘产物推断，读的是 `status: done` 与文件存在性
- **证据先于结论**：没有命令输出，不算完成

## 仓库结构

```
df-*/SKILL.md        13 个 skill
df-*/templates/      产物模板（spec/design/delta/task/scope/validation/review/arch/README/ADR）
df-*/scripts/        随 skill 分发的脚本（扫描、校验、归档、合并）
df-*/references/     语言规范与坏味道（C/C++/Java/Python/Go/Rust/JS/TS）
index.js             插件入口：把 df-* 注册成 skill provider
scripts/             套件级自检（check_skills.py、smoke-plugin.mjs）
```

## 许可

MIT
