# Blog Topic Pipeline — Session Example

## Context

User wanted a 3-job pipeline for tech blog topic selection:
1. 10:00 — Collect hot AI/frontend content from Hacker News + Zhihu
2. 10:30 — Filter Top 3 topics (3 criteria: depth, interest, differentiation)
3. 11:00 — Generate writing briefs (outline, viewpoints, references, word count)

All three should deliver results back to the originating chat, be continuable, and use only web tools.

## Job Prompts Used

### Job 1 (collect)

```
你是技术博客选题助手。每天早上你需要从 Hacker News 和知乎收集 AI/前端领域的热门内容。

请使用 web_search 工具完成以下搜索任务（至少执行 4 次搜索）：
1. 搜索 Hacker News AI LLM 热门文章
2. 搜索 Hacker News 前端开发热门文章
3. 搜索 知乎 AI 大模型 热门讨论
4. 搜索 知乎 前端开发 热门文章

最终输出 Markdown 格式表格，包含标题、链接、1-2句说明。
每个来源至少 5 条。优先选有深度、有争议性或新技术发布的内容。
```

### Job 2 (filter)

```
你是技术博客选题筛选助手。你的任务是根据上一个任务（Job 1）收集的热门内容输出，
筛选出 3 个最适合我们博客的选题。

评估标准：
1. 技术深度 — 是否有足够的技术干货可展开
2. 读者兴趣度 — 是否切中目标读者（AI/前端开发者）的痛点或好奇点
3. 差异化 — 与常见文章视角是否不同，能否提供独到见解

输出格式 Markdown：## 今日推荐选题 Top 3，每个选题包含排名、标题建议、
来源文章链接、选题理由（从三个维度简要说明）、建议写作角度。
```

### Job 3 (brief)

```
你是技术博客简报生成助手。根据上一个任务（Job 2）筛选出的 3 个选题，
为每个选题生成一份详细简报。

每份简报必须包含：
1. 文章大纲（3-5级标题结构）
2. 核心观点（3-5个关键论点，每个1-2句）
3. 推荐参考链接（3-5个相关资源链接）
4. 预估字数（总字数范围）

输出格式 Markdown：## 选题简报，每个选题单独一节，包含编号、标题、
大纲、核心观点、参考链接、预估字数。整体简洁专业，适合作为写作前的 brief 参考。
```

## Error Transcript (cronjob tool struggles)

The `cronjob` tool was error-prone during creation — the agent repeatedly
forgot to include `prompt` in the arguments object, producing alternating
errors:

```
"schedule is required for create"
"create requires either prompt or at least one skill"
```

Both errors mean the same thing: you're missing one of the two required
fields. The error message alternates based on which one is missing.
Resolved by switching to the CLI for creation and the `cronjob` tool
only for `action="update"` enrichment.

## Final Job Configuration

| Job | ID | Schedule | context_from | enabled_toolsets | deliver |
|-----|----|----------|-------------|------------------|---------|
| 1-Collect | `1058a11856f7` | `0 10 * * *` | — | `["web"]` | origin |
| 2-Filter | `d17afa0670ef` | `30 10 * * *` | `["1058a11856f7"]` | `["web"]` | origin |
| 3-Brief | `1b8b20ef4886` | `0 11 * * *` | `["d17afa0670ef"]` | `["web"]` | origin |

All three also set `attach_to_session: true`.