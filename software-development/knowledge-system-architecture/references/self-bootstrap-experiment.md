# Agent Self-Bootstrap Experiment Pattern

Proving that an Agent can autonomously discover knowledge gaps,
fill them, and establish relations — forming a closed maintenance loop.

## Pattern

```
Phase 1: SEARCH existing knowledge
    ↓
Phase 2: ANALYZE gaps (found vs missing)
    ↓
Phase 3: CREATE missing cards via Tool Server
    ↓
Phase 4: RELATE new cards to existing ones
    ↓
Phase 5: VALIDATE everything
    ↓
Phase 6: REPORT findings
```

## Key Metrics to Capture

- Cards found vs missing (gap analysis)
- New cards created
- Relations established
- Validation pass rate
- Knowledge graph growth (nodes + edges)

## Implementation Checklist

- [ ] Agent uses only Tool Server (never touches files directly)
- [ ] All creates go through adapter → engine → storage
- [ ] Relations use `resolve_relation()` (not hardcoded IDs)
- [ ] `validate_knowledge()` run on every new card
- [ ] `repair_relations()` run after bulk creates
- [ ] Report written to `experiments/` directory

## Real Example (Phase 4.8)

Input: Computer-Network knowledge base (6 existing cards)
Process:
  1. search("TCP","UDP","IP","HTTP","DNS","ARP") → all found ✅
  2. search("congestion","sliding window","socket","routing","OSI") → all missing ❌
  3. create_knowledge × 5 (TCP拥塞控制, OSI七层, TCP滑动窗口, Socket, 路由算法)
  4. relate × 5 (extends:TCP, uses:UDP, framework_for:IP, ...)
  5. validate × 5 → all passed ✅
Result: 6 → 11 network cards, 12 new edges, knowledge graph expanded 83%
