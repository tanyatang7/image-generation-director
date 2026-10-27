# 自动校验增强版：结构化产物与统一入口

## 三类关联产物

每轮同时维护 `task-list.json/.md`、`execution-list.json/.md`、`check-list.json/.md`，规则与内置工具接续方法见 [three-checklists.md](three-checklists.md)。`director.py run` 自动建立内置工具任务与执行清单；视觉检查仍需实际看图后填写。清单助手的通过范围限于本地结构、数量、文件与记录检查。

本文件定义机器可检查的子集。创作方法、原有参考清点确认、六个用户节点、IP 子流程选择与条件暂停继续以 SKILL.md 和对应创作规则为准。

本版没有受保护的用户审批服务。`decisions` 是 Agent 转录用户实际回答的本地记录；`source`、原话和内容哈希便于核对，但不是身份证明，也不能防有权限的 Agent 伪造记录。不得以“validator 通过”声称用户真实授权已经被程序认证。

## 执行入口

先定位当前 Skill 根目录，以下 `<skill>` 指该真实路径；所有任务产物写在 Desktop/codex 内当前项目的 work/、outputs/ 下。

```bash
python3 <skill>/scripts/director.py validate <bundle.json>
python3 <skill>/scripts/director.py subjects <bundle.json>
python3 <skill>/scripts/director.py render <bundle.json>
python3 <skill>/scripts/director.py run <bundle.json>
python3 <skill>/scripts/director.py review-template <bundle.json>
python3 <skill>/scripts/director.py export <final-bundle.json>
```

- Python 只负责本地结构和图片检查，需要 Pillow。真实生图由 Codex 内置 `image_gen` 工具完成，不需要本 Skill 配置 API key。
- `validate` 只检查，不上传。`subjects` 返回要绑定的内容哈希，不创建批准。
- `render` 先检查再生成供展示的表格及发送文本归档；它不自动发布聊天消息。Agent 展示生成的内容并在原有节点等待。
- `run` 固定执行 validator → 版本快照 → 每项请求一致性检查 → 建立 `image_gen.imagegen` 任务 → receipt，明确报告 0 次调用。
- `run --execute` 明确拒绝，避免误用已删除的本地客户端路径。真实调用按 [codex-imagegen.md](codex-imagegen.md) 使用 `director_checklists.py event` 获取冻结参数并逐项调用内置工具。
- `review-template` 输出的观察值为空、结论为 unknown。必须实际逐张看图后填写，不能批量改 pass。
- `export` 只复制已完成审阅和本地决策记录的最终 PNG；不替用户做抠图、改背景或重采样。需要后处理时按用户所选工具完成后，把实际文件和来源写进 `final.exports`，再验证导出。

脚本会固定检查本入口，但 AI 仍能修改本地脚本、记录或绕过入口；本版不声称全局强制遵循流程。

## Bundle 数据与阶段

每次提交一个 UTF-8 JSON 对象。不要由 Agent 另写“检查已通过”来替代实际运行。JSON 禁止重复键。基础字段：

| 字段 | 含义 |
|---|---|
| `schema_version` | 固定 1 |
| `id`、`version` | 本次产物/轮次的稳定英文编号与正整数版本；修改已冻结内容时升版本 |
| `stage` | inventory / keywords / directions / round1 / composition / refinement / ip-correction / style-correction / final |
| `task` | id、root（当前项目绝对路径）、request（用户原始需求）、scenario、mode（ip 或 non-ip）；无风格参考时另填 style_text |
| `references` | 有序参考描述列表，允许两个角色使用同一个文件，不按文件哈希去重 |
| `keywords` | Stage 0 对应的关键词数据 |
| `directions` | 当前供审阅的完整五方向池；排除后补足五套形成新版本，旧池另行留档 |
| `decisions` | 各原有节点的用户回答转录，不是可信审批记录 |
| `schemes` | 本次实际生成的完整方案；只在生成阶段需要 |
| `reference_ids` | 本轮基础参考顺序：style、ip、detail；保留同文件双角色 |
| `parameters` | model=gpt-image-2、size、quality、output_format=png；作为冻结意图和记录，内置工具调用本身只接收其工具定义允许的字段 |
| `parent` | 后续轮次所选前序产物、receipt、视觉报告及 scheme_id；首轮没有 |

`inventory` 只要求基础输入；`keywords` 另外要求参考清点的实际回答；`directions` 再要求关键词回答；`round1` 再要求文字方向审阅回答与完整 Prompt。不得为了通过检查伪造尚未发生的回答。

