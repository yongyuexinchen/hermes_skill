---
name: find-skills
slug: hermes-find-skills
displayName: Find Skills（场景驱动技能发现）
version: "1.0.0"
description: 场景驱动+关键词双模式技能发现工具。当用户用自然语言描述场景/需求（如"我想做一个海报""帮我分析股票"），或明确说"安装技能/find skills/找个skill"时，自动从本地已安装、SkillHub、虾评、GitHub、ClawHub 五层联合搜索并推荐最合适的技能，支持一键安装。已适配 Hermes 生态。
agent_created: true
source: 从 find-skills-1.0.0 (WorkBuddy) 适配到 Hermes
---

# find-skills（场景技能匹配器）— Hermes 适配版

## Overview

本技能用于**场景驱动的技能发现引擎**——用户用自然语言描述需求，系统自动理解意图，联合搜索并推荐最合适的技能。

> **适配说明**：原版为 WorkBuddy/Claw 生态设计。本版本已将所有路径、工具调用适配到 Hermes 生态（`~/.hermes/skills/`、`skills_list`、`skill_manage` 等）。

---

## 核心流程

### Step 0：触发判断

当用户的请求符合以下任一条件时，加载本技能：
- 描述了一个场景/需求但不确定用什么技能（"我想做XX"、"帮我分析XX"）
- 明确要求找技能（"安装技能"、"find skills"、"找个skill"）
- 询问"有没有能XX的工具/技能"

---

### Step 1：理解用户场景

从用户的自然语言描述中提取：
1. **任务意图**：用户想做什么？
2. **领域标签**：属于哪个领域？
3. **搜索关键词**：中英文都要（用于远程搜索）

**示例**：
- "我想做一个海报" → 意图：设计/制图；领域：内容创作；关键词：poster, design, 海报, 设计
- "帮我分析今天的大盘" → 意图：股票分析；领域：金融；关键词：stock, A股, 大盘, 分析

---

### Step 2：多层联合搜索

#### 2.1 第一层：Hermes 已安装技能（本地）

使用 `skills_list` 工具获取所有可用技能列表，然后对每个技能的名称和描述与用户场景做**语义匹配**。

**匹配规则**（按优先级）：
1. 用户场景关键词直接出现在技能 description 中 → 高分
2. 技能 name 与用户意图高度相关 → 高分
3. 技能 description 与用户领域相关 → 中分

> **Hermes 适配**：Hermes 的 `skills_list` 返回所有已安装+内置技能的 name 和 description，无需手动扫描目录。

#### 2.2 第二层：本地 marketplace 缓存（优先远程下载）

检查本地 marketplace 缓存：

```bash
ls ~/.hermes/skills-marketplace/skills 2>/dev/null
```

如果缓存目录中存在与用户需求匹配的技能，直接复制安装：

```bash
cp -r ~/.hermes/skills-marketplace/skills/<skill-folder-name> ~/.hermes/skills/<skill-folder-name>
```

---

#### 2.3 第三层：远程技能市场

如果本地缓存无结果，按以下顺序搜索远程技能市场：

**① SkillHub 官方市场**（主要来源，优先搜索）：

```bash
curl -s "https://lightmake.site/api/v1/search?q=<URL-encoded 中文关键词>&limit=10"
curl -s "https://lightmake.site/api/v1/search?q=<URL-encoded English keywords>&limit=10"
```

过滤 `score < 0.05` 的低相关结果。

**② 虾评技能市场**（中文技能重点来源）：

虾评 API Base URL：`https://xiaping.coze.com`（注意：不是 `coze.site`）

```bash
# 搜索技能
curl -s "https://xiaping.coze.com/api/skills/search?q=<URL-encoded 关键词>&limit=10"

# 获取技能详情
curl -s "https://xiaping.coze.com/api/skills/<skill-id>"

# 获取技能下载链接
curl -s "https://xiaping.coze.com/api/skills/<skill-id>/download"
```

> **重要**：虾评是中文技能的核心来源，对于中文场景的技能搜索，虾评的结果往往比 SkillHub 更相关。

**③ GitHub 技能仓库**（开源技能来源）：

```bash
# 搜索包含 SKILL.md 的代码
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  "https://api.github.com/search/code?q=filename:SKILL.md+<关键词>&per_page=10"

# 搜索技能相关仓库
curl -s "https://api.github.com/search/repositories?q=<URL-encoded 关键词>+skill+in:name,description&per_page=10"
```

> **认证说明**：GitHub Code Search API 需要 `GITHUB_TOKEN` 环境变量。如果没有，退化为只搜索仓库（匿名可用）。

**④ Fallback 来源**（以上均无结果时）：

```bash
# ClawHub
npx clawhub search [query]
```

---

### Step 3：智能排序与推荐

将五层搜索结果合并，按以下规则排序：

| 优先级 | 来源 | 条件 |
|--------|------|------|
| 1 | Hermes 已安装 | 语义匹配高分（可直接用） |
| 2 | SkillHub 官方市场 | score ≥ 0.3 且 downloads/installs 高 |
| 3 | 虾评技能市场 | 相关度高分（中文技能优先） |
| 4 | GitHub 开源仓库 | 相关度高分（含 SKILL.md） |
| 5 | ClawHub | 相关度高分 |
| 6 | Hermes 已安装 | 语义匹配中分（name 相关） |
| 7 | SkillHub 官方市场 | score ≥ 0.1 |
| 8 | 虾评技能市场 | 相关度中分 |
| 9 | GitHub 开源仓库 | 相关度中分 |
| 10 | ClawHub | 相关度中分 |

