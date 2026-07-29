# DRBCV Vault Migration Pattern

Reading external Obsidian/DRBCV knowledge vaults into Knowledge OS
without modifying the originals.

## Core Principle

```
D:\DRBCV-Knowledge (truth source, READ-ONLY)
        │
        ▼
adapters/drbcv/
        │  parse YAML frontmatter
        │  extract [[wikilinks]]
        │  infer domain from file path
        ▼
Knowledge OS Index (rebuildable cache)
```

**Never modify the original vault.** The adapter is read-only.
The Knowledge OS index is a cache — if it gets corrupted, re-scan and rebuild.

## Deterministic ID Generation

Use `hash(title + domain)` instead of random UUID. This ensures:
- Re-importing the same vault produces the same IDs
- `repair_relations()` can re-resolve wikilinks without ID churn
- Cards across sessions remain referenceable

```python
def _make_id(title: str, domain: str) -> str:
    return hashlib.md5(f"{domain}:{title}".encode()).hexdigest()[:8]
```

## DRBCV Card Format

```yaml
---
name: BGP协议        # → title
type: discriminant   # → type
status: core         # (not mapped)
source: "[[ref]]"    # (not mapped)
domain: computer-network  # → tags[0]
---
# Content with [[wikilinks]]
```

### Field Mapping

| DRBCV Field | Knowledge OS Field |
|-------------|-------------------|
| `name` | `title` |
| `type` | `type` (passed through) |
| `domain` | `tags[0]` (inferred from path if missing) |
| `[[wikilinks]]` in body | `relations: [related:<hash>]` |
| Full markdown | `content` (preserved) |

## Wikilink Extraction

```python
def _extract_wikilinks(content: str) -> list[str]:
    return re.findall(r"\[\[([^\]]+)\]\]", content)
```

Wikilinks become `relations` with deterministic target IDs:
```python
relations = [f"related:{_make_id(wl, domain)}" for wl in wikilinks]
```

## Domain Inference

If `domain` is not in frontmatter, infer from path:
```python
DOMAIN_MAP = {
    "Calculus": "calculus",
    "Computer-Network": "computer-network",
    "Hermes": "hermes",
    ...
}
```

## Broken Card Handling

Cards that fail YAML parsing (encoding issues, malformed frontmatter)
are reported but NOT dropped:

```python
result = scan_vault(root)
# result["broken_cards"] → count
# result["broken_files"] → list of paths
```

Common causes: Windows-1252 encoding, unclosed frontmatter, missing `name` field.

## Scan Statistics

```python
{
    "total_cards": 268,
    "broken_cards": 24,
    "by_domain": {"calculus": 103, "computer-network": 81, ...},
    "by_type": {"connection": 102, "discriminant": 60, ...},
    "cards": [...]  # list of card dicts ready for indexing
}
```

## Integration with KnowledgeEngine

```python
for card_dict in result["cards"]:
    card = Card(
        id=card_dict["id"],        # deterministic
        title=card_dict["title"],
        type=card_dict["type"],
        content=card_dict["content"],  # full original
        tags=card_dict["tags"],
        relations=card_dict["relations"],
    )
    engine.create(title=card.title, content=card.content, ...)
```
