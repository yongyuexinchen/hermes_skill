---
name: research-loop
description: >
  vb-librarian Phase 5 执行技能。不自己写卡——创建 DRBCV Kanban 工作流，
  由 scanner→merger→card-writer→linker→reviewer 五 Agent 流水线生成卡片。
version: 5.1.0
category: personal
triggers:
  - vb-librarian 执行 Phase 5 时自动加载
related_skills:
  - venture-brain
  - drbcv-research-method
---

# Research Loop Skill v5.0 — DRBCV 工作流集成

## 职责

vb-librarian **不自己写卡**。在 venture-brain v6.0 的单报告模型下，它从一个 REPORT.md 中提取概念、创建 DRBCV Kanban 工作流，调度 5 个 Agent 完成卡片生成。

### ⚠️ 前置检查：验证 REPORT.md 存在

```bash
ls -la "D:/Contents/research/<date>_<主题>/REPORT.md"
```

如果 REPORT.md 不存在，说明前期 Agent 产出失败——先修复上游，不执行 Phase 5。

---

```
REPORT.md（含信息来源表）
        │
        ▼
┌───────────────────────────────────────────┐
│  DRBCV Kanban Board: drbcv-<研究主题>       │
│                                           │
│  scanner → merger → card-writer           │
│                  → linker → reviewer      │
│                                           │
│  输出: D:\Contents\DRBCV-Knowledge\       │
│        <研究主题>\Concepts\                │
└───────────────────────────────────────────┘
        │
        ▼
  vb-librarian 验收
```

---

## Phase 5 执行步骤

### Step 1：盘点源文件 + 查重

源文件只有一份 REPORT.md（v6.0 一研一报），按章节拆分为扫描范围：

```bash
# 源文件（v6.0 简化后）
D:\\Contents\\research\\<date>_<topic>\\REPORT.md
# 章节：一、行业背景 / 二、核心玩家 / 三、技术架构 / 四、商业分析 / 五、机会评估

# 查重：扫目标 Vault 已有 Concepts/
ls D:\\Contents\\DRBCV-Knowledge\\<研究主题>\\Concepts\\
```

如果有已存在的卡片，scanner 会读取 REPORT.md 对应章节并与已有卡片比对，标记为 "existing"（跳过重建）或 "update"（增量更新）。

### Step 2：创建 DRBCV Kanban Board

```bash
# 创建 board
hermes kanban boards create drbcv-<研究主题slug>

# Scanner：按 REPORT.md 章节拆任务
hermes kanban --board drbcv-<slug> create "扫描: REPORT.md § 行业背景 & 核心玩家" --assignee scanner
hermes kanban --board drbcv-<slug> create "扫描: REPORT.md § 技术架构 & 开源项目" --assignee scanner
hermes kanban --board drbcv-<slug> create "扫描: REPORT.md § 商业分析 & 机会评估" --assignee scanner

# Merger：合并去重
hermes kanban --board drbcv-<slug> create "合并: 概念列表 + 来源交叉引用" --assignee merger

# Card-Writer：生成卡片
hermes kanban --board drbcv-<slug> create "生成: DRBCV卡片" --assignee card-writer

# Linker：建立关系链
hermes kanban --board drbcv-<slug> create "链接: 关系+wikilinks" --assignee linker

# Reviewer：质量检查
hermes kanban --board drbcv-<slug> create "检查: 质量报告" --assignee reviewer
```

### Step 3：等待流水线完成

监控 Kanban 状态，所有任务 done 后进入验收：

```bash
hermes kanban --board drbcv-<slug> list
```

### Step 4：验收（Superpowers verification-before-completion）

- [ ] 卡片存在于 `D:\Contents\DRBCV-Knowledge\<研究主题>\Concepts\`
- [ ] 每张卡片 frontmatter 完整（name/type/status/source/domain）
- [ ] 无重复卡片（与已有 Vault 卡片不冲突）
- [ ] wikilinks 双向可达
- [ ] reviewer 报告通过

### Step 5：产出 DRBCV 卡片到 Vault

卡片生成完成后，验证并确认产出位置：

```bash
ls D:\Contents\DRBCV-Knowledge\<研究主题>\Concepts\
```

更新该 Vault 的 INDEX.md（卡片数量 +1，新增条目）。

---

## 关键约束

- **vb-librarian 不写卡** — 调 DRBCV 工作流
- **查重在先** — scanner 扫源文件前先扫已有 Vault
- **卡片命名** — 由 card-writer 按 DRBCV 标准命名（概念名做文件名）
- **Source 卡** — linker 根据 scanner 提取的来源自动生成

---

## 禁止事项

- ❌ vb-librarian 不要自己生成卡片内容
- ❌ 不要跳过查重直接 scanner
- ❌ 不要跳过 reviewer 验收

---

## 🔴 陷阱：卡片格式漂移（2026-07-20 实战）

card-writer Agent 可能使用 **非 DRBCV 标准的 frontmatter**。以下对比来自 Neuro-sama 调研真实产出：

### ❌ 错误格式（card-writer 实际输出）
```yaml
id: 4e08c36b-...
title: Neuro-sama 的实时 AI 直播架构
type: concept
tags: [Neuro-sama, AI-VTuber, ...]
created: 2026-07-20
source: research/2026-07-20_Neuro-sama
relations: []
```

### ✅ 正确格式（DRBCV 标准）
```yaml
name: Neuro-sama实时AI直播架构
type: discriminant
status: core
source: "[[SourceName]]"
domain: AI伴侣赛道
```

**reviewer 必须逐项检查：**

| 检查项 | 错误 | 正确 |
|--------|------|------|
| frontmatter 键名 | `id`, `title`, `tags` | `name`, `type`, `status`, `source`, `domain` |
| `type` 取值 | `concept` | `discriminant` / `connection` / `mixed` / `procedure` |
| `source` 格式 | 裸路径 `research/...` | wikilink `[[SourceName]]` |
| 类比栏 | 缺失 | 必须有「一句话比喻」+「生活映射表」 |
| 关系栏 | `relations: []` | `## 关系\n### → 指向\n- [[卡片A]]` |

**详细卡片格式规范见 `references/drbcv-card-format.md`。** reviewer 验收时必须对照该文件逐卡检查，不通过则退回 card-writer 重做。

> 📋 卡片格式参考：[`references/drbcv-card-format.md`](references/drbcv-card-format.md) — frontmatter、四型、类比栏、验收清单
