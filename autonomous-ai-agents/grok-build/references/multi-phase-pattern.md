# Multi-Phase Project Delegation Pattern

Proven in Hermes Mini Knowledge OS (199 tests, 5 phases, Grok Build as executor).

## Pattern

```
Phase -1: Hermes — ADR + architecture + contract interfaces
Phase  0: Grok  — Scaffold (or Hermes does trivial dir creation)
Phase  N: Grok  — Implement one layer at a time, bottom-up
          Hermes — Verify (pytest + architecture check), fix edge cases
```

## Phase Order (bottom-up)

```
Storage → Search → Engine → Adapter → CLI/Tools → Experiments
```

Each layer only depends on the one below. Grok implements; Hermes verifies that:
1. `pytest` all green
2. Architecture redlines intact (no cross-layer imports)
3. Contracts satisfied (Protocol compliance)

## Grok Task Template

```json
{
  "task": "Phase N: 具体目标。创建文件X实现接口Y。完成后pytest全绿。",
  "context": "Python 3.11, 依赖列表, 已有代码约定",
  "constraints": "只修改X目录; 禁止import Y; 禁用外部API",
  "workspace": "E:/path"
}
```

## When Grok Gets It Wrong

Common patterns and fixes:
- **Wrong file name** → accept if functionality correct (e.g., `engine.py` vs `knowledge_engine.py`)
- **Misses methods** (e.g., forgot `find_related`, `validate`) → Hermes patches directly
- **Imports prohibited modules** → add factory function in adapter layer, have Grok code import factory instead
- **Returns None instead of raising** → fix return type + add exception class
- **Creates throwaway test artifacts** → clean up before next phase

## Key Anti-Patterns

- ❌ Don't delegate trivial scaffolding (mkdir + touch) to Grok — 60s overhead for 2s work
- ❌ Don't let Grok modify files outside the specified scope — verify with `git diff`
- ❌ Don't use Grok for architecture decisions — that's Hermes' job (ADR)
