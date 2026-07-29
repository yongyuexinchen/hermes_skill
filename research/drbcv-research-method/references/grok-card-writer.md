# Grok Build Card-Writer（批量建卡替代方案）

## When to Use
- 10+ source files, 20+ expected cards
- Sources are lecture transcripts, course notes, or any long-form text
- Repetitive file operations (batch create + verify) would drain Hermes tool calls
- DeepSeek API available (cache makes re-reading sources nearly free)

## When NOT to Use
- <5 source files (Hermes direct write_file is faster and cheaper)
- Cards require deep math reasoning (use V4-Pro directly, not delegated to Grok)
- Single-card refinement (overkill)

## Workflow

### Step 1: Convert Source Files
If sources are `.docx`, convert to `.md` first:

```python
# Install: pip install python-docx (use system python, not hermes venv)
from docx import Document
for fp in docx_files:
    doc = Document(fp)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    # Also extract tables
    content = "\n\n".join(paragraphs)
    write to out_dir / f"{basename}.md"
```

Windows note: use `/c/ProgramData/anaconda3/python` (hermes venv may not have python-docx).

### Step 2: Create Task Spec
Save a `TASK-任务名.md` in the vault root:

```markdown
# 知识库建卡任务书

## 任务
从 Sources/ 中的源文件提取核心概念，按 DRBCV 格式创建知识卡片。

## 卡模板（严格遵守）
[Paste the full DRBCV card template here — frontmatter, type判定, 正例, 反例, 详细解释, 生活类比, 关系]

## 第一步（验证批：3-5篇）
处理以下源文件：
- 文件名1.md
- 文件名2.md

## 建卡原则
1. 每篇源文件提取 1-5 个核心概念
2. 判别型 vs 连接型区分明确
3. 每张卡≥1个生活类比
4. 类型判定不能全标 mixed

## 验证标准
完成后输出建卡列表 + 类型判定依据 + 遗漏检查
```

### Step 3: Run Grok Headless
```bash
cd "D:/DRBCV-Knowledge/新vault名"
grok -m deepseek-v4 -p "$(cat TASK-任务名.md)" --yolo --output-format json --max-turns 30
```

Grok will: read sources → plan concepts → create card files → verify → report.

### Step 4: Verify
- Check output JSON: `stopReason` should be `EndTurn`
- Count cards: `ls Concepts/ | wc -l`
- Spot-check 2-3 cards for DRBCV format compliance
- Run `reviewer_check.py` if available

## Batch Size Limit (Critical)

**5-7 source files per Grok task is the sweet spot.** Full data from the computer-network build (107 sources across 11 batches):

| Files | Result | Notes |
|-------|--------|-------|
| 5 | EndTurn, 25 turns | Gold standard — ample turns for reading + writing + self-review |
| 6-7 | EndTurn, 19-23 turns | Comfortable margin |
| 10-11 | EndTurn, 33-35 turns | Tight. Only works with --max-turns 35 |
| 13 | **Cancelled at 10 turns** | Too many files. Grok can't read all sources before the agent loop loses context |
| 17 | max_turns_reached at 35 | Some cards created, batch incomplete |
| 25-30 | max_turns_reached | Batch LaTeX fix task — scanning existing cards is even slower than creating new ones |

**Rule: 5-8 files when creating new cards; 3-5 files when fixing existing cards.**

## Parallel Batch Execution

When you have 20-40 source files, split into 4-5 batches of ≤10 files each, then run in parallel:

```bash
cd "D:/DRBCV-Knowledge/vault-name"
grok -m deepseek-v4 -p "$(cat TASK-02.md)" --yolo --output-format json --max-turns 30 &
grok -m deepseek-v4 -p "$(cat TASK-03.md)" --yolo --output-format json --max-turns 30 &
grok -m deepseek-v4 -p "$(cat TASK-04.md)" --yolo --output-format json --max-turns 30 &
grok -m deepseek-v4 -p "$(cat TASK-05.md)" --yolo --output-format json --max-turns 30 &
```

Or via Hermes: `terminal(background=true, notify_on_complete=true)` for each batch.

Each batch is independent — no session resume needed between them. Monitor with `process(action='poll')`.

### Python Path on Windows for Docx Conversion

Hermes venv typically lacks `python-docx`. Use Anaconda:
```
/c/ProgramData/anaconda3/python -c "from docx import Document; ..."
```
## DeepSeek Cache Observation (Confirmed Jul 2026 — 2 sessions)

| Session | Sources | Cards | Cache hit | Incremental input |
|---------|---------|-------|-----------|-------------------|
| Session 1 (Ch1-3) | 45 | 43 | ~6.5M | ~220K |
| Session 2 (Ch4-6) | ~50 | TBD | ~7M (est.) | ~250K (est.) |

