# 贯穿执行的任务清单：计划、执行、检查三个视图（v1）

每轮开始先恢复阶段，执行时更新事实，结束后核对结果。三类清单用同一 `task_id` 关联，禁止用计划勾选代替执行，或用“生成成功”代替结果通过。用户原话、专业规则与 AI 建议分别标明来源。

面向用户只维护一份连续的 `task-ledger.json/.md`，包含要求/来源、验收标准、状态、实际完成及依据、必要证据；三张视图服务于该总清单，不要求用户分别阅读。开始前逐项对应要求，过程中执行并更新，结束逐项交代结果。状态区分未做、执行中、已执行未验证、受阻/待核实、检查未通过、已完成检查。工具生成成功只能说明产物已返回，不能单凭它填完成检查。

复杂生图轮次在已有输出目录维护，不额外造报告项目；简单问答或无需产物的任务在回复中简短维护即可，不强行落盘。只在关键变化时汇报，不逐项播报常规操作。未完成项记录后继续处理可推进部分，仅确需用户决定或介入时提问。

## 开始前：任务清单

记录当前阶段、上轮实际完成状态、用户原话及来源、选中对象、修改要求、下一阶段、应出数量、是否明确授权跳步。查上轮 bundle、receipt、视觉报告及当前回答；文件冲突或缺失先查证，不自行补确认。

| 任务编号 | 要做什么 | 依据/来源 | 应交付什么 | 可观察的通过条件 |
|---|---|---|---|---|
| composition-01 | 选定方向的构图变体之一 | 方向选择与“去掉锁”的原话 | 单张 PNG + Prompt | 指定关系、无锁；其余四版共覆盖至少三种 C 关系 |

数量沿用原流程：首轮 5 张、选方向后构图 5 张、选构图后精修 3 张、每步矫正 1 张。`选择 + 修改` 必须分开记录。例如首轮后“优化第5个，去掉锁”是选方向且修改整轮元素，下一步仍为五版构图。不能将“这个”“继续优化”或一个局部修改当成跳步依据。用户明确要求只修一张、不同动作/表情或不用矫正时记录原话，按具体要求执行；不把这些例外扩散到其他任务。

非生图阶段也使用上述任务表：清点、关键词表、五方向表、用户决定、最终比较和导出都是任务项；没有发生的用户决定保持待回答。无需把每个思考动作拆成任务，保留有交付物或决策作用的项即可。

## 执行中：执行清单

| 任务编号 | 实际状态 | 实际做了什么 | 证据 | 未完成/失败原因 |
|---|---|---|---|---|
| composition-01 | not_started / running / success / failed / uncertain | 工具调用、归档、看图等事实 | 调用标识、文件绝对路径、SHA-256 | 无法确认结果填 uncertain，不重发掩盖 |

每项完成后立即更新；批量生成时按固定编号展示，不能以异步返回顺序代替用户选择的编号。准备了请求、启动了工具、生成了文件、看完了图片分别记录。离线预览显示 0 次调用；三张成功两张失败不能称五张完成。恢复任务先读执行清单，再核对证据文件，已成功不重复生成，运行中断不自动重试。

## 执行后：检查清单

| 任务编号/规则 | 预期 | 实际观察 | 检查方式与检查者 | 证据 | 结果 |
|---|---|---|---|---|---|
| composition-01 / surface | 无锁图标 | 实际看图填写 | ai_visual + 当前 Agent | 本图 SHA-256 | pass / fail / unknown |

三层结果分别记录：

- **程序检查**：数量、字段、文件可解码、参考顺序、Prompt 一致、实际尺寸和 alpha、产物哈希。
- **AI 视觉检查**：逐项看图，核对 IP、构图、表情、袋形、透视、风格；写观察与方法，不批量填 PASS。示例角度和比例标为目测，不等于精确测量。
- **人的规则和选择**：执行前把用户明确的规则纳入标准；执行后只有实际用户/审核者回答才能记录选择或接受。AI 判断“不错”不是用户验收。

单项失败/未知仍保留，汇总后按原用户节点处理：选底图、修具体项、接受已知偏差或明确跳过。检查清单有记录不等于标准已满足。不自动归档 FINAL，不增加一轮用户重复确认。

## 最终核对：先查清单有没有漏，再查结果是否通过

结束当前任务或交付最终图前，重新读取用户原始要求、全部仍有效的后续修改和指定参考材料；不能只依赖任务清单、摘要或上轮通过结论。区分用户要求与 AI 自己提出的方案，查明后续修改是补充、替换还是取消；取消/替换必须有实际用户依据。

