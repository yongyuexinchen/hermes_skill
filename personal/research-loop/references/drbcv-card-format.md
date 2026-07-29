# DRBCV 知识卡片标准格式

> reviewer 验收时必须逐卡对照此文件。

## Frontmatter（必须）

```yaml
---
name: <概念名，也是 Obsidian 文件名>
type: discriminant  # 四型之一
status: core        # core / exploding / unexplored
source: "[[SourceName]]"
domain: <研究主题>
---
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `name` | 中文概念名，不含英文括号 | `迪杰斯特拉算法` |
| `type` | 四型：`discriminant` / `connection` / `mixed` / `procedure` | `procedure` |
| `status` | 成熟度：`core` / `exploding` / `unexplored` | `core` |
| `source` | wikilink 格式，指向 Sources/ 下的来源卡 | `[[014 4.4.1 路由算法]]` |
| `domain` | 所属知识库 | `computer-network` |

**禁止的 frontmatter 键名：** `id`, `title`, `tags`, `created`, `updated`, `relations`

## 正文结构（必须）

```markdown
# <概念名>

## 类型判定
<一句话>

## 类比 ← 必须
**一句话比喻：** <夸张的生活场景>
| 维度 | 生活映射 |
|------|---------|
| ... | ... |

## 是什么
...

## 输入-输出空间
...

## 正例（≥2个）
...

## 反例/边界（≥1个）
...

## 详细解释
...

## 关系
### → 指向
- [[卡片A]]
### ← 被指向
- [[卡片B]]
```

**类比栏铁律：** 每张卡必须含「一句话比喻」+「生活映射表」，用夸张场景翻译抽象概念。无类比 = 不合格，退回重做。

## type 四型判定

| type | 含义 | 典型标题句式 |
|------|------|------------|
| `discriminant` | 概念的定义与边界 | "XX 是什么" |
| `connection` | 概念间的关系 | "XX 与 YY 的关系" |
| `mixed` | 混合型 | 兼有定义和关系 |
| `procedure` | 算法/过程 | "XX 的步骤" |

## 验收清单

- [ ] frontmatter 使用 `name/type/status/source/domain`，非 `id/title/tags`
- [ ] `type` 为四型之一，非 `concept`
- [ ] `source` 是 wikilink `[[...]]`，非裸路径
- [ ] 类比栏存在且含「一句话比喻」+「生活映射表」
- [ ] 正例 ≥2 个，反例 ≥1 个
- [ ] 关系栏有 `→ 指向` 和 `← 被指向`
- [ ] 文件名 = 概念名（不含 category_domain 前缀）
