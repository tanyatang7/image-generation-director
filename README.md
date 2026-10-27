# Image Generation Director · 生图导演

面向 **UI 与运营插画**的 Codex Skill：将需求拆成视觉元素，探索五个方向，继续构图变体、精修和 IP / 风格修正，并为每张图保留提示词及检查记录。

适用于运营头图、弹窗插画、功能配图、空状态图和角色复用。它提供可阅读、可修改的创作方法与辅助脚本，**不包含模型、账号、API 密钥或免费生图额度**。

## 工作方式

```text
需求与参考图 → 参考角色确认 → 关键词拆解 → 五个方向
    → 逐图生成与检查 → 用户选方向 → 五个构图变体
    → 可选精修 → 最终选图与矫正确认 → 导出归档
```

- **用户做审美决策**：确认参考用途、方向、构图和矫正选择。
- **当前 Codex 会话模型**：分析需求、写提示词、编排工具、查看图片并记录检查结果。
- **Codex 内置生图工具**：实际生成与编辑图片。此发布版不调用公司 API。
- **本地 Python 脚本**：校验阶段与数据、冻结提示词、记录执行和导出；运行脚本本身不会生成图片。

完整规则在 [SKILL.md](SKILL.md)；关键词、构图、IP、元素和归档说明在 [references/](references/)。

## 运行要求

| 项目 | 要求 |
|---|---|
| Agent | 能读取本地 Skill，并提供内置 `image_gen` / `imagegen` 生图工具的 Codex 环境 |
| Python | Python 3.10 或更高版本；使用记录与图片检查脚本时需要 Pillow |
| 系统 | 脚本使用 POSIX 文件锁，面向 macOS / Linux；Windows 原生未支持，可在 WSL 中自行验证 |
| 模型与额度 | 使用者自己的 Codex 账号及生图权限；可用性与额度以实际账号为准 |

OpenAI 官方目前说明内置生图使用 `gpt-image-2`，计入 Codex 使用额度。工具参数不支持的模型、尺寸或质量字段，不能因写进本地记录就视为服务已接受。参见 [官方生图说明](https://learn.chatgpt.com/docs/image-generation)。

## 安装

在 macOS / Linux 终端中，将仓库克隆到个人 Skill 目录：

```bash
mkdir -p "$HOME/.agents/skills"
git clone https://github.com/tanyatang7/image-generation-director.git \
  "$HOME/.agents/skills/image-generation-director"
```

如果该目录已经存在，请先核对来源，备份后再决定合并或替换，避免覆盖自用版本。也可以下载仓库 ZIP，解压后把包含 `SKILL.md` 的目录命名为 `image-generation-director`，放入上述 Skill 目录。

需要使用辅助脚本时，在合适的 Python 环境中安装依赖：

```bash
python3 -m pip install -r "$HOME/.agents/skills/image-generation-director/requirements.txt"
```

安装后重新开启 Codex 会话，并确认能找到 `$image-generation-director`。如果当前客户端没有内置生图工具，此版本不能直接出图，不会自动切换到其他 API。

## 开始使用

在 Codex 中明确调用 Skill，附上你的参考图并描述用途。例如：

```text
使用 $image-generation-director，为活动弹窗设计一张插画。
主题是“开启新旅程”，主体完整呈现，背景需要透明。
图 1 是风格参考，图 2 是角色参考。
先按流程分析并展示方向，等我选择后再继续。
```

这是使用示例，不是已经执行的生成任务。用户已给出的参考角色和决定应直接沿用；需要决定的节点保留确认，不代选，也不把等待当成同意。

## 输出目录配置

公开版移除了原作者电脑上的固定路径。**执行任何脚本前，先选定符合用户和项目规则的输出目录。**

- `IMAGE_DIRECTOR_ROOT`：允许写入的绝对根目录。
- 未设置时：以脚本进程的当前工作目录为根。
- `bundle.task.root`：任务项目的绝对路径，可以等于该根或位于该根内部。
- 参考图可以从其他已授权的可读位置输入；输出根限制不等于安全沙箱。

例如，在你的实际项目目录启动脚本：

```bash
# 先进入你已选定的实际项目目录，再设置变量
export IMAGE_DIRECTOR_ROOT="$PWD"
python3 "$HOME/.agents/skills/image-generation-director/scripts/director.py" --help
```

Agent 建立真实任务 bundle 后，辅助脚本的调用方式是：

```text
python3 <Skill目录>/scripts/director.py validate <bundle.json>
python3 <Skill目录>/scripts/director.py render <bundle.json>
python3 <Skill目录>/scripts/director.py run <bundle.json>
```

`run` 只准备请求，返回 `calls: 0`。真实出图由 Agent 随后调用内置工具完成。结构和事件协议见 [execution-bundle.md](references/execution-bundle.md) 与 [codex-imagegen.md](references/codex-imagegen.md)。

```text
实际任务根目录/
├── work/director/<轮次>-v<版本>/   提示词、冻结请求、选择及检查记录
├── outputs/generated-images/     每轮生成图片
└── outputs/final/                最终导出
```

不要把用户参考图、业务文案、生成任务记录或凭据提交到公开仓库。仓库的 `.gitignore` 仅辅助忽略常见本地文件，不替代发布前检查。

## 能力与验证边界

- 同时保留 IP 与非 IP 工作流、五方向及五构图探索、可选精修、原始确认节点。
- 单次工具成功不代表图片好看；实际图片仍需要逐张查看，文字与图形也需要检查。
- 本地记录和检查脚本不是不可绕过的审批服务，不能认证用户身份，也不保证所有 Agent 都严格遵循规则。
- 提示词、参考图或冻结内容发生变化时需要新版本；结果不明时先核对已有调用，避免重复生成。
- 本次公开发布整理做了本地脚本与路径检查，没有重新执行完整真实生图流程，也不承诺不同模型的效果一致。

## 文件说明

| 文件 | 用途 |
|---|---|
| `SKILL.md` | Agent 入口、创作阶段与确认节点 |
| `references/prompt-rules-core.md` | 关键词与画面规则 |
| `references/composition-templates.md` | C1–C9 构图模板 |
| `references/prompt-rules-ip.md` | IP 与风格修正规则 |
| `references/element-library.md` | 元素与装饰参考 |
| `references/execution-bundle.md` | 结构化数据与执行协议 |
| `references/three-checklists.md` | 任务、执行、检查记录 |
| `references/codex-imagegen.md` | 内置工具参数与调用边界 |
| `references/asset-management.md`、`references/output-layout.md` | 参考图、输出及历史记录 |
| `scripts/` | 本地校验、任务准备和记录辅助脚本 |

## 来源与许可

由作者自用的 Cursor 版本迁移整理为 Codex 发布版。迁移版使用当前会话模型处理提示词，使用 Codex 内置工具生图；原先的公司接口配置不包含在本仓库中。

本仓库按 [MIT License](LICENSE) 发布。允许使用、修改、分发及商业使用；复制全部或实质部分时须保留版权与许可声明。许可证适用于本仓库内容，不授予模型服务额度，也不替用户授权参考图片、角色、商标或其他第三方素材。

Author: [tanyatang7](https://github.com/tanyatang7)

## English

A Codex image-direction skill for UI and marketing illustrations. It includes reference-role assignment, keyword decomposition, five visual directions, five composition variants, optional refinement, IP/style correction, and per-image review records. The public package uses Codex's built-in image tool, not a company API. Local helpers require Python 3.10+, Pillow, and a POSIX environment. MIT licensed; model access and usage limits belong to each user.
