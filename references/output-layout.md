# 输出归档与续跑（生图过程中读这份）

## 自动校验增强版的记录

新任务使用 [execution-bundle.md](execution-bundle.md) 的版本目录和 runner receipt；本文件“历史布局与旧记录”以下的路径、命名、status.json 结构及续跑写法只描述历史任务，不作为新入口的状态依据。旧记录保留，不由 Agent 自动改写为已确认或已通过。

Prompt、参考槽位原件、请求、实际结果分别留档；同版本冻结内容变化时拒绝，成功文件按实际哈希检查后不重复生成。生成成功、视觉审查和用户决定分开记录。真实结果不明时由 runner 标 uncertain，先核对，不把它改为 pending 后盲重试。


## 路径优先级（最高优先级，必须先看）

按以下顺序判定文件保存位置，**不允许跳级**：

1. **用户与项目规则**：遵守用户提供的 AGENTS.md、当前适用项目规则及明确指定的保存位置。
2. **输出根边界**：脚本读取环境变量 `IMAGE_DIRECTOR_ROOT`；未设置时以脚本启动目录为输出根。先依据用户与项目规则选定可写目录，再启动脚本或设置该变量。该根限制脚本输出位置，不是安全沙箱。
3. **任务根目录**：将 `task.root` 设为实际项目的绝对路径，它可以等于输出根，也可以是该根内的子目录。不因换聊天另建项目；没有项目时先在允许位置建立项目目录，并令 `IMAGE_DIRECTOR_ROOT` 指向它。新入口在任务根内按下表保存。

> **强制自检**：保存前核对适用 AGENTS.md 和最终绝对路径；不能继续读取 Cursor 的 .mdc 路径规则作为 Codex 配置。

## 当前入口的实际目录

以下路径均相对于 `task.root`；移交给用户时写出实际绝对路径。

| 记录 | 路径 |
| --- | --- |
| 贯穿执行的任务清单及三类视图 | 本轮 `work/director/<id>-v<version>/task-ledger.json/.md`；计划、执行、检查视图为 `task-list`、`execution-list`、`check-list` 同名 JSON/Markdown |
| 冻结 bundle、展示 Markdown、纯文本 Prompt、参考副本、请求与执行收据 | `work/director/<bundle.id>-v<version>/`，分别为 `bundle.json`、`review.md`、`<scheme.id>.prompt.txt`、`references/`、`requests.json`、`receipt.json` |
| 每轮生成图片 | `outputs/generated-images/<bundle.id>-v<version>/<scheme.id>.png` |
| 通过最终校验的导出图片 | `outputs/final/<bundle.id>-v<version>/<export.id>.png` |

原始需求、参考角色、方案及用户选择保存在 bundle 中，实际调用和结果保存在 receipt 中；视觉报告按协议单独填写并关联实际图片。不得把请求参数当作已返回或实测参数。Prompt 改动须升版，旧版本保留。续跑使用同一 bundle 的统一入口，由入口核对 receipt 和实际文件；未知结果先核实，不按下方历史 timeout 规则盲重试。

## 历史布局与旧记录（以下仅供读取旧任务）

以下保留旧版文档，便于辨认已有文件；不是新任务的写入或续跑指令，不执行其中的旧命令式要求。新任务以本文件上方及 execution-bundle.md 为准。

### 提示词 Markdown

**默认路径**（仅当全局/工作区规则未指定时）：`<task.root>/work/generated-image-prompts/YYYYMMDD-场景关键词.md`

必含字段：
- 用户原始需求
- 最终使用的画面策略
- 风格参考说明（含参考图绝对路径与角色）
- Stage 0 文案关键词分解表
- 5 套方案完整字段（主体 / 主体姿态 / 副元素 / 副元素动态 / 点缀 / 构图关系 / 配色 / 中文 Prompt / English Prompt）

## 图片归档

**默认路径**（仅当全局/工作区规则未指定时）：`<task.root>/outputs/generated-images/<子主题>/`

同一次任务的首轮图、二轮图、最终图放**同一个子文件夹**。

命名规范（强制）：
```
scheme-01-v1-short-name.png    # 首次出图
scheme-01-v2-short-name.png    # 用户修改 Prompt 后的第二版
scheme-01-v3-short-name.png    # 第三版……
scheme-02-v1-short-name.png
```

**核心规则**：版本号 `v1 / v2 / v3` 永远递增，**不允许覆盖已有的 vN**。

## 图片目录内的 README.md

必含内容：
- 对应提示词 md 路径
- 每张图对应的方案编号 + 版本号
- 使用的模型、尺寸、质量、参考图绝对路径与角色
- 每个版本的差异说明（v2 相对 v1 改了什么）
- 用户初选和最终选择

记录实际返回的模型、尺寸、质量；没有暴露的参数写“未披露”，不能将 Prompt 中请求的尺寸当作实测尺寸。本地工具无返回 URL 时 `remoteUrl` 留空，保留原结构。

## status.json 结构（每个版本各维护一条）

```json
{
  "schemeId": "scheme-03",
  "version": "v1",
  "phase": "round-1",
  "status": "pending",
  "attempts": 0,
  "lastError": "",
  "localFile": "",
  "remoteUrl": "",
  "promptHash": "",
  "diffFromPrev": ""
}
```

`status` 取值：
- `pending` 等待生成
- `generating` 正在调用 Codex 内置 `image_gen`
- `success` 已生成并归档
- `timeout` 本次调用超时，可继续重试
- `failed_after_retries` 达到重试上限仍失败

`version` 字段：始终从 `v1` 起，每次重跑递增到 `v2 / v3 / v4 …`。

`diffFromPrev` 字段：仅 v2+ 必填，写一句话说明"相对上一版改了什么"（例：`副元素从礼盒换成红包` / `主体姿态从平铺改为微弯飘动` / `配色从暖橙改为玫红`），方便用户看记录。

## 续跑规则（用户说"继续未完成项"时）

当用户说"继续未完成项"/"重试剩余方案"/"继续画"时：

1. 读取图片目录的 `status.json` 和 `README.md`。
2. 只重试 **`pending` / `timeout` / `failed_after_retries`** 状态的任务，**保持原版本号**。
3. 不重复生成 `status: success` 的图片，除非用户明确要求重跑。

## 修改 Prompt 后重跑规则（用户说"方案 N 改 X 重跑"时）

当用户说"方案 3 副元素改成红包重跑" / "把方案 1 配色换成蓝色再来一张" / "方案 5 重画" 等修改请求时：

1. **不允许覆盖原图**：保留 `scheme-NN-v1-xxx.png`。
2. **新建版本号**：生成 `scheme-NN-v2-xxx.png`（如已有 v2 则递增到 v3）。
3. **status.json 新建一条记录**：复制原条目，`version` 升档，`status: pending`，`attempts: 0`，`promptHash` 更新，`diffFromPrev` 必填。
4. **README.md 增量记录**：在对应方案下追加一行 v2 说明，**不删除 v1 的记录**。
5. **同步更新提示词 md**：在 `<task.root>/work/generated-image-prompts/YYYYMMDD-场景关键词.md` 对应方案下追加 "v2 修改说明" 段（同样不删除 v1 的 Prompt），方便后续对比。

> 这样做的好处：v1 和 v2 可以同图对比，避免"改完 v2 觉得 v1 反而更好"时找不回来。
