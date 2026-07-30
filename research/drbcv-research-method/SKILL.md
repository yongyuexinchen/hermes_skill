---
name: drbcv-research-method
description: "将学习材料转化为 DRBCV 知识卡片。轻量流程：Hermes 理解内容 → 写 .md 卡片到 Obsidian Vault → 用户审阅。"
version: 1.4.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [research, knowledge-map, obsidian, drbcv]
    related_skills: [obsidian]
---

# DRBCV 轻量知识建卡工作流

## 核心理念

知识卡片的目的是**帮助理解**，不是为了建一个完美的知识图谱。流程越轻，用得越多。流程越重，用得越少。

## 卡片格式

```markdown
---
name: 概念名
type: discriminant|connection|mixed|procedure
status: unexplored|exploding|exploded|core
source: "[[来源文件名]]"
domain: 领域名
---

# 概念名（英文术语）

## 类型判定
[判别/关系/混合/程序] — [一句话判断依据]

## 类比 ★
### 一句话比喻
[用夸张的生活场景翻译核心概念，越离谱越好记]

### 生活映射
| 概念世界 | 现实世界 |
|---------|---------|
| 概念A | 对应物A |
| 概念B | 对应物B |
| 概念C | 对应物C |
> 生活映射表**恰好 3 行**——不要 5 行（太啰嗦，2026-07-23 用户明确纠正：类比太啰嗦，精简到 3 行映射表），不要 2 行（太偷懒）。3 行是最佳平衡——挑选最核心的 3 个维度做映射。

## 是什么
[2-3句话清晰定义]

## 输入-输出空间（程序型必填）
- **输入**: [什么参数]
- **输出**: [返回什么]
- **前置条件**: [约束条件]

## 正例（≥2 个）
1. **场景A**: [具体]
2. **场景B**: [具体]

## 反例/边界（≥1 个）
1. **常见误解/边界情况**: [它不是什么 / 什么情况下失败]

## 详细解释
[核心机制说明。程序型含核心代码+步骤表]

## 关系
### → 指向
- [[后继概念A]] (关系描述)

### ← 被指向
- [[前置概念X]] (关系描述)
```

> **四型卡片侧重点**：
> - discriminant: 定义 + 正反例 + 与相似概念的区别 + 比喻
> - connection: 概念间的关系对比 + 适用场景 + 比喻
> - mixed: 兼有定义和关系 + 比喻
> - procedure: 代码 + 步骤表 + 关键注意事项 + 比喻
>
> ⚠️ 权威格式参考：`research-loop` 技能的 `references/drbcv-card-format.md`，reviewer 验收时以此文件为准。

> ⚠️ **每张卡必须有类比**。这是用户的核心要求。不要写干巴巴的学术定义——必须用生活场景做比喻。类比栏放在 ## 类型判定 之后，作为卡片第二栏——这是读者接触概念后第一时间看到的内容，放对了位置类比才有冲击力。
>
> 好的类比示例：
> - 定积分 → 「把不规则图形切成无数极薄的薯片，每片近似矩形，堆起来就是总面积」
> - DHCP 攻击 → 浴场场景：「你光溜溜进去喊谁是搓澡师傅，假师傅嗓门大先跑来，给你抹了奇怪的东西」
> - 栈 → 「手枪弹夹——最后压入的子弹最先射出，中间那颗不把上面全卸了拿不到」
> - 时间复杂度 → 「给 100 人发传单：O(1) 用喇叭广播一次，O(n) 一个个递，O(n²) 递完还要确认对方收到了没」

## Vault 结构

