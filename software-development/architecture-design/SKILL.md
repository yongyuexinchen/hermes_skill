---
name: architecture-design
description: System architecture design with ADR, interface contracts, and three-layer pattern. Use when designing new systems, resolving architecture drift, or making structural decisions before implementation.
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [architecture, design, adr, system-design, planning, interfaces]
---

# Architecture Design

Use this skill when:
- Designing a new system from scratch
- Resolving architecture drift between two competing directions
- The user asks for "architecture", "system design", "模块架构", "分层设计"
- Before any `plan` skill or Grok Build delegation — architecture comes first

## Core Workflow

```
Phase -1: ADR + Interfaces (Hermes does this, no delegation)
    ↓
Phase 0:  Scaffolding (delegate to Grok Build if meaningful)
    ↓
Phase 1+: Core implementation (delegate to Grok Build)
```

### Phase -1: Architecture Decision Records + Interface Contracts

**This is the architect's core deliverable — NOT code.** Do this before any implementation.

1. **ADR documents** in `docs/ADR/` — record WHY, not just WHAT
2. **Interface contracts** (Protocol classes) — define boundaries Grok cannot cross
3. **architecture.md** — living document, updated when decisions change

### ADR Format

Every ADR follows this structure:

```markdown
# ADR-NNN: [Decision Title]

| 属性 | 值 |
|------|-----|
| **状态** | ✅ 已采纳 / ⏳ 提议中 / ❌ 已废弃 |
| **日期** | YYYY-MM-DD |
| **决策者** | [Who made this] |
| **前置 ADR** | [References to prior ADRs this depends on] |
| **影响范围** | [Which modules/layers are affected] |

---

## 背景
[What is the problem? What are the alternatives?]

## 决策
[What did we choose? Be explicit.]

## 理由
[Why this choice? 3-5 concrete reasons.]

## 代价
[What are we giving up? Mitigation strategies.]

## 替代方案及否决理由
[What else did we consider and why did we reject it?]

## 影响
[What changes in the codebase?]
```

### Interface-First Design

Define contracts before implementation. This is what separates architect from code-writer:

```python
# Hermes defines THIS (the contract)
class StorageProvider(Protocol):
    def save(self, entry: Entry) -> None: ...
    def load(self, entry_id: str) -> Entry | None: ...
    def list_all(self) -> list[Entry]: ...
    def delete(self, entry_id: str) -> bool: ...

# Grok implements THIS (the concrete class)
class MarkdownStorage:  # implements StorageProvider
    ...
```

The contract:
- Forces Grok to stay within boundaries
- Enables mock testing (no real filesystem needed)
- Makes backend replacement zero-cost

### Three-Layer Architecture

When system has both core logic and multiple interfaces (CLI + Web), use this pattern:

```
Application Layer  ← CLI, Web API, frontend (replaceable)
        │
   [Engine API only — no direct storage access]
        │
Core Layer         ← Business logic, CRUD orchestration
        │            NO web dependencies, NO database dependencies
   [Provider interfaces]
        │
Storage Layer      ← Markdown files, search index, metadata DB
```

**Red lines (never cross):**
- Core Layer never imports FastAPI / Flask / HTTP
- Core Layer never imports sqlite3 / SQLAlchemy for knowledge storage
- Application Layer never reads/writes knowledge files directly
- Knowledge entries NEVER stored in SQLite (only application metadata)

### Resolving Architecture Drift

When two designs emerge (e.g., CLI-first vs Web-first), DON'T pick one and discard the other:

1. Identify the relationship: are they alternatives, layers, or overlapping?
2. Default to **layering** — most "competing" designs are actually different layers
3. Write an ADR documenting the resolution
4. Update architecture.md to reflect the unified structure

## Deliverables Checklist

Before entering implementation phase:

- [ ] `docs/ADR/` with at minimum: storage choice, search strategy, interface strategy
- [ ] `architecture.md` with: system goals, module architecture diagram, data flow, API design, directory structure, development phases
- [ ] Interface contracts: Protocol classes for all cross-layer boundaries
- [ ] Three-layer clarity: what goes in each layer, what never crosses boundaries

## Pitfalls

1. **Skipping ADR** — "it's a small project, we don't need docs." Wrong. ADR is how you prove you made conscious tradeoffs, not just coded the first thing that came to mind.
2. **Writing ADR after implementation** — ADR records the decision process. If the code is already written, it's not a decision record, it's a post-hoc rationalization.
3. **Merging Core and App layers** — "it's simpler to just put the API in the engine." It is simpler today; it's architecture debt tomorrow. The boundary pays off the first time you add a second interface.
4. **Letting Grok design architecture** — Grok implements, Hermes designs. Never delegate architecture decisions to the execution agent.

## References

- `references/adr-template.md` — blank ADR template for new decisions
