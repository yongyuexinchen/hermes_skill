---
name: knowledge-system-architecture
description: >
  Patterns for building layered knowledge management systems — Core/Storage/Application separation,
  Provider interfaces, dependency injection, Relation Resolvers, Agent Adapters, Tool Servers,
  and Hermes skill integration. Use when architecting any system where knowledge sovereignty
  (files over databases) and agent operability are design goals.
version: 1.0.0
author: Hermes Agent
triggers:
  - building a knowledge system
  - DRBCV architecture
  - knowledge engine design
  - agent knowledge integration
  - layered architecture with Provider interfaces
  - relation resolution systems
  - relation repair / broken edges detection
  - knowledge graph maintenance
  - tool server for agents
  - cross-domain bridge generation
  - knowledge graph analysis between domains
  - bridge proposal system
---

# Knowledge System Architecture

> ⚠️ **ARCHIVED**: Knowledge OS 项目已于 2026-07-20 归档至 `E:\hermes-mini-os-archived\`。
> 知识维护现已简化为 Obsidian + Hermes 直写。本 skill 保留作为架构参考文档。
> 活跃的知识建卡流程见 `drbcv-research-method` skill。

Reusable patterns from building Hermes Mini Knowledge OS (Phase 0-6) — archived.

## Architecture Decision Records (ADR) Template

Every architectural choice worth debating deserves an ADR. Format:

```markdown
# ADR-NNN: Decision Title

| 属性 | 值 |
|------|-----|
| **状态** | ✅ 已采纳 / ⬜ 提议中 / ❌ 已废弃 |
| **日期** | YYYY-MM-DD |
| **决策者** | Role |
| **前置 ADR** | [NNN](...) |

## 背景 — 备选方案 — 决策 — 理由 — 代价 — 否决理由 — 影响
```

Key ADRs from Knowledge OS:
- 001: Markdown + YAML storage (knowledge sovereignty in files)
- 002: Search layer independent (index is cache, rebuildable)
- 003: Engine depends on interfaces (dependency inversion, testable)
- 004: Three-layer split (Application → Core ← Storage)
- 005: Search returns Cards not IDs (instant usability)
- 006: Hermes ↔ Knowledge OS integration (no dual memory/planner)

## Three-Layer Architecture

```
Application Layer          Core Layer            Storage Layer
─────────────────    ─────────────────    ─────────────────
CLI (click+rich)         contracts/          markdown/
Tool Server (7 tools)      CardProtocol        MarkdownStorage
Hermes Skill Adapter       StorageProvider     .md files (truth)
                           SearchProvider
                          models/              index/
                            Card dataclass      WhooshSearch
                          engine/               jieba tokenizer
                            KnowledgeEngine     index (rebuildable)
                            RelationResolver
                            exceptions
```

### Layer Rules

| Layer | Can Import | Forbidden |
|-------|-----------|-----------|
| Core | contracts, models, stdlib | fastapi, click, sqlite3, applications, storage.* |
| Storage | core.contracts, core.models | applications, frontend |
| Application | adapters, core.engine | storage.markdown, storage.index |
| Adapter | core, storage | applications (except hermes bridge) |

## Provider Interface Pattern

Define Protocols in `core/contracts/`. Implement in `storage/`. Inject into `core/engine/`.

```python
# core/contracts/ — the contract
class StorageProvider(Protocol):
    def save(self, card: CardProtocol) -> None: ...
    def load(self, card_id: str) -> CardProtocol | None: ...
    def list_all(self) -> list[CardProtocol]: ...
    def delete(self, card_id: str) -> bool: ...
    def exists(self, card_id: str) -> bool: ...

# storage/markdown/ — the implementation
class MarkdownStorage:  # satisfies StorageProvider by structural subtyping
    def save(self, card): ...

# core/engine/ — dependency injection
class KnowledgeEngine:
    def __init__(self, storage: StorageProvider, search: SearchProvider):
        self._storage = storage
```

### Test Mock Pattern

```python
# tests/conftest.py
class InMemoryStorage:
    """Dict-based mock — no filesystem dependency."""
class InMemorySearch:
    """Substring-match mock — no whoosh dependency."""

# tests/test_engine.py
engine = KnowledgeEngine(storage=InMemoryStorage(), search=InMemorySearch())
```

## Tool Server Pattern

Thin layer over adapter. Pydantic schemas for type safety. Registry for dispatch.

```
Agent → ToolRegistry.call_tool(name, request) → adapter → engine → storage/search
```

```python
# schemas.py — Pydantic models
class SearchRequest(BaseModel): query, tags, limit
class ToolResponse(BaseModel): status, data, error

# server.py — registry
class ToolRegistry:
    def __init__(self, adapter): self._tools = {...}
    def call_tool(self, name, request) -> ToolResponse: ...