**Cache hit ratio: ~97%** — re-reading source files costs almost nothing. Grok can freely re-read sources during the card-writing loop without cost penalty. This is the single biggest reason batch processing with Grok is viable.

## Stop Reason Signals

| stopReason | Meaning | Action |
|---|---|---|
| `EndTurn` | All sources processed, cards created | Verify and continue |
| `max_turns_reached` | Some cards likely created but batch incomplete | Check output, split remaining sources into smaller batch |
| `Cancelled` | Batch too large, source processing incomplete | Reduce batch to ≤8 files, retry |

## Image-Only Content Risk (Critical)

When sources are `.docx` converted to `.md`, images (protocol diagrams, topology maps, state machines, formulas as screenshots) are **lost** during text extraction. The lecture transcripts often say "如图所示" without restating the visual content in words.

**Detection**: `grep -c '如图|下图|上图|示意图' Sources/*.md`

In the computer-network test, **28 of 45 source files** had image references. ALOHA protocol was initially missed because its throughput formula and collision diagram lived only in images.

**Mitigation**:
1. Keep **original `.docx`** in a separate archive directory (not in the Obsidian vault to avoid graph clutter)
2. For image-heavy files (≥3 "如图" hits), use vision model (豆包/火山方舟) to extract image text before Grok processing
3. After Grok batch completes, scan for missing concepts: `grep -r 'concept_name' Sources/ | wc -l` — if zero hits but concept is in the syllabus, it was likely image-only

## Obsidian Graph Cleanup

After batch card creation, the Obsidian graph gets polluted by Sources/, Templates/, and TASK files. Fix via `.obsidian/graph.json`:

```json
{
  "search": "-path:Sources -path:Templates -path:TASK -path:temp -path:Systems",
  "hideUnresolved": true,
  "showAttachments": false
}
```

Also exclude any `media/` directory if broken image references (`![...](media/imageN.jpeg)`) create ghost nodes.

## Comparison: Grok vs Multi-Agent Pipeline

| Dimension | Standard Pipeline (Scanner→Merger→Writer→Linker) | Grok Card-Writer |
|-----------|--------------------------------------------------|------------------|
| Best for | Math-heavy, needs V4-Pro per card | Bulk text extraction, moderate complexity |
| File operations | Hermes tool calls (write_file per card) | Grok native file ops (faster) |
| Token cost | Scanner + Merger + Writer overhead | Single agent loop with cache |
| Relation linking | Dedicated Linker agent | Grok adds relations inline |
| Quality floor | Higher (dedicated Reviewer pass) | Needs manual spot-check |
| When to choose | >50 cards, math density, need perfect relations | 20-80 cards, text sources, accept 85% quality |

## Math Formula Spec Chain-Loading

For math-heavy vaults (微积分/线代/概率论), create a shared `数学公式规范.md` at `D:/DRBCV-Knowledge/Templates/` and inject it into Grok prompts via bash concatenation. For non-math vaults (计算机网络/数据结构), skip this entirely to save tokens.

```bash
# Math vault TASK invocation (chain-loads formula spec)
cd "D:/DRBCV-Knowledge/微积分"
PROMPT="$(cat D:/DRBCV-Knowledge/Templates/数学公式规范.md; echo; cat TASK-任务名.md)"
grok -m deepseek-v4 -p "$PROMPT" --yolo --output-format json --max-turns 35

# Non-math vault TASK invocation (no formula spec — saves ~2.6K tokens)
cd "D:/DRBCV-Knowledge/计算机网络"
grok -m deepseek-v4 -p "$(cat TASK-任务名.md)" --yolo --output-format json --max-turns 35
```

The formula spec mandates:
- Single backslashes only (`\int` not `\\int`)
- `\lvert...\rvert` instead of `|...|` in all LaTeX (prevents markdown table breakage)
- `\displaystyle` before integral signs for Obsidian-compatible rendering
- No markdown tables for formula-heavy content — use numbered lists instead

## Critical Pitfall: Grok Cannot Batch-Fix Existing Cards

Grok is **excellent at creating new cards from source text** but **terrible at scanning and patching existing cards**. Test data: 4 batches of 25-30 cards each, all hit max_turns=35 before completing. Grok also overwrites human-edited cards with lower-quality versions (observed: hand-written list-format 基本积分公式 was replaced with broken table-format by Grok's "fix").

**Rule: Use Python scripts for mechanical fixes. Use Grok only for semantic card creation from source material.**

```python
# Example: fix double backslashes across all cards (1 second, 100% reliable)
import glob, re
for fp in glob.glob("Concepts/*.md"):
    content = open(fp).read()
    content = re.sub(r'\\\\(?=[a-zA-Z{])', r'\\', content)  # \\ → \
    open(fp, 'w').write(content)
```
