# 概念清单 → delegate_task 上下文模板

当用户粘贴多领域概念清单要求建卡时，按此模板组装 delegate_task 的 context。

## 使用时机

- 用户直接提供 20+ 概念的定义和解释（聊天粘贴，无源文件）
- 概念按领域分组（如"后端工程/AI基础/RAG"）
- 需要先出样卡确认格式，再批量并行

## 前置步骤

1. 建顶层 source 卡 + 全部领域目录
2. 手写 3 张样卡（选 3 个不同领域的代表概念）
3. 用户确认类比栏行数、深度后 → 派活

## delegate_task context 模板

每个 task 的 context 包含以下固定部分 + 该批概念素材：

```markdown
## 任务：为 AI 伴侣技术栈知识库创建 DRBCV 卡片

### DRBCV 卡片格式（必须严格遵守）

**Frontmatter**:
```yaml
---
name: <中文概念名>
type: discriminant  # 四型之一: discriminant/connection/mixed/procedure
status: core
source: "[[AI伴侣技术栈概述]]"
domain: <所属领域>
---
```
禁止使用: id, title, tags, created, updated, relations

**正文模板**:
```markdown
# <概念名>

## 类型判定
<一句话>

## 类比 ★
### 一句话比喻
<夸张的生活场景比喻>
### 生活映射
| 概念世界 | 现实世界 |
|---------|---------|
| ... | ... |
(必须恰好 3 行)

## 是什么
...

## 输入-输出空间
...

## 正例（≥2 个）
...

## 反例/边界（≥1 个）
...

## 详细解释
...

## 关系
### → 指向
- [[卡片A]] — 简要说明
### ← 被指向
- [[卡片B]] — 简要说明
```

### 参考样例
先读取了解风格：
- D:\Contents\DRBCV-Knowledge\<领域>\Concepts\<样例1>.md
- D:\Contents\DRBCV-Knowledge\<领域>\Concepts\<样例2>.md

### 本节需要创建的卡片

## <领域1> (<N>张)
路径: D:\Contents\DRBCV-Knowledge\<顶层目录>\<领域1>\Concepts\

**1. <概念名>**
素材: <用户提供的原始解释>
type: discriminant|procedure

...（重复至全部概念）

### 关系网要求
- 同一领域内的卡片互相建立 → 指向和 ← 被指向
- 跨子域关联要标注（如 <领域A> 的卡片 → [[<领域B>的卡片]]）
- 每张卡至少 2 个指向、1 个被指向

### 核心规则
- 类比必须用夸张生活场景
- 类比映射表恰好 3 行
- 正例 ≥2 个，反例 ≥1 个
- 文件名 = 概念名（不含英文括号）
- 完成后用终端列出所有创建的文件确认
```

## 参数建议

| 参数 | 建议值 |
|------|--------|
| 每批卡片数 | 13-19 张（≤20 稳妥） |
| 并发批数 | 3（delegation.max_concurrent_children 上限） |
| role | leaf |
| 样卡确认 | 必须先做！避免全量返工 |

## 验收 checklist

- [ ] `search_files` 统计各领域文件数 = 预期
- [ ] 抽 4-5 张卡检查：类比栏恰好 3 行、正例 ≥2、反例 ≥1
- [ ] Frontmatter 无 id/title/tags 等禁用字段
- [ ] 跨域 wikilink 引用目标确实存在

## 实战记录

- 2026-07-23: AI伴侣技术栈 58 张卡，9 领域，3 批并行（15+14+26），10 分钟完成，验收通过
