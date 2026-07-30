# Merge Plan Example: PA Agent (29 sources → 33 cards)

Real run: 2026-07-29. Source: `PA_Agent/prompt_engineering/` (29 `.txt` files, ~400KB, ~7,900 lines).
Result: 33 DRBCV cards, 0 forbidden frontmatter keys, 100% analogy coverage, all 6 required chapters present.

## 3-way split strategy

| Group | Domain | Source files | Cards | Agent instruction |
|-------|--------|-------------|-------|-------------------|
| A | Core framework | 市场诊断框架, 二元决策, 提示词大纲 | 10 | Extract 8 cycle states + gate + trader's equation |
| B | State strategies | 11 files (analysis + strategy pairs) | 8 | **Merge each pair** into 1 card (e.g. 上涨通道分析+策略 → 上涨通道) |
| C | Patterns & signals | 15 files (file14–28, 逐棒检查单) | 12 | Mostly 1:1, with one merge: 最终旗形+趋势反转MTR |

## Merge directives that worked

The key to avoiding fragmentation: **tell the agent exactly which files to merge before it starts reading.**

```
1. 上涨通道分析识别.md + 上涨通道交易策略.md → 合并为 1 张「上涨通道」卡
2. 下跌通道分析识别.md + 下跌通道交易策略.md → 合并为 1 张「下跌通道」卡
3. 极速上涨分析识别.md + 极速上涨交易策略.md → 合并为 1 张「极速上涨」卡
...
```

Without explicit merge directives, agents default to 1:1 source-to-card mapping → fragmentation.

## Sample card quality

| Card | Analogy | Quality |
|------|---------|---------|
| 尖峰 | "高速公路上飙车——不能追只能等靠边" | ★★★ |
| 铁丝网 | "堵死在高速上踩油门——烧了一箱油还在原地" | ★★★ |
| 信号棒 | "过马路绿灯——不是亮了就冲，还得看有没有闯红灯的车" | ★★★ |

## Verification commands

```bash
# Total cards
ls Concepts/*.md | wc -l

# Frontmatter delimiter integrity (should = cards × 2)
search_files(pattern="^---$", target="content", path="Concepts")

# Analogy coverage (should = card count)
search_files(pattern="^## 类比", target="content", path="Concepts")

# Forbidden keys (should = 0)
search_files(pattern="^(id|title|tags|created|updated|relations):", target="content", path="Concepts")

# Required chapters (should = cards × 6)
search_files(pattern="^## (类型判定|是什么|正例|反例|详细解释|关系)", target="content", path="Concepts")
```
