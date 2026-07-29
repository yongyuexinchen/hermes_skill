# rebuild_index CWD Path Bug — Full Debug Trace

**Date:** 2026-07-19
**Phase:** 8.3 (Computer Network Knowledge Refinement)
**Bug ID:** `build_adapter_cwd_path`

## Symptom

```python
from adapters.agent import build_adapter
e = build_adapter().engine
e.rebuild_index()
e.get("tls_detail")  # → CardNotFoundError
```

And yet:

```python
from storage.markdown.markdown_storage import MarkdownStorage
s = MarkdownStorage(data_dir="E:/hermes-mini-os/knowledge/cards")
s.load("tls_detail")  # ✅ works — 1089 chars, 6 DRBCV sections
```

## Root Cause

`build_adapter()` in `adapters/agent/agent_adapter.py` used **relative** default paths:

```python
# BEFORE (broken)
def build_adapter(
    cards_dir: str = "knowledge/cards",
    index_dir: str = "knowledge/index",
) -> KnowledgeAgentAdapter:
```

These resolve against `os.getcwd()`, which varies:
- Terminal: `C:\Users\53028` → storage at `C:\Users\53028\knowledge\cards\` (WRONG)
- `execute_code` sandbox: temp dir → storage at temp/knowledge/cards/ (WRONG)
- Only works when CWD happens to be `E:\hermes-mini-os`

## The Two-Bug Cascade

**Bug 1 (primary):** CWD-dependent paths.
- `engine.rebuild_index()` → `storage.list_all()` reads wrong dir → returns old/empty cards
- `engine.get("tls_detail")` → `storage.load()` reads wrong dir → `None` → CardNotFoundError
- The 4 new DRBCV cards written to `E:\hermes-mini-os\knowledge\cards\` are invisible

**Bug 2 (secondary, masked by Bug 1):** YAML `int` tag crash.
- Card frontmatter: `tags: [computer-network, tls, security, 408]`
- YAML parser treats `408` as `int`, not `str` (unquoted bare number)
- `whoosh_search._to_document()`: `" ".join(card.tags)` → `TypeError: expected str, int found`
- This only surfaced AFTER Bug 1 was fixed, because rebuild_index was reading the wrong directory before

## Fix

### Primary fix: anchor paths to project root

```python
# AFTER (fixed)
def build_adapter(
    cards_dir: str | None = None,
    index_dir: str | None = None,
) -> KnowledgeAgentAdapter:
    from pathlib import Path as _Path
    _root = _Path(__file__).resolve().parent.parent.parent  # project root
    cards_dir = str(_root / (cards_dir or "knowledge/cards"))
    index_dir = str(_root / (index_dir or "knowledge/index"))
    ...
```

Now `build_adapter()` always points to `E:\hermes-mini-os\knowledge\` regardless of CWD.

### Secondary fix: tag type safety

```python
# In whoosh_search.py _to_document():
"tags": " ".join(str(t) for t in card.tags),  # was: card.tags
```

### Card file fix: quote numeric tags

```yaml
# In .md frontmatter:
tags: [computer-network, tls, security, '408']  # quote 408 to keep it string
```

## Verification

```bash
# Test from ANY directory
cd /
python -c "
import sys; sys.path.insert(0,'E:/hermes-mini-os')
from adapters.agent import build_adapter
e = build_adapter().engine
e.rebuild_index()
c = e.get('tls_detail')
print(c.title, len(c.content))  # → TLS 协议详解 1089
"
```

## Regression Tests

Added `tests/test_rebuild_fix.py` (6 tests):
1. `test_create_and_rebuild_keeps_id` — title/content/tags preserved
2. `test_multiple_cards_after_rebuild` — all cards survive rebuild
3. `test_rebuild_idempotent` — double rebuild same as single
4. `test_search_works_after_rebuild` — index functional post-rebuild
5. `test_deleted_not_restored` — deletes are permanent even after rebuild
6. `test_rebuild_picks_up_new_markdown` — storage.save + rebuild = visible

All tests use `tmp_path` fixture (no real file pollution).

## Lessons

1. **Factory functions with default paths must anchor to a stable reference point**, not CWD.
   `__file__` is stable; CWD changes per invocation context.
2. **YAML bare integers in tag lists** silently become `int` — always quote them or cast with `str()`.
3. **Two bugs can mask each other**: Bug 1 hid Bug 2 because the wrong directory didn't contain
   the files with int tags. Fix Bug 1 first, then Bug 2 reveals itself.
4. **InMemory mocks in unit tests mask path-resolution bugs**: always have at least one
   integration test that exercises the real `build_adapter()` factory.