```

## Relation Resolver Pattern

### Problem
Agent creates cards with placeholder relations: `"depends_on:card_tcp"` → but real ID is UUID.

### Solution: Backward-compatible migration
```python
# Old format (still readable)
relations = ["depends_on:card_tcp"]  # string

# New format (auto-resolved)
relations = [{"target_id": "a1b2c3d4", "type": "depends_on", "confidence": 0.9}]  # dict

# Normalize — handles both
def normalize_relation(rel) -> dict: ...
```

### Resolver
```python
class RelationResolver:
    def resolve_target(self, target_name: str) -> str | None:
        """title match → ID match → fuzzy match → None"""
    def repair_all(self) -> {"fixed": N, "failed": N}: ...
```

## Agent Adapter Pattern

Bridge between application layer and engine. Returns structured dicts for easy agent parsing.

```python
class KnowledgeAgentAdapter:
    def __init__(self, engine): self.engine = engine  # expose for advanced ops
    def search_knowledge(query, tags, limit) -> {"status":"ok", "results":[...]}: ...
    def create_knowledge(title, content, ...) -> {"status":"ok", "card":{}}: ...
```

### Production Factory
```python
# adapters/agent/ — the ONE place that knows about concrete storage/search
def build_adapter(cards_dir, index_dir) -> KnowledgeAgentAdapter:
    engine = KnowledgeEngine(
        storage=MarkdownStorage(cards_dir),
        search=WhooshSearch(index_dir),
    )
    return KnowledgeAgentAdapter(engine)
```

## CLI Testing Injection Pattern

CLI layer must not import storage.* (architecture rule), but needs mock for tests.

```python
# applications/cli/main.py
_current_adapter: KnowledgeAgentAdapter | None = None

def set_adapter(adapter):    # test injection point
    global _current_adapter
    _current_adapter = adapter

def _get_adapter():           # inject first, fallback to production
    if _current_adapter is not None:
        return _current_adapter
    return build_adapter(...)

# tests/test_cli.py
@pytest.fixture
def runner(mock_adapter):
    set_adapter(mock_adapter)   # inject before invoke
    return CliRunner()
```

## Hermes Skill Integration Pattern

Knowledge OS registered as a Hermes skill. See also `references/self-bootstrap-experiment.md`
for the Agent-driven knowledge gap discovery and completion pattern.

```
hermes/skills/knowledge-os/
├── SKILL.md       ← triggers, operations, when to use
├── config.yaml    ← project_path, adapter_module
├── tools.md       ← tool reference for agent
└── examples/      ← usage scenarios
```

```python
# adapters/hermes/__init__.py
class KnowledgeHermesAdapter:
    """5 operations: search, create, update, relate, review"""
    def search(query, tags, limit) -> {"status":"ok","operation":"search","result":...,"verification":"..."}: ...