根目录：`D:\Contents\DRBCV-Knowledge\`

### 领域标准子目录（建新领域时按此创建）

```
<新领域>/
├── Concepts/         # ★ 所有 DRBCV 知识卡片 (.md) —— 核心产出
├── Sources/          # 原文逐字稿 (.txt)，从 docx/pdf 提取
├── Templates/        # 该领域的卡片模板 (.md)，定义本领域卡片侧重点
├── Scripts/          # （可选）提取脚本、批处理工具
├── Articles/         # （可选）长文/笔记（不同于 Concepts 的短卡片）
├── Maps/             # （可选）draw.io 图 / PNG，供卡片引用
└── Systems/          # （可选）系统设计文档
```

### 建新领域 checklist

```bash
# ⚠️ Windows git-bash 不支持大括号展开！分三次 mkdir，不要用 {a,b,c}
mkdir -p "<Domain>/Concepts"
mkdir -p "<Domain>/Sources"
mkdir -p "<Domain>/Templates"
```

1. 提取原文 → `Sources/`（⚠️ **必须输出 .md 而非 .txt**——见下方陷阱）
2. 写 3 张样卡 → 确认风格 → 批量处理
3. 更新 `.obsidian/graph.json` 的 `search` 字段，排除 Sources/Templates（图谱去噪）
   - 在 `graph.json` 中设 `"search": "-path:Sources -path:Templates -path:Articles -path:temp -path:media"`
   - 确保 `"hideUnresolved": true`——否则断链会显示为灰色节点

### 现有领域（供参考）
`Calculus/` `Computer-Network/` `Data-Structures/` `Linear-Algebra/` `Hermes/` `AI伴侣赛道/` `Grok-Build/` `SillyTavern/`

## 工作流

### 小任务（1-3 个概念）

```
用户: "写一张 TCP 拥塞控制的卡"
  → Hermes 理解概念
  → 检查 Vault 是否已有
  → 写 .md 到 Concepts/
  → 回复: "写好了，Obsidian 打开看下"
```

### 中等任务（4-10 个概念）

```
用户: "把这篇文章里的计算机网络概念都建卡"

1. Hermes 先抽样 2-3 张样卡 → 用户确认风格
2. 确认后批量写入剩余卡片
3. 每张卡都要有正例/反例/关系
```

### 用户直接提供内容（聊天中粘贴，无源文件）

```
用户: "帮我存这几张卡：[粘贴 5 个概念的定义和解释]"

1. 先建领域目录（如需新领域）
2. 把用户原始内容写入 Sources/<描述>.md —— 这是 source 文件的来源
3. 写卡片时 source: "[[<描述>]]" 指向刚创建的源文件
4. 所有卡片并行写入（≥5 张卡时一轮写完）
5. 统一验证（grep 7 章节 + 禁用字段 + frontmatter 分隔符）
```

> **为什么必须先建 source 文件？** 卡片 frontmatter 的 `source` 字段必须是 `[[wikilink]]`，而 wikilink 需要指向 Sources/ 下的实体 .md 文件。用户粘贴的内容就是原文——保存它，卡片才能引用。同时这也保留了原始内容的可追溯性。

> ⚠️ **工具调用次数陷阱**：即使只有 10-15 张卡，如果每张卡一个 `write_file` 调用，加上前置的读取源文件、读取参考卡等调用，很容易在 10-15 张时就耗尽工具调用迭代上限，导致任务做一半被截断。
> **对策**：卡片数量 ≥ 8 时，确保首轮读取完所有源文件后，首轮就批量创建尽可能多的卡片（每轮 3-5 张同时写）。不要在创建阶段穿插多余的读取/验证调用——先写完，再验证。

### 用户提供概念清单（多领域、无源文件，≥20 张）

```
用户: 粘贴了 9 个领域、50+ 个概念的定义和解释，要求建卡

流程：
1. 先建顶层 source 卡（如「AI伴侣技术栈概述.md」）← 所有卡片统一引用
2. 建全部领域目录（mkdir -p）
3. 先手写 3 张样卡 → 用户确认风格（类比栏行数、正反例密度）
4. 用户确认后，用 delegate_task 分 3 批并行：
   - 每批 agent 拿到：完整格式规范 + 样例卡路径（agent 先读） + 该批概念素材 + 目标路径
   - ⚠️ context 中必须包含：类比栏恰好 3 行、正例 ≥2、反例 ≥1、关系网指令
   - 按领域分组派活，每批 ~15-20 张（不要一个 agent 扛 25+ 张）