### 参考记录

每项有 `id`、`role`（style/ip/detail）、`path`、`sha256` 和 `inventory`。inventory 包含 subject_type、colors（最多三个估值）、accessories（最多三项）、background。文件哈希使用实际文件字节的 SHA-256；程序检查文件存在、哈希及解码能力，不证明 Agent 已看过图片。

同图兼任使用两个不同 id，role 分别为 style 和 ip，path/sha256 可相同。用户上传顺序不等于调用顺序。Stage 3 由执行器自行组装为“选定图片＋对应角色参考”，不要求 AI 自行排列。

### 关键词与方向

关键词为 3–5 项，每项有 id、word、semantic、l2（五个候选）、l3（可为空）、icons（2–4 个候选）、scene_alignment。语义合理性与候选是否来源正确仍需内容审查。

每版供审阅的方向固定五项；用户排除后保留其余项，以新编号补足五套，重新审阅当前整组方向。旧版本留档，不复用旧 subject_hash。每项字段如下：

```json
{
  "id": "scheme-01",
  "name": "方案名称",
  "subject": "供速览表显示的完整主体关系",
  "meaning": "元素与业务含义的对应说明",
  "combination": "C4",
  "elements": ["character", "card", "icon", "stars"],
  "motion": "主体动作",
  "perspective": "视角",
  "ip_role": "main"
}
```

`elements` 是任务内稳定的元素标识，用于核对构图变体没有丢元素；不是检测图片像素。IP 模式必须标 main/secondary，并在完整五方案池中混合。非 IP 模式不要求 ip_role。

首轮检查 C1–C9、至少三种 A 关系、同 C 最多两套。原规则已允许用户明确复用参考构图：在 `decisions.reference_layout` 转录原话，action= reuse_layout 或 close_edit，subject_hash 绑定 inventory 内容，才按该原有例外不检查首轮组合覆盖。不能因 AI 认为“更好”自行添加此记录；该例外不自动外推到 Stage 2。

### Prompt 与逐图清单

每个完整 scheme 保留对应 direction 的字段，再增加：

- `prompts.zh`、`prompts.en`：完整、连贯、不带字段标签的可发送文本，无首尾空白。展示用 subject/motion 等字段独立保留。
- `send_language`：zh 或 en，选择其中一份发送，不额外拼接、增强或剥标签。
- `checklist`：relation、decoration_count、decoration_shape、decoration_position、interior、icon_count、icon_position、icon_type、surface、perspective、framing、crop、palette，每个字段都是具体预期文字。

留档 Markdown、`.prompt.txt` 和请求使用同一份选定文本；动态代码围栏允许 Prompt 本身含反引号。中文、引号、换行、`$()` 通过文件传递，不进入 shell 代码。

程序目前不保证已填入的 C 编号与 Prompt 描述语义一致、不通过关键词搜索宣称“视觉风格合格”。动感词、禁词的语境、形象特征、颜色约束、C 模板语义填充仍保留原文审查规则，不能被结构 PASS 替代。

### 决策记录

```json
{
  "subject_hash": "由 subjects 输出的对应内容哈希",
  "action": "confirm",
  "response_text": "用户实际回答原文",
  "source": "对应消息的可定位标识或原始记录路径",
  "selected_ids": ["scheme-01", "scheme-02", "scheme-03", "scheme-04", "scheme-05"]
}
```

inventory、keywords、directions 用上面的 confirm 结构；只有 directions 需要 selected_ids。修改意见不写 confirm，应返工并等待对应决定；已经明确回答的节点不重复问。

**已确认的数量规则**：用户排除后补足五套，重新审阅后再生成。selected_ids 必须覆盖当前五套；只选择剩余三套不能进入生图。新方向池的哈希变化后，旧确认失效。补充新方向属于推理工作，可准备材料；不得把准备完毕当成用户已经审阅。

**已确认的标签规则**：采用不带标签的完整发送文本，例如“小斑马抱着礼盒。”；展示表格仍可以保留主体、动作等字段。程序检查已知中英文字段标签（行首或分号后），发现则拒绝，要求在推理段重新整理文本；不在执行时自动删标签。该检查不是对任意语言标签的语义识别。

### 后续轮次 parent

parent 包含 bundle、receipt、review 三个文件描述（每个是 path/sha256），以及 scheme_id。bundle 指 runner 冻结的前序 bundle.json；receipt 指实际执行记录；review 指填写完成的逐图报告。