1. 将有效要求逐项对应到任务清单。缺少对应项、范围变窄、验收条件变弱都记为遗漏；即使现有检查全 PASS，也不能把这项要求记为完成。
2. 对应实际结果和必要证据，分别写已完成什么、未做什么、哪些只完成实现尚未验证、哪些受阻或无法完成。程序检查只能证明登记项的明确子集；语义覆盖、视觉效果及人的选择各自核实。
3. 漏项补进同一任务清单并继续执行。需要改冻结的 Prompt/标准时升版，保留旧版及修改依据；不删除失败项，不把未完成降为不适用，不用 AI 建议替代用户要求。
4. 可继续推进的直接做；只有确实缺少用户决定或介入才能继续的部分才提问。无法完成时明确具体限制、已做到的范围及留下的未完成项，不制造完成声明。

最终回复按任务规模简述“要求 → 实际状态/结果 → 必要证据”。小任务一句或几句即可；已有 `task-ledger` 时直接补核对结果，不另造长报告。源需求覆盖核对是人工/Agent 的语义工作，目前助手不自动判定它完整；`checks_passed` 仅代表已经登记的检查项通过。

## 本地实现与调用路径

`task-list.json` 是冻结的计划源，`execution-list.json`、`check-list.json` 根据执行记录/视觉审阅派生；同名 Markdown 用于人阅读。改要求或 Prompt 必须新版本目录，旧标准不覆盖。

### Codex 内置 image_gen 路径

`director.py run` 接入三类清单：建立冻结任务，实际调用前后刷新执行状态，视觉项默认为 unknown。原有 bundle 校验、数量/顺序、后端与最终选择规则不变。逐图审阅后可调用 `inspect --review` 更新检查清单；审阅需要具体观察、方法和检查者，旧格式审阅不得伪补。

标准 bundle 使用 `director.py run` 准备任务；通用转接场景可用 `prepare`。两者都必须在每次调用前用 `event running` 取得已检查的 `tool` 与 `arguments`，再交给内置工具，调用后记录结果。

```bash
python3 <skill>/scripts/director.py run <bundle.json>
# 或仅在通用转接场景：python3 <skill>/scripts/director_checklists.py prepare <spec.json>
python3 <skill>/scripts/director_checklists.py event <本轮work目录> --record <running.json>
# Agent 将返回的 tool 与 arguments 原样交给内置 image_gen，一项一次调用。
python3 <skill>/scripts/director_checklists.py event <本轮work目录> --record <result.json>
python3 <skill>/scripts/director_checklists.py inspect <本轮work目录> --review <visual-review.json>
```

`run` 和 `prepare` 都不生图。`event running` 只记录派发准备，不证明工具已接受；若之后未实际调用，记录 uncertain 并说明。失败结果不冒充执行完成。每次新的工具调用均取得对应任务参数，参考重复槽位原样保留。

`spec.json` 最小结构（示例，用户决定必须换成已发生的真实回答，不照抄示例为授权）：

```json
{
  "work": "<task.root>/work/director/<round>-v1",
  "current_stage": "round1",
  "next_stage": "composition",
  "expected_count": 5,
  "decision": {
    "action": "select_direction",
    "text": "优化第5个，去掉锁",
    "source": "实际用户消息的定位记录",
    "selected_id": "用户实际选中的图编号"
  },
  "modifications": [{"text": "去掉锁", "scope": "本轮全部五版", "source": "同上"}],
  "jobs": []
}
```

`jobs` 填足五项；每项包含 `id / name / prompt / reference_paths / output / checks`。`checks` 是具体预期文字的键值表。`output` 位于 Desktop/codex 项目输出目录。`reference_paths` 是有序绝对路径数组，风格/IP 同图时重复填。

动作支持 `confirm_directions`（directions→round1）、`select_direction`（round1→composition）、`select_composition`（composition→refinement）、`modify`（保留当前阶段和数量）。精修三张默认同一 Prompt；用户明确要求三种动作等时，用 `distinct_prompts: {text, source}` 记录实际要求。明确改阶段/数量用 `explicit_override`，另提供 `override: {text, source, stage, count}`；“改细节”本身不能作为跳步原话。

执行事件：`{task_id, status: "running"}`；结果事件：`{task_id, status: "success", tool_call_id, path}`。失败/未知事件还需 `reason`。工具临时输出可位于工具默认目录，事件处理器验证 PNG 后复制到计划中已确认的项目输出路径；不会覆盖已有文件。调用标识只是来源记录，不是工具端认证。

视觉审阅：`items.<task_id>.image_sha256` 绑定实际图片；`checks.<规则名>` 填 `expected / observed / verdict / reviewer / reviewer_kind / method`，`reviewer_kind` 为 program 或 ai_visual。只有真实用户已回答时才加 `human_decision: {selected_id, text, source}`。这条记录是转录，不宣称认证过用户。

## 能验证与不能保证的边界

助手可拒绝错误的声明阶段/数量、缺项、重复派发、变化后的参考、失配的图片/审阅哈希，并避免自动填视觉与人工 PASS。它不能可靠地自行理解用户自然语言、认证 Agent 转录的选择，或阻止 Agent 绕过助手直接调用内置工具。三类清单降低遗漏并让遗漏可查，不能承诺 AI 永不漏项。
