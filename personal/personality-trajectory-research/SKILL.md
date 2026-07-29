---
name: personality-trajectory-research
description: >
  人格发展轨迹研究。基于用户完整心理画像，搜集历史上/现实中具有
  相似人格结构的个体案例，分析其发展路径、关键转折点、终局结果，
  形成对用户发展方向的结构化预判与改造建议。
version: 1.0.0
category: personal
---

# 人格发展轨迹研究 v1.0

## 目标

不依赖单一心理学流派，而是通过**真实案例的发展结果**来反推：
1. 和用户相似人格结构的人，最终走向了什么结局
2. 哪些变量决定了他们的成败
3. 用户可以从中学到什么改造策略

## 研究框架

每个案例按以下维度分析：

### 人格匹配度
- 与用户相似的核心特质（系统思维/创伤驱动/内部锚点/多系统人格）
- 差异点（关键不同）

### 发展轨迹
- 早期关键事件
- 中年转折点
- 晚年终局

### 成败变量
- 什么让他们成功
- 什么限制了他们
- 如果可以重来，最优策略是什么

### 对用户的启示
- 可直接迁移的策略
- 需要警惕的相似陷阱

## 案例来源优先级
1. 传记/自传（一手资料）
2. 学术心理传记（psychobiography）
3. 可靠的人物研究文章
4. 访谈/纪录片

> **报告结构模板**：详见 `references/report-template.md`（五章结构+评分卡模板+关键数据点清单）

## 产出格式

```
D:\Contents\research\<date>_人格轨迹研究\
├── REPORT.md                          # ★ 主报告（含所有案例分析 + 综合预判）
├── Agent1_五案例研究_中间产出.md        # Agent 1 原始搜索结果（案例人格匹配+轨迹+成败变量）
├── Agent2_多学科理论整合.md             # Agent 2 理论整合报告（15+理论 × 5学科）
├── Agent3_发展轨迹数据_中间产出.md       # Agent 3 数据搜索结果（6项搜索 + 变量评分）
└── Agent2_多学科理论整合_原始输出.txt    # 缓存原始文件（可选，从 delegate 缓存提取）
```

### 中间文件规则
- **默认（v6.0 原则）**：Agent 产出直接汇入 REPORT.md，不存中间文件（避免碎片）
- **用户明确要求时**：从 delegate 缓存提取原始输出存盘
- 缓存路径：`C:\Users\53028\AppData\Local\hermes\cache\delegation\subagent-summary-*.txt`

### DRBCV 卡片产出（不可省略）

研究完成后必须建 DRBCV 知识卡片到 Vault：

```
D:\Contents\DRBCV-Knowledge\人格发展轨迹\
├── INDEX.md
├── Sources\
│   └── 人格轨迹研究概述.md      # 源卡（研究背景+方法+核心发现）
└── Concepts\
    ├── 假性自体-Winnicott.md    # discriminant
    ├── 创伤驱动型创造力.md       # connection
    ├── 内部锚点系统.md          # discriminant
    ├── 四系统人格架构.md         # discriminant
    ├── SDT需求补偿机制.md       # connection
    ├── 弱关系桥梁理论.md         # discriminant
    ├── 独立创造者成功五因素.md    # procedure
    └── 社交孤立倒U型曲线.md      # connection
```

**建卡策略**：
- 卡片数 ≥5 时用 `execute_code` 批量写入（一次调用全部完成，避免单卡逐个 write_file 打满工具调用上限）
- 每张卡须含：DRBCV 标准 frontmatter + 类比栏（一句话比喻 + 3行生活映射表）+ ≥2 正例 + ≥1 反例 + 双向 wikilink
- 卡片 frontmatter 用 `name/type/status/source/domain`，禁用 `id/title/tags`
- 建完写 INDEX.md 收尾

## 执行流程（实战验证）

### 前置条件
1. 加载 `user-profile` skill——获取完整心理画像（人格结构、决策算法、关键经历）
2. 确认用户具体需求——是整体分析还是聚焦某个维度

### 正确执行路径（delegate_task 方案）

```
Hermes（不自行研究）
  │
  ├─→ delegate_task 1: 案例搜索与分析（5-6个历史/现实个体）
  │     搜索传记、心理传记学研究、发展轨迹、终局
  │     输出：每个案例的匹配度+轨迹+成败变量+启示
  │
  ├─→ delegate_task 2: 多学科理论整合
  │     心理学(SDT/依恋/假性自体)+社会学(弱关系/社会资本)+
  │     存在主义哲学(意义疗法)+神经科学(奖励系统/DMN)+组织行为学
  │     输出：各学派核心观点+对用户人格的解释力
  │
  └─→ delegate_task 3: 发展预判与改造建议
        搜索系统思维者职业数据、创伤创造力研究、独立创造者成功因素
        输出：预判模型+可操作改造建议
        每个数据点标注来源 URL

全部返回后：
  Hermes 整合 → REPORT.md → D:\Contents\research\<date>_人格轨迹研究\
```

### 为什么要用 delegate_task 而非 Kanban Swarm

当前环境的 Kanban profiles（researcher/vb-researcher 等）缺少 provider 配置，Worker 会秒崩（`pid not alive`）。`delegate_task` 的子 Agent 继承当前会话的 provider/model，可以直接使用 web_search。

### 并行策略
- 最多 3 个 delegate_task 并发（当前 `delegation.max_concurrent_children` 限制）
- 如果研究维度 > 3，分两轮派活
- 每个 Agent context 必须包含：用户关键人格特征摘要（从 user-profile 提取）+ 具体搜索指令 + 输出格式要求 + 来源标注要求

## 禁止事项
- ❌ 不要只做理论推演，必须有真实案例支撑
- ❌ 不要美化或妖魔化任何案例人物
- ❌ 不要跳过失败案例只看成功案例
- ❌ 不要给出无法操作的抽象建议
- ❌ 不要用 Kanban Swarm——profile 缺 provider 会崩溃（2026-07-28 实战验证）
- ❌ Hermes 不要自己写第一版分析——先派 Agent 搜索，再整合
