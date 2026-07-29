# Relation Repair System Pattern

From Phase 9.5 — Knowledge Graph Repair for Hermes Mini Knowledge OS.

## Problem

DRBCV vault migration generates relations from wikilinks (`[[Card Title]]`) using
deterministic hashes. When the wikilink text doesn't match the card's frontmatter
`name` field exactly, the generated relation ID points to a non-existent card.

Example: wikilink `[[TCP握手]]` → hash `abc123`, but card on disk has title
`TCP三次握手与四次挥手` → hash `xyz789`. Relation broken.

## Architecture

```
core/relation/relation_repair.py     ← Core layer (no fastapi/click)
applications/api/routes/relations.py ← API layer
```

## Three-Layer Resolution

```python
class RelationRepairEngine:
    def resolve_one(self, target_name: str) -> str | None:
        # Layer 1: exact match (storage.load by ID)
        # Layer 2: normalized match (strip spaces, punctuation, lowercase)
        # Layer 3: alias table + fuzzy title contains match
    def resolve_all(self, dry_run: bool = True) -> dict:
        # dry_run=True: report only, no write
        # dry_run=False: apply fixes via storage.save()
```

## Dry-Run Safety

CRITICAL: implement `dry_run=True` as default. First run analyzes only.
Second run with `dry_run=False` applies fixes after human confirmation.

```python
# API: always dry-run first
POST /api/relations/repair?apply=false  → report
POST /api/relations/repair?apply=true   → execute
```

## Real Results (Phase 9.5)

| Metric | Before | After |
|--------|--------|-------|
| Total relations | 42 | 42 |
| Broken | 27 | 21 |
| Fixed | — | 19 |

Remaining 21 broken relations are from DRBCV wikilinks pointing to cards
not yet imported into Knowledge OS (e.g., `[[函数极限]]` → card is `极限定义`).

## Normalization Function

```python
@staticmethod
def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\u4e00-\u9fff]", "", text)  # remove all non-word, non-CJK
    return text
```

## When the Three-Layer Engine Resolves Zero

If `resolve_all()` returns `resolved: 0, failed: N` (all hash IDs are random/unrelated to titles),
the engine can't help. **Fallback: Wikilink Body Parsing**.

The card bodies contain `[[wikilinks]]` that DO reference real card titles. Parse those instead:

```python
# 1. Build title→id index from all cards
title_to_id = {}
for card in storage.list_all():
    full = storage.load(card.id)
    if full:
        title_to_id[full.title] = full.id

# 2. Parse wikilinks from body content, resolve by title
WIKILINK_RE = re.compile(r'\[\[([^\]]+)\]\]')
for filepath in glob.glob('knowledge/cards/*.md'):
    # Parse YAML frontmatter + body
    fm = yaml.safe_load(frontmatter_text)
    wikilinks = WIKILINK_RE.findall(body)
    # Resolve: exact → normalized → substring
    new_relations = [f'related:{title_to_id[title]}' for title in wikilinks
                     if title in title_to_id]
    # Rewrite card file with fixed relations
    fm['relations'] = new_relations
    write_file(rebuild_yaml(fm) + body)
```

See `scripts/repair_relations_from_wikilinks.py` for the full production script.

## Pitfalls

1. **Don't resolve by substring alone**: `[[TCP]]` should not match `[[TCP拥塞控制]]` unless
   the target is clearly unique. Prefer exact and normalized matches over fuzzy.

2. **Always rebuild index after repair**: Changes to card relations via `storage.save()`
   bypass the search index. Call `engine.rebuild_index()` after applying fixes.

3. **Test with InMemory backends**: The repair engine takes `StorageProvider` as
   constructor arg, enabling clean unit tests without filesystem dependency.

4. **Hash IDs ≠ Title Hashes**: DRBCV migration sometimes generates random hash IDs
   that have no semantic relationship to card titles. When `scan_broken()` shows 100%
   broken and `resolve_all()` returns 0 fixes, the engine's title-matching is useless
   — fall back to wikilink body parsing.

5. **YAML numeric tag quoting**: Tags like `408` must be quoted as `'408'` in YAML
   frontmatter or they'll be parsed as integers, breaking join/split operations
   downstream. Use `yaml.dump(..., sort_keys=False)` to preserve order.