```

## DRBCV Vault Migration

See `references/drbcv-vault-migration.md` for the full pattern: deterministic
ID generation, wikilink extraction, domain inference from path, broken card
handling, and integration with KnowledgeEngine.

**Real migration results (Phase 7):**
- 268 DRBCV cards scanned, 166 indexed, 24 broken (Calculus YAML encoding)
- Domain distribution: Calculus 103, Computer-Network 81, SillyTavern 46, Hermes 32, Grok-Build 6
- Scan time: 0.3s for 418 .md files across all vaults

## Knowledge Curator Pattern

See `references/knowledge-curator-skill.md` for the four-operation analysis
pattern (scan → review → plan → explain). Curator is read-only; knowledge-os
does the writes. Includes real Phase 8.2 Computer Network audit results.


## Web API Layer Pattern

See `references/web-api-layer.md` for the FastAPI Application Layer pattern:
TestClient with InMemory injection, Pydantic schema isolation, AST-based
architecture enforcement, and the 9-endpoint layout.

## Frontend Knowledge Explorer Pattern

See `references/frontend-knowledge-explorer.md` for the React+Vite+TypeScript SPA
pattern: API client centralization, Cytoscape.js dynamic import for graph visualization,
dark theme CSS variables, and the `/api/graph` backend endpoint for node-edge data.

**Setup pitfalls**: See `references/frontend-setup-pitfalls.md` — Vite proxy
config, int-tag YAML crash, API type assumptions.

## Full Vault Health Audit Pattern

See `references/full-vault-health-audit.md` for the cross-domain knowledge
graph analysis pattern used in Phase 8.6: graph shape classification
(mesh vs chain), cross-domain edge detection, Agent Readiness scoring (80/100
baseline), and the five-tier S/A/B/C/D asset rating system.


## Bridge Generator Pattern

See `references/bridge-generator.md` for the cross-domain bridge discovery
pattern: rule-based analysis (tag crossover + keyword overlap + structure
similarity), human-in-the-loop acceptance, 5 bridge types, and the weighted
scoring formula (0.4×tag + 0.3×keyword + 0.3×structure).

## Maintenance Cron Pattern

See `references/maintenance-cron-system.md` for the read-only maintenance
system pattern: 5 scheduled jobs (health_scan, quality_review, relation_review,
growth_report, evolution_suggestion), API endpoints, report generation, and
the constraint that maintenance never auto-modifies knowledge.

## Interactive Health CLI

See `references/kos-health-cli.md` for the `kos health` on-demand CLI command:
leverages MaintenanceAdapter's four read-only methods, outputs matching
`knowledge/reports/YYYY-MM-DD.md` format, supports `--output` file writing,
and includes the mock-based CLI test pattern.


## Relation Repair System

See `references/relation-repair-system.md` for the three-layer resolution pattern
(exact → normalized → fuzzy), dry-run safety mechanism, and Phase 9.5 repair
results (27→21 broken, 19 fixed).

**When the engine resolves zero** (all hash-based IDs are random, not derived
from titles), fall back to parsing `[[wikilinks]]` from card bodies and matching
against a title→id index. See `scripts/repair_relations_from_wikilinks.py` for
the production script. Phase 10 results: 154/196 cards fixed, 526/784 wikilinks
resolved (from 382/382 broken → 13 broken after fix).


## Common Pitfalls

1. **Core importing Application**: Core must never import CLI/Tools/Web. If you find yourself importing `applications.*` in `core/`, the dependency is inverted.

2. **Application bypassing Engine**: CLI/Tools must go through adapter/engine. Direct `storage.save()` in CLI = architecture corruption.

3. **Knowledge in database**: ADR-001 says Markdown is truth. SQLite is for metadata only (search history, user prefs), NOT knowledge content.

4. **Dual memory systems**: Hermes Memory (short-term conversation) and Knowledge OS (long-term structured knowledge) serve different purposes. Don't merge them.

5. **Card constructor rejects invalid data**: `Card(type="bad")` raises in `__post_init__`. When tool/validate needs to pass unchecked data, bypass with `Card.__new__(Card)` + manual field assignment.

6. **Duplicate function definitions**: Python silently overwrites. `grep -n "def funcname"` before assuming a function behaves as written.

7. **Click underscore→hyphen**: `def list_cards` becomes `list-cards` CLI command. Test accordingly.

8. **Custom .md card filenames**: Card.from_markdown() and storage.load() work with any filename (e.g. `tls_detail.md`). Use engine.create() for production card creation (generates UUID filenames). If writing files manually, use 8-char hex names matching the id field in frontmatter.

9. **execute_code truncates long string content**: When creating cards with full DRBCV content (>2KB), the sandbox strips multi-line strings. Workaround: use `write_file` to write card `.md` files directly to `knowledge/cards/`, then `engine.rebuild_index()`. Card files must use Knowledge OS YAML frontmatter format (id, title, type, tags, relations), NOT raw DRBCV format. Also: YAML parses unquoted `408` as int — quote numeric tags as `'408'` and use `str(t)` in join operations.

10. **adapter.update_knowledge() kwargs unpacking**: The adapter's signature is `update_knowledge(self, card_id, title=None, content=None, tags=None, type_=None, relations=None)`. When calling from an API layer where fields arrive as a dict, unpack explicitly: `adapter.update_knowledge(card_id, title=fields.get("title"), ...)`. Passing the dict as a positional arg silently fails with 400.

11. **build_adapter() CWD-dependent relative paths**: The factory method `build_adapter()` in `adapters/agent/agent_adapter.py` MUST NOT use bare relative paths like `"knowledge/cards"` as defaults — they resolve against CWD, which varies between Terminal (`C:\Users\<user>`), execute_code sandboxes (temp dirs), and the project root. This causes `engine.rebuild_index()` to silently read/write the wrong directory (empty or stale), and `engine.get()` to raise CardNotFoundError for cards that exist on disk. **Fix**: anchor paths to `Path(__file__).resolve().parent.parent.parent` (project root). See `references/rebuild_index_cwd_bug.md` for the full debug trace and two-bug cascade (CWD paths + int-tag crash).

12. **Vite dev server must proxy /api to backend**: The React dev server at :5173 does not automatically forward `/api/*` requests to the FastAPI backend at :8000. Without proxy config, API calls return HTML (the index page) instead of JSON, causing `.map()` crashes in React components. **Fix**: `vite.config.ts` → `server.proxy: { '/api': 'http://127.0.0.1:8000' }`. See `references/frontend-setup-pitfalls.md`.

13. **Dark theme title illegibility**: Default CSS `color` inherits from body (`#c8c8dc`) but `<h1>` and `<h2>` may render with browser-default colors close to dark backgrounds (e.g., `#1a1a2e` on `#0a0a14` is invisible). Always explicitly set `.dashboard h1 { color: #e8e8f8; }` and `.graph-page h2 { color: #e8e8f8; }` in dark-theme projects.
