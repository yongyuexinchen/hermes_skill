# Hermes-Native Mid-Batch Card Creation

When you have 5–15 clean markdown source files producing 5–10 cards, skip the Grok Build pipeline entirely — Hermes `write_file` with parallel writes is faster, cheaper, and more reliable. Use this pattern when:

- Sources are already clean `.md` files (no docx conversion needed)
- Cards follow strict DRBCV format (7 fixed chapters, known frontmatter keys)
- Source files come in **analysis+strategy pairs** that merge into a single card
- User provides 3 reference cards (样卡) to lock in format

## Pattern: Analysis + Strategy → Single Card Merge

In Price-Agent domain, each market state has two source files (e.g., `上涨通道分析识别.md` + `上涨通道交易策略.md`). These merge into one **discriminant-type** card that covers both identification and trading rules.

For standalone methodology files (e.g., `文件15-二次入场机会.md`), the card type is typically **procedure**.

## Execution Flow

### Step 1: Read reference cards first
Read 2–3 existing well-formed cards from `Concepts/` to internalize:
- Exact frontmatter keys (name/type/status/source/domain — no id, title, tags, created, updated, relations)
- Chapter order: 类型判定 → 类比 ★ → 是什么 → 正例 → 反例/边界 → 详细解释 → 关系
- 类比 format: 一句话比喻 + 生活映射表 (exactly 3 data rows)
- 关系 format: ### → 指向 (wikilinks) / ### ← 被指向 (wikilinks)

### Step 2: Read all sources in parallel
All source reads are independent — batch them in a single tool call round.

### Step 3: Write all cards in parallel
All card writes are independent — write all 8 cards in one or two batches.

### Step 4: Validate
```bash
cd "D:/Contents/DRBCV-Knowledge/<Domain>/Concepts"
for f in <card1>.md <card2>.md ...; do
  echo "=== $f ==="
  head -8 "$f"
  echo "---"
  grep "^## " "$f"
  echo ""
done
```

Check:
- [ ] All frontmatter has exactly 5 keys (name/type/status/source/domain)
- [ ] All 7 chapters present in correct order
- [ ] 类比 section has 一句话比喻 + 3-row 生活映射 table
- [ ] 关系 section has both → 指向 and ← 被指向 with wikilinks

## When Hermes-Native vs Grok Build

| Scenario | Approach |
|----------|----------|
| 1–8 cards from clean .md | Hermes write_file |
| 5–10 cards from clean .md (analysis+strategy pairs) | Hermes write_file (parallel) |
| 10+ cards from docx transcripts | Grok Build pipeline |
| 20+ cards across multiple chapters | Grok Build with TASK files |
| Single card creation/editing | Hermes write_file or patch |

## Pitfalls

1. **Don't skip the 样卡 step** — reading 2–3 reference cards locks in the format. Without it, frontmatter keys and chapter structure will drift.
2. **Parallel writes work** — all card writes are independent. Serializing them wastes turns.
3. **Validation is mandatory** — a 30-second grep pass catches frontmatter drift and missing chapters that would require manual fix later.
4. **Source wikilinks in frontmatter `source` field** — use `[[文件名]]` format to match Obsidian's wikilink resolution, even when the source file sits in `Sources/` not `Concepts/`.
