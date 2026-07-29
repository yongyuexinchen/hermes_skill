# Knowledge OS Architecture Patterns

Patterns from building Hermes Mini Knowledge OS (E:\hermes-mini-os\) — a layered personal knowledge infrastructure.

## Three-Layer Architecture (ADR-004)

```
Application Layer (CLI / Tool Server / Web)
       ↓
Core Layer (KnowledgeEngine + Provider Interfaces)
       ↑
Storage Layer (MarkdownStorage + WhooshSearch)
```

Core must NOT import Web/CLI/DB/SQLite. Application must NOT import Storage implementations directly.
All Application access goes through `adapters.agent.KnowledgeAgentAdapter`.

## Provider Interface Pattern (ADR-003)

```python
class StorageProvider(Protocol):
    def save(card) / load(id) / list_all() / delete(id) / exists(id)

class SearchProvider(Protocol):
    def index(card) / deindex(id) / search(query) / rebuild(cards)
```

Engine depends on interfaces (Protocol), not concrete classes. This enables:
- InMemoryStorage/InMemorySearch mocks for unit tests
- Drop-in replacement of search backends (whoosh → FAISS → …)
- Architecture boundary enforcement

## Adapter Layer Pattern

`adapters/agent/KnowledgeAgentAdapter` wraps Engine for Agent consumption:
- All methods return `{"status": "ok"/"error", ...}` dicts
- `build_adapter()` factory: the ONLY place that imports Storage implementations
- `set_adapter()` global injection: enables tests to inject mocks without importing Storage

## Tool Server Pattern (Phase 4.5)

`applications/tools/ToolRegistry` wraps Adapter for LLM tool-calling:
- Pydantic schemas define input/output contracts
- `registry.call_tool(name, request)` — unified dispatch
- Tools: search_knowledge, create_knowledge, update_knowledge, validate_knowledge, find_related, resolve_relation, repair_relations

CLI and Tool Server are parallel Applications — both share the same Adapter.

## CLI Testing Injection Pattern (Phase 4a)

```python
# In applications/cli/main.py:
_current_adapter = None

def set_adapter(adapter):
    global _current_adapter
    _current_adapter = adapter

def _get_adapter():
    if _current_adapter is not None:
        return _current_adapter
    return build_adapter()

# In tests:
@pytest.fixture
def runner(adapter):
    set_adapter(adapter)
    return CliRunner()
```

Pitfall: duplicate `def _get_adapter()` definitions in the same scope — the second silently overrides the first. Use `grep -n "def _get_adapter"` to check.

## Relation Resolver Pattern (Phase 5.5)

Structured relations with dangling detection:

```python
# Legacy:  "depends_on:card_tcp"
# New:     {"target_id": "a1b2c3d4", "type": "depends_on", "confidence": 0.95}

class RelationResolver:
    def resolve_target(target_name) → real_id | None
    def repair_card(card) → (fixed, failed)
    def repair_all() → {"fixed": N, "failed": N}
```

Resolution strategy: exact ID match → exact title match → fuzzy title match → not found.
Placeholder detection: `looks_like_placeholder()` detects non-UUID strings (underscores, names).

## Card Validation Bypass Pattern

Card.__post_init__ validates type/title at construction time. When a Tool/Adapter needs to pass unvalidated data to Engine for validation:

```python
card = Card.__new__(Card)       # skip __post_init__
card.id = req.card.id           # assign fields manually
card.type = req.card.type        # invalid values OK here
...
engine.validate_card(card)       # validation happens here
```

## Self-Bootstrap Experiment Pattern (Phase 4.8)

Hermes Agent uses its own Tool Server to operate on the knowledge base:
1. Search for existing knowledge
2. Analyze gaps
3. Create cards via create_knowledge tool
4. Establish relations
5. Validate all cards

Proves the closed loop: Agent reads → finds gaps → creates → relates → validates.

## Architecture Audit Pattern

```python
def _check_layer(layer_path, deny_list):
    for each .py file in layer_path:
        for each line starting with "import" or "from":
            if banned module in line and "noqa" not in line:
                violation
```

Only checks actual import statements — docstrings listing banned terms are NOT violations.
