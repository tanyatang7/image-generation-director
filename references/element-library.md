# Element Library（写 Prompt 时查）

> 这里集中存放 icon 库、装饰词库、动感词库、跨场景拆解示例。**agent 写 prompt 时按需 Read 查表**，不需要每次开会话都加载。

## 一、通用面性 icon 库（按语义类别）

> Agent 在 Stage 0 的 icon 候选列里直接从下表挑，不要凭空造词。
> 缺词时先用最贴近的语义代替，**不允许造业务定制 icon**（如"赠送 icon""分享卡 icon"）。
> 公共面性 icon 也可去 [iconfont.cn](https://www.iconfont.cn/) 查。

| 类别 | 常用 icon | 中文写法 | English Prompt 关键词 |
| --- | --- | --- | --- |
| **动作类** | 分享箭头 / 上传↑ / 下载↓ / 双向⇄ / 循环 / 加号+ / 对勾✓ / 关闭× | 1 个面性分享箭头 icon / 1 个面性对勾 icon | filled share arrow icon / filled checkmark icon / filled plus icon |
| **状态类** | 心形 / 五角星（面性） / 大拇指 / 笑脸 / 闪电 / 火焰 | 1 个面性心形 icon / 1 个面性闪电 icon | filled heart icon / filled lightning bolt icon / filled flame icon |
| **时间类** | 时钟面 / 沙漏 / 日历方块 / 计时器 | 1 个面性时钟 icon / 1 个面性沙漏 icon | filled clock icon / filled hourglass icon |
| **信息类** | 铃铛 / 信封 / 对话气泡 / 问号? / 感叹号! / 信息i | 1 个面性铃铛 icon / 1 个面性对话气泡 icon | filled bell icon / filled chat bubble icon |
| **内容类** | 文档 / 文件夹 / 图片 / 播放三角▶ / 锁 / 书签 | 1 个面性文档 icon / 1 个面性播放 icon | filled document icon / filled play triangle icon |
| **用户类** | 头像剪影 / 群组 / 加号头像 | 1 个面性头像 icon / 1 个面性群组 icon | filled avatar icon / filled group icon |

---

## 二、装饰类型清单（按形态分组）

**装饰选型规则**：每套方向只用 **1 类同形装饰**；**5 套方向之间必须用不同装饰类型**；装饰必须遵守整体动势，**不允许四面八方乱飞**。

| 类别 | 中文写法 | English Prompt 关键词 | 适合搭配的主体类型 |
| --- | --- | --- | --- |
| **小星星** | 4 颗小星星散落 | 4 small twinkling stars scattered | 福利类、惊喜类 |
| **小爱心** | 4 朵小爱心散落 | 4 small heart shapes scattered | 互动类、社交类 |
| **小彩带** | 4 段小彩带散落 | 4 small ribbon strips scattered | 庆祝类、活动类 |
| **小光斑** | 4 颗小光斑散落 | 4 small light spots scattered | 高级感、强调类 |
| **小气泡** | 4 个小气泡散落 | 4 small bubble shapes scattered | 轻松类、活泼类 |
| **小礼花** | 4 团小礼花散落 | 4 small confetti bursts scattered | 庆祝类（避免与小彩带同套） |
| **小烟花** | 4 团小烟花散落 | 4 small firework sparks scattered | 节庆类 |
| **小三角粒子** | 4 个小三角粒子散落 | 4 small triangle particles scattered | 科技类、潮流类 |

### 装饰动势词（与装饰类型组合，必选 1 种）

| 中文 | English |
| --- | --- |
| 喷射放射（从中心扩散） | radiating outward in burst pattern |
| 螺旋上升（从中心扩散变体） | swirling upward in spiral |
| 错落漂浮（向中心收敛） | scattered at varying heights, drifting toward center |
| 重力暗示（跟随主体动势） | suggesting gentle gravity drift |
| 围绕环抱（向中心收敛变体） | wrapping around in arc, all facing center |

---

## 三、动感词库

> Codex 推理段 写 Prompt 时按主体类型从下表挑词。**不允许 5 套方案 / 5 个变体之间用同一组词**。

### 纸质物（券/卡/红包/票）

| 中文 | English |
| --- | --- |
| 微弯飘动 | softly curving in mid-air |
| 边缘上卷 | edges gently curled upward |
| 错落叠放 | stacked at staggered angles |
| 风中翻转 | fluttering in the breeze |
| 半空悬浮 | floating mid-flight |
| 一角翘起 | one corner lifting up |
| 微微抖动 | trembling slightly |

### 礼盒 / 容器

| 中文 | English |
| --- | --- |
| 刚被打开 | lid just popped open |
| 倾斜悬浮 | tilted and hovering |
| 喷涌而出 | contents bursting outward |
| 微微弹起 | lifted slightly off ground |
| 盖子飞起 | lid soaring upward |

### 通用动态修饰（任何主体可加）

| 中文 | English |
| --- | --- |
| 凝固瞬间 | caught mid-motion / frozen in time |
| 刚刚发生 | as if just happening |
| 风吹过的瞬间 | wind-blown / breeze-caught |
| 半空中 | suspended mid-air |
| 动势冻结 | dynamic pose frozen |

---

## 四、跨场景字面词归位示例

> 高频字面词的「3 类归属 + 5 个 L2 候选 + icon 候选」速查表。
> Stage 0 写 L2 候选时，先在这里找有没有现成的；没有再走「字面词 → 具象映射拆解」（详见 `prompt-rules-core.md` 第六章）。

| 字面词 | 类型 | L2 5 个候选 | 完全抽象词的 icon 候选 |
| --- | --- | --- | --- |
| **解锁** | 完全具象 | 钥匙刚插锁孔 / 弹开的挂锁 / 钥匙+锁 / 打开的宝箱 / 闯过的关卡门 | —— |
| **抽奖** | 完全具象 | 大转盘 / 老虎机 / 奖杯 / 中奖券 / 礼盒 | —— |
| **签到** | 完全具象 | 签到本+笔 / 印章 / 打卡机 / 签到日历方块 / 签到券 | —— |
| **邀请** | 完全具象 | 邀请函 / 请柬 / 红色信封 / 双手递信 / 信封+爱心 | —— |
| **闯关** | 完全具象 | 关卡门 / 旗帜 / 城堡 / 通关勋章 / 卡通角色冲过门 | —— |
| **夺宝** | 完全具象 | 宝箱 / 宝石 / 钥匙开宝箱 / 寻宝地图 / 海盗船 | —— |
| **拼团** | 半具象 | 拼图块 / 两半合体物 / IP 抱团 / 双手交握 / 圆桌 | —— |
| **免费** | 半具象 | 0 元价签 / 撕掉的价签 / 红包 / 礼盒 / 钱包 | —— |
| **学习** | 半具象 | 课本 / 翻开的书 / 平板 / 毕业帽 / 铅笔 | —— |
| **内容**（教育=主题课程） | 完全具象 | 课本 / 翻开的书 / 平板 / 毕业帽 / 铅笔 | —— |
| **分享** | 完全抽象 | 礼盒 / 红包 / 链接卡 / 课程卡 / 文档（被分享的对象） | 分享箭头 icon / 加号头像 icon |
| **关注** | 完全抽象 | 头像 / 大 V 角色 / 屏幕 / 信封 / 卡片（被关注的对象/通知载体） | 加号 icon / 铃铛 icon |
| **收藏** | 完全抽象 | 卡片 / 商品 / 文章 / 课程 / 单品（被收藏的对象） | 心形 icon / 书签 icon / 五角星 icon |
| **点赞** | 完全抽象 | 卡片 / 头像 / 视频缩略图 / 文章 / 商品（被点赞的对象） | 大拇指 icon / 心形 icon |

---

## 五、6 场景 L2 偏好池（与 prompt-rules-core.md 第七章配套）

| 使用场景 | L2 偏好池 | 避开 |
| --- | --- | --- |
| **电商** | 礼盒 / 红包 / 优惠券 / 购物袋 / 钞票 / 商品 / 价签 | 课本 / 关卡门 / 信封等非电商语义 |
| **教育** | 课本 / 翻开的书 / 平板 / 毕业帽 / 铅笔 / 关卡门 / 奖杯 | 红包 / 价签 / 购物袋 |
| **社交** | 对话气泡 / 头像 / 信封 / 卡片 / 心形 / 3D 手机 | 价签 / 关卡门 / 钞票 |
| **运营活动** | 礼盒 / 宝箱 / 转盘 / 邀请函 / 奖杯 / 红包 | 课本 / 文档 |
| **工具效率** | 文档 / 文件夹 / 时钟 / 平板 / 笔记本 / 对勾 | 礼盒 / 关卡门 |
| **品牌 IP / 启动屏** | IP 角色 / 场景背景 / 标志性配饰 | 业务定制 UI |