`decisions.parent_choice.subject_hash` 对以下对象使用同一个 `hash_obj()` 算法：

```text
{bundle_hash: 前序 bundle 的规范化哈希,
 receipt_sha256: receipt 文件字节哈希,
 review_sha256: review 文件字节哈希}
```

action 为 select / accept_current / correct / continue_correction；selected_id 与 parent.scheme_id 一致。有失败图片、视觉 fail 或 unknown 时，只有用户明确选择接受当前问题才填 `accepts_issues: true`。这是记录，不是程序替用户同意。

- composition：前序必须为 round1；五套、至少三个 C 编号、同 C 最多两套、元素标识集合保持一致。新增 `variation_axes`（四项 id/label，含 combination、motion，其余两维由原 Skill 推理段选择）；每个 scheme 的 `variation_values` 与这四维一一对应。调用时保持基础风格/IP/细节参考的既定顺序，并在末尾追加用户选中的上一轮图片作为构图底图。
- refinement：前序为 composition；parent_choice.next=refine；同一 Prompt 三次独立调用。
- ip-correction：IP 模式；前序为 composition/refinement；action=correct；单张，实际发送文本等于 SKILL.md 的固定 IP 句式。
- style-correction：IP 模式前序必须为 ip-correction，action=continue_correction 可引用原用户“先 IP 后风格”的同一次选择，不新增中途审批；若用户已说停止，就不得执行。非 IP 模式直接从 composition/refinement 进入，action=correct。
- 换参考图：前后 references 不同时，还需 reference_change 原话记录，subject_hash 绑定 `{before:旧列表,after:新列表}`。只补录真实决定。

前序必须存在完整结果记录，不能五套仅跑一张便把轮次报成完成。单图失败不阻塞其他独立调用；轮次结束后报告失败并由用户决定继续路径。

## 最终交付

stage=final。parent 指最终选中的已生成图片（composition/refinement/ip-correction/style-correction），并包含最终选图的 parent_choice 记录。

`final` 包含 comparison（实际看图的对比记录）、background（preserve/transparent），可附 `exports` 列表。每项 exports 含 id、asset（path/sha256）、background，可声明 width/height；程序核对实际尺寸。后处理文件与所选原图不同，还要有 source_sha256 和 processing_note；不声称仅凭记录就证明抠图保留了主体。

`decisions.final` 绑定 `{image:{path,sha256},parent_bundle_hash:...,export_spec:完整final对象}`，action 为 deliver_without_correction / deliver_after_correction / stop_correction，并记录实际原话和来源。必须保留暂停点 6 的比较及选择；“不用修了”的既有回答直接沿用，不重复确认。

透明输出要求实际存在透明像素，不把白底/棋盘格当透明。多尺寸文件必须实际生成后再填规格。统一导出不擅自抠图或调整尺寸。

## 状态、版本和重试

- 快照写到 `work/director/<id>-v<version>/`：bundle.json、review.md、每套 .prompt.txt、按槽位复制的参考原件、requests.json、receipt.json。
- 生图写到 `outputs/generated-images/<id>-v<version>/<scheme-id>.png`；最终文件写到 `outputs/final/<id>-v<version>/`。
- 生成状态：pending、running、success、retryable、failed_after_retries、failed、uncertain、invalid_output。视觉检查单独记录，不把生成成功改称视觉通过。
- 同版本内容或引用变化则拒绝；修改 Prompt/参考需新版本。已有同版本成功文件按哈希检查后跳过，不重新付费生成。
- 内置工具明确返回可重试错误时，按工具反馈和当前会话限制处理；不能凭旧接口状态码规则盲重试。
- 超时、连接中断或结果去向不明时记 uncertain，不自动再次提交。先核对原调用与实际文件，再报告；不得改成 pending 掩盖不确定结果。
- 多进程按 task.root 加文件锁，避免本入口同时处理同一任务。锁不构成安全隔离。
- 旧版 status.json 仅作为历史证据，不自动导入为已确认的阶段；根据实际文件和原始用户回答建立新记录。缺失的用户决定必须询问，不能补“同意”。

## 验收边界

本版可测试的是实际入口的拒绝、调用次数、请求内容、结果文件和续跑行为。规则表、视觉报告、用户原话仍可由本地 Agent 写入；模型不误解需求、所有入口不被绕过、真实图像效果和用户验收不在本版强制保证范围内。