5. 等全部返回 → 抽 4-5 张卡验收（frontmatter + 类比行数 + 正反例数 + 跨域关系）
6. 验收通过 → 完成

关键：样例必须先确认再批量派活——避免 50 张卡全部返工。
详见 references/concept-list-delegation.md（delegate_task 上下文模板）。
```

### 从代码仓库提取知识文件（GitHub 项目文档 → 卡片）

```
用户: "把这个 GitHub 项目的文档做成知识卡片"

1. git clone 项目 → find 知识文件（prompt_engineering/*.txt、docs/*.md 等）
2. 统计规模：文件数 + 总行数 + 预估卡片数 → clarify 策略（直接写 vs 样卡→委派）
3. 复制源文件到 Sources/，⚠️ .txt 必须转 .md（for f in *.txt; do cp "$f" "Sources/$(basename "$f" .txt).md"; done）
4. 读取 2-3 个最大/最重要的源文件理解内容类型
5. 写 3 张样卡（选三个不同层次的概念：骨架概念、程序流程、具体交易概念）
6. 验证样卡合规（frontmatter 5 键 + 7 章节 + 类比 3 行 + 正反例 ≥2/≥1）
7. 用户确认风格后 → delegate_task 分批并行建剩余卡片
8. 验收：统计产出 vs 预期，抽 4-5 张卡逐项检查
```

> **关键：合并同类源文件**。PA Agent 的 prompt_engineering/ 有 29 个文件，但「极速上涨分析识别+极速上涨交易策略」是同一概念的识别篇+策略篇，合并为 1 张「极速上涨」卡，不要拆成 2 张薄卡。分析识别+交易策略成对出现的文件一律合并。

### 自整理知识的 source 卡模式

当用户直接提供概念内容（非从书本/文章提取）时：
1. 在顶层 Sources/ 创建一张概述卡，如 `AI伴侣技术栈概述.md`
2. 概述卡内容：领域架构说明 + 概念列表
3. 所有概念卡片的 `source` 统一指向 `"[[概述卡名]]"`
4. 这保证了 wikilink 不悬空，且 Obsidian 图谱中有统一的来源节点

### 大任务（10+ 概念或课程/书籍）

```
用户: "把这本书第3章建卡"

1. 先估算范围：几节、预计几张卡
2. 抽样 3 张样卡 → 确认
3. 按节批处理，每批 5 张
4. 批量写入后统一验证（用 search_files 而非手动翻卡）：
```bash
# 检查每张卡是否包含全部 7 个必需章节
search_files(path="<Domain>/Concepts", pattern="## 类型判定", output_mode="count")
search_files(path="<Domain>/Concepts", pattern="## 类比 ★", output_mode="count")
search_files(path="<Domain>/Concepts", pattern="## 是什么", output_mode="count")
search_files(path="<Domain>/Concepts", pattern="## 正例", output_mode="count")
search_files(path="<Domain>/Concepts", pattern="## 反例/边界", output_mode="count")
search_files(path="<Domain>/Concepts", pattern="## 详细解释", output_mode="count")
search_files(path="<Domain>/Concepts", pattern="## 关系", output_mode="count")
# 检查禁用字段（id/title/tags 不应出现）
search_files(path="<Domain>/Concepts", pattern="^(id|title|tags):", output_mode="count")
# 检查 frontmatter 边界符（每卡 2 个 ---，总计 = 卡片数 × 2）
search_files(path="<Domain>/Concepts", pattern="^---$", output_mode="count")
```
所有 count 必须等于卡片总数；不一致时定位缺章节的卡片手动补全。
```

> ⚠️ **合并同类，别每源一卡**（2026-07-22 用户纠正）：当多个源文件覆盖同一主题的不同侧面时，**合并成 1-2 张丰富卡片**，不要每个源文件各出一张薄卡。用户明确纠正过「合成吧」——碎片卡片不如一张好卡片。
>
> **合并原则**：
> - 同主题、不同分集（如「路由传参(一)+(二)+URL传参」）→ 合并为一张综合卡
> - 同一项目的「介绍+部署+使用」→ 合并为 1-2 张项目卡
> - 同一技术的「原理+配置+部署」→ 合并为 1-2 张技术卡
> - **反模式**：Chatglm2+langchain 4 篇各生成一张 → 应合并为 2 张（部署篇 + 配置篇）
> - 合并后的 source 字段列出所有来源：`source: "[[源1_原文]] / [[源2_原文]]"`
> 📋 实战案例：[references/merge-plan-example-price-action.md](references/merge-plan-example-price-action.md) — 29 源→33 卡，3 Agent 并行，零缺陷验收，含完整的三组拆分策略和验证命令

### 超大规模（40+ 概念，整本书/整门课）

详见 `references/batch-delegation-template.md`（delegate_task 上下文模板）和 `references/source-extraction.md`（原文提取脚本）。

```
用户: "把这门课全部建卡"  → 40+ 节逐字稿

流程：
1. 一次性提取所有原文文本（python-docx → Sources/）
2. 写 3 张样卡 → 用户确认风格（含类比！）
3. 用 delegate_task 并行分派：3 个 leaf agent 各处理一个章节
   - 每个 agent 独立读源文件 → 写 .md
   - 提供完整的卡片模板 + 3 张样卡作为格式参考
   - 上下文必须包含：「类比要求」（夸张生活场景）
   - ⚠️ 每个 agent 卡片数控制在 8-12 张，≥15 张时拆成两个子任务
4. 等子 agent 返回 → **统计实际产出**（`ls Concepts/ | wc -l`）→ 有缺卡则"补刀"（重新 delegate_task 仅未完成的源文件，≤8 张卡）
5. 全部完成后统一检查 wikilink 完整性
5. 全部完成后统一检查 wikilink 完整性

关键：不要自己一张张写，超大规模用 delegate_task 并行处理。
每批最多 3 个 agent（delegation.max_concurrent_children 限制）。

---


```

## 陷阱（实操中反复踩过的坑）

### 🔴 陷阱 1：Source 文件是 .txt → Obsidian wikilink 无法解析

**问题**：python-docx 提取原文默认存为 `.txt`，但 Obsidian 的 `[[wikilink]]` 只解析 `.md` 文件。卡片 frontmatter 中 `source: "[[文件名]]"` 指向 `.txt` 文件时，点击无法跳转，图谱中也是断链。

**修复**：提取完成后，在终端执行：
```bash
for f in "<Domain>/Sources/"*.txt; do mv "$f" "${f%.txt}.md"; done
```
或者直接在提取脚本中输出 `.md` 后缀。

### 🔴 陷阱 2：delegate_task 子 agent 迭代次数不足导致缺卡

**现象**：子 agent 在 `max_turns` 内写不完所有卡片（尤其 ≥12 张时常见），任务标记为 `completed` 但实际产出不完整。

**对策**：
1. 父 agent 收到返回后，立即统计实际写入的卡片数 vs 预期数
2. 缺卡部分重新发起一个小范围的 `delegate_task`（"补刀"）——只传未完成的源文件
3. 补刀任务的卡片数控制在 ≤8 张，降低单 agent 负担
4. 或在一开始就拆分：≥15 张卡的任务拆成两个子任务（各 7-8 张），走 3 agent 并行或两轮

- **不要漏类比**：每张卡必须有「类比」栏（一句话比喻 + 生活映射表）。这是用户反复强调的核心要求——干巴巴的学术定义没有价值
- **不要用占位符**：禁止 "待补充"、"TODO"、"???" 等填充内容
- **不要空卡片**：禁止只有标题没有内容的卡片
- **不要建 pipeline**：不需要 scanner→merger→writer→linker→reviewer 多角色流程
- **不要跨域链接**：独立领域（如 `Data-Structures`、`Linear-Algebra`）的卡片只能 `[[wikilink]]` 指向**同领域**的卡片，不要跨领域链接（如线代卡指向数据结构卡）。这控制每个文件夹的维护边界，改一个领域不用操心别的领域。
  - **例外**：统一知识图谱（如 `AI伴侣技术栈/` 下按子域分文件夹）内部允许跨子域链接——比如 `AI伴侣-后端工程` 的 SSE 可以指向 `AI伴侣-基础设施` 的 WebSocket，因为它们同属一个知识体系。判断标准：顶层文件夹是同一个名字，子文件夹是其组成部分。
- **写技能时给模板，别 snapshot 当前状态**：技能应描述「怎么做」的通用模式，而非「现在有什么」的目录快照。快照会过时，模板不会

### 🔴 陷阱 3：每源一卡 → 碎片化（2026-07-22 用户纠正）

**现象**：处理 60+ 源文件时，默认每个源各生成一张卡片，导致大量碎片薄卡——同一主题被拆成 3-4 张（如「路由传参(一)」「路由传参(二)」「URL传参」各一张），阅读体验差，关系链也难以维护。

**修复**：在 delegate_task 的 context 中明确指示 agent **合并同类源文件**——把同一主题的多篇原文合并成 1-2 张综合卡片。source 字段用 `/` 分隔多个来源。如果在派活前就做合并规划（告知 agent 哪些源文件应合并处理），效果更好。

### 🔴 陷阱 4：超短源文件（≤20 行）——不能跳过

**现象**：某些源文件只有 10-20 行（如「50 种行业清单」只有简介没有具体列举），容易被判定为"不值得建卡"而跳过，但其中仍可能包含独立的核心概念（如「私有化大模型」）。

**对策**：超短源文件至少出 1 张卡——如果源文件引入了一个与其他源都不重复的概念，就必须建卡。只有源文件完全没有新概念（纯过渡性/预告性内容）才可以跳过。

### 🔴 陷阱 5：转录错别字 → 不可验证的产品名（2026-07-22）

**现象**：课程逐字稿中语音转录产生的错别字（如「毕昇」→「毕胜」、「Dify」→「Define」），被直接用作卡片名。用户搜不到该产品，卡片失去价值。

**对策**：
1. **建卡前验证产品名**：如果源文件中出现疑似产品名（如「XX 平台」「XX 项目」），先判断——这个名能搜到吗？和同域其他卡片描述的是同一个东西吗？
2. **不确定就泛化**：无法验证的具体产品名 → 改为概念分类卡。例如「毕胜：低代码大模型应用平台」→「低代码大模型应用平台」（作为分类概念，Dify/DB-GPT 是其子类实例）。source 字段保留原始转录文字，概念名不要照搬。
3. **交叉比对同域源文件**：如果两个源文件描述高度相似但名字不同（如「大模型项目7」和另一个「XX 平台」），很可能是同一产品的不同称呼——合并处理，不要各建一张。

### 🔴 陷阱 6：卡片写完后用户找不到（2026-07-29）

**现象**：卡片写入 Concepts/ 后，Hermes 回复中说了路径，但用户仍然问"卡片放哪里去了"——因为路径埋在文字段落里不够显眼。

**修复**：每轮写完卡片后，回复末尾必须包含一个**独立的、显眼的文件树**：

```
D:\Contents\DRBCV-Knowledge\<领域>\Concepts\
├── 卡片1.md
├── 卡片2.md
└── 卡片3.md
```

并附加一句"用 Obsidian 打开 `D:\Contents\DRBCV-Knowledge` 这个 Vault，左侧刷新即可看到"。不要把路径藏在长段落里——用户扫一眼就能看到的位置才是正确的。

新建 vault 后记得在 `.obsidian/graph.json` 中设置：
```json
{
  "search": "-path:Sources -path:Templates -path:Articles -path:temp -path:media",
  "hideUnresolved": true
}
```



## 数学公式规范

LaTeX 公式中的坑：
- 不要用 `|x|`（会被 markdown 表格解析为列分隔符），用 `\lvert x \rvert`
- 不要在代码块里用双反斜杠 `\\`
- 公式较多的卡片用列表而非表格展示例子

详见 `D:\Contents\DRBCV-Knowledge\Templates\数学公式规范.md`
