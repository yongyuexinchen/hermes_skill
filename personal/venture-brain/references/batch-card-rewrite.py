# Batch DRBCV Card Rewrite Template
# Use when vb-librarian produces cards in wrong format (≥5 cards).
# Copy this into execute_code(), populate `cards` dict, run.

from hermes_tools import write_file

base = "D:/Contents/DRBCV-Knowledge/<研究主题>/Concepts"

cards = {}

# Template card — fill in per concept:
cards["概念名"] = """---
name: <概念名>
type: discriminant          # discriminant / connection / mixed / procedure
status: core                # core / exploding / unexplored
source: "[[SourceName]]"    # wikilink to source
domain: <研究主题>
---

# <概念名>

## 类型判定
<一句话>

## 类比
**一句话比喻：** <夸张的生活场景>

| 维度 | 生活映射 |
|------|---------|
| ... | ... |
| ... | ... |
| ... | ... |

## 是什么
<核心定义，2-3 句>

## 输入-输出空间
- **输入**：...
- **输出**：...

## 正例（≥2个）
1. ...
2. ...

## 反例/边界（≥1个）
- ❌ ...

## 详细解释
<深入展开>

## 关系
### → 指向
- [[卡片A]]
- [[卡片B]]
### ← 被指向
- [[卡片C]]
"""

for name, content in cards.items():
    path = f"{base}/{name}.md"
    write_file(path, content)
    print(f"✓ {name}")

print(f"\nDone: {len(cards)} cards written")
