# DRBCV 卡片格式修复模式

> 适用场景：vb-librarian 产出的卡片 frontmatter 使用了错误格式（id/title/tags/relations），需要批量修复。

## 错误 vs 正确格式

```yaml
# ❌ vb-librarian 常见输出
id: 20260728-card-01
title: 创新药板块估值框架
type: concept
tags: [创新药, 估值, PB]
relations:
  - 20260728-card-02

# ✅ DRBCV 标准
name: 创新药板块估值框架
type: discriminant          # 四型之一：discriminant/anomaly/prediction/causal
status: core                # core/supplementary/draft
source: "[[调研主题名]]"     # wikilink 指向父主题
domain: 创新药投资           # 领域分类
```

## 批量修复模式（≥5 张卡片）

使用 `execute_code`，将所有卡片内容预置在 Python dict 中循环 `write_file`：

```python
from hermes_tools import write_file

cards = {}
cards["path/to/cards/01_xxx.md"] = """---
name: 卡片名称
type: discriminant
status: core
source: "[[父主题]]"
domain: 领域名
---

# 标题

## 类比
**一句话比喻**：...
| 抽象概念 | 生活映射 |
...
（完整卡片内容）
"""

# ... 其他卡片 ...

for path, content in cards.items():
    write_file(path, content)
```

## 每张卡片必须包含

1. **DRBCV 标准 frontmatter**：name, type（四型之一）, status, source（wikilink）, domain
2. **类比栏**：一句话比喻 + 生活映射表（≥3行，用夸张日常场景翻译抽象概念）
3. **≥2 正例** + **≥1 反例**
4. **双向 wikilink**：末尾的 `→ 指向` 和 `← 被指向`

## type 四型速查

| type | 含义 | 适用场景 |
|------|------|---------|
| discriminant | 区分/辨析 | "PB和PE的区别"、"License-out vs FDA申报" |
| causal | 因果分析 | "集采→创新药：利好大于利空" |
| prediction | 趋势预测 | "GLP-1可能比ADC更大" |
| anomaly | 异常发现 | "CXO估值异常低但基本面健康" |

禁止使用 `concept`、`procedure`、`framework` 等非四型值。