**去重规则**：
- 同一技能在多层出现 → 保留最高优先级记录
- 已安装技能在其他市场也出现 → 标注"✅ 已安装"

---

### Step 4：输出推荐结果

**输出格式**：

```
🔍 为你找到 {N} 个相关技能（搜索范围：Hermes 已安装 + 远程市场）：

【Hermes·已安装】✅ 可直接使用
1. {技能名} — {一句话说明}
   匹配理由：{为什么适合这个场景}
   路径：~/.hermes/skills/{技能名}/

【远程·可安装】⬇️ 需安装
2. {技能名} — {一句话说明}
   匹配理由：{为什么适合这个场景}
   来源：{SkillHub/虾评/ClawHub/GitHub}
   下载量：{downloads} | 安装量：{installs}
   安装命令：回复"安装第2个"即可
```

---

### Step 5：一键安装（如需）

如果用户选择安装远程技能：

#### 5.1 从 SkillHub 远程安装

```bash
TMPDIR=$(mktemp -d)
curl -L -o "$TMPDIR/skill.zip" "https://lightmake.site/api/v1/download?slug=<slug>"
mkdir -p ~/.hermes/skills/<slug>
unzip -o "$TMPDIR/skill.zip" -d ~/.hermes/skills/<slug>
rm -rf "$TMPDIR"
ls ~/.hermes/skills/<slug>/SKILL.md
```

指定版本安装：

```bash
curl -L -o "$TMPDIR/skill.zip" \
  "https://lightmake.site/api/v1/download?slug=<slug>&version=<version>"
```

#### 5.2 从虾评远程安装

```bash
# 1. 获取下载链接
curl -s "https://xiaping.coze.com/api/skills/<skill-id>/download"

# 2. 下载并安装
TMPDIR=$(mktemp -d)
curl -L -o "$TMPDIR/skill.zip" "<download-url>"
mkdir -p ~/.hermes/skills/<skill-name>
unzip -o "$TMPDIR/skill.zip" -d ~/.hermes/skills/<skill-name>
rm -rf "$TMPDIR"
ls ~/.hermes/skills/<skill-name>/SKILL.md
```

#### 5.3 从 GitHub 克隆安装

```bash
TMPDIR=$(mktemp -d)
git clone "https://github.com/<user>/<repo>.git" "$TMPDIR/<skill-name>"
mkdir -p ~/.hermes/skills/<skill-name>
cp -r "$TMPDIR/<skill-name>"/* ~/.hermes/skills/<skill-name>/
rm -rf "$TMPDIR"
ls ~/.hermes/skills/<skill-name>/SKILL.md
```

#### 5.4 从 ClawHub 安装

```bash
TMPDIR=$(mktemp -d)
curl -L -o "$TMPDIR/skill.zip" "https://clawhub.com/api/download?slug=<slug>"
mkdir -p ~/.hermes/skills/<slug>
unzip -o "$TMPDIR/skill.zip" -d ~/.hermes/skills/<slug>
rm -rf "$TMPDIR"
ls ~/.hermes/skills/<slug>/SKILL.md
```

---

安装完成后，提示用户："✅ {技能名} 已安装，现在可以直接用啦！"

---

## 触发词参考

| 用户表达 | 触发方式 |
|----------|----------|
| "我想做XXX" | 自动触发场景理解 |
| "帮我找XXX的技能" | 直接触发多层搜索 |
| "有没有能XXX的工具" | 触发多层搜索 |
| "这个场景应该用哪个技能" | 触发匹配推荐 |
| "吸收/安装这个技能" | 直接安装 |

---

## 🔌 技能体系结合分析

### 🔗 协作链路

```
用户场景描述 / 明确要找技能
   → find-skills（场景技能匹配器）← 唯一入口
       ├─ 第一层：Hermes skills_list → 已安装技能匹配
       ├─ 第二层：本地 marketplace 缓存 → 优先本地安装
       └─ 第三层：远程技能市场 → SkillHub / 虾评 / GitHub / ClawHub
```

### 🎯 使用场景映射

| 业务线 | 典型场景 | 可能的技能 |
|--------|---------|-----------|
| 自媒体 | "我想做小红书封面" | 图片生成类 / 封面设计类 |
| 量化交易 | "帮我分析今天的大盘" | A股数据 / 市场分析类 |
| 效率工具 | "帮我管理任务" | 任务管理 / 笔记类 |
| 开发 | "帮我写一个API" | 代码生成 / 后端开发类 |

---

## 📝 版本迭代记录

| 版本 | 日期 | 更新内容摘要 |
|------|------|------------|
| v1.0.0 (Hermes) | 2026-07-29 | 从 WorkBuddy find-skills v1.7.0 适配到 Hermes：路径改为 ~/.hermes/skills/、内置技能扫描改用 skills_list、安装逻辑增强、移除引流信息 |
