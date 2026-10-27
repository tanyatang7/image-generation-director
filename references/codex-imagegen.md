# Codex 内置 image_gen（gpt-image-2）

本 Skill 的唯一生图入口是 Codex 内置 `image_gen` 工具。OpenAI 官方说明内置生图使用 `gpt-image-2`，并计入 Codex 通用使用额度。`image_gen` 是工具名，`gpt-image-2` 是其底层模型；当前工具参数不包含模型选择字段，因此不能在调用时再写一个虚构的 `model` 参数。

## 执行前提

- 不需要本地 API key，也不需要安装或运行 Python 生图客户端。
- 本地 Python 脚本只冻结阶段、Prompt、参考图顺序、输出位置和执行记录，不负责向图像服务发请求。
- 内置工具不可用时，记录具体错误并停止依赖该图片的阶段。不得静默切换到 CLI、直连 API 或其他服务；只有用户明确选择替代路径后才能变更后端。
- 用户授权本轮生图不代表用户已经选择方向、构图或矫正方案。所有原有确认节点仍是进入依赖阶段的前提。

## 固定调用流程

先保存并校验本轮 bundle：

```bash
python3 <skill根目录>/scripts/director.py run <本轮bundle.json>
```

该命令只准备任务，生成 `task-list.json`、`requests.json` 和 `receipt.json`，返回 `calls: 0`。随后对每个任务依次执行：

1. 写入该任务的 `running` 事件，用 `director_checklists.py event` 取得冻结后的 `tool` 和 `arguments`。
2. Agent 将返回的 `arguments` 原样传给 Codex 内置 `image_gen`；不得在执行段改写 Prompt、删减参考图或合并任务。
3. 工具成功后，记录工具调用标识和工具返回的本地图片路径。事件处理器验证 PNG 并复制到已冻结的项目输出路径。
4. 工具失败或结果不明时，分别记录 `failed` 或 `uncertain`，保留成功项，不以重复调用掩盖失败。
5. 一轮全部结束后逐张实际查看，再填写与图片 SHA-256 绑定的视觉检查。

事件示例：

```json
{"task_id":"scheme-01","status":"running"}
{"task_id":"scheme-01","status":"success","tool_call_id":"实际调用标识","path":"工具返回的本地 PNG 路径"}
```

`event running` 返回的调用结构为：

```json
{
  "tool": "image_gen.imagegen",
  "arguments": {
    "prompt": "冻结后的完整 Prompt",
    "referenced_image_paths": ["风格参考绝对路径", "IP 参考绝对路径"]
  }
}
```

无参考图时省略 `referenced_image_paths`。不要传空数组、输出路径、模型、质量、尺寸或其他工具定义未接受的字段。

## 参考图顺序

所有本地参考图先实际查看并归档。工具参数使用有序的 `referenced_image_paths`。

| 阶段 | 第一张输入 | 第二张输入 |
| --- | --- | --- |
| 首轮、构图变体 | 风格参考 | IP 参考 |
| 同图兼任两个角色 | 同一原图 | 同一原图，重复传入 |
| 构图变体、精修 | 先保持基础参考的既定顺序 | 最后追加用户选中的上一轮图片作为构图底图 |
| Stage 3 A | 选定生成图 | IP 参考 |
| Stage 3 B，IP 模式 | 步骤 A 产物 | 风格参考 |
| Stage 3 B，非 IP 模式 | 选定生成图 | 风格参考 |

用户明确指定的角色分配优先，Prompt 中图序须一致。额外细节参考排在相应角色图后。重复路径不去重；工具如何内部使用重复槽位仍需根据实际结果核验。

## 数量、输出与透明背景

- Stage 1：5 个不同 Prompt，5 次独立调用，每次一张图。
- Stage 2 构图变体：5 个不同 Prompt，5 次独立调用。精修如已选择则同 Prompt 独立调用 3 次。
- 不把五个方向合并成一张拼图，不因调用耗时自行减少数量。
- `parameters.model=gpt-image-2`、size、quality 和 output_format 是 bundle 中的冻结意图与记录。内置工具没有对应显式参数时，不把这些字段传给工具，也不声称服务接受了它们。
- 内置工具不接收目标文件路径。工具生成文件通常位于其默认生成目录；成功事件将其复制到配置的输出根内、本轮已冻结的输出路径。
- 需要透明背景时在 Prompt 中明确请求，并在产物返回后检查实际 alpha；白底或棋盘格不算透明。

## 失败与结果不明

1. `running` 只表示已登记待调用，不证明工具已经接受请求。
2. 返回成功后检查本地文件存在、可解码且为 PNG，再登记 `success`。
3. 同一个任务已登记 `running` 或已经成功时，不重复派发。若工具结果不明，先核对现有生成记录和文件，再由用户决定是否重试。
4. Prompt 或参考图变化时升版本，原任务不覆盖；用户方向选择变化时回到对应节点。
5. 工具拒绝参考图、返回错误或不可用时，如实记录原错误范围；不得改走未获用户选择的生图后端。

## 扁平风反向词

延续原流程的扁平风提示模板：

```text
flat 2D illustration, no 3D, no shading gradient, no volumetric light, vector style, clean line art
```

如与用户明确要求的背景渐变或参考质感冲突，按用户要求限定词语作用范围；需要创意取舍时在方案节点让用户决定，不静默删掉用户要求。历史效果数据不能替代本任务实际看图核验。

## 官方依据与边界

- [Codex image generation](https://learn.chatgpt.com/docs/image-generation)：内置生图使用 `gpt-image-2`，计入 Codex 通用使用额度；较大批量或程序化使用才需要另行配置 API key。
- 当前工具定义决定实际可传参数。Skill 只使用 `prompt` 和可选的 `referenced_image_paths`。
- 本地执行记录能够检查阶段、数量、请求和文件，不能认证用户身份，也不能阻止具备其他工具权限的 Agent 绕过该流程。
