## Cross-Domain Bridge Generator Pattern

Phase 9.2 — Rule-based discovery of cross-domain knowledge connections
with human-in-the-loop acceptance.

### Problem

A knowledge vault with 268 cards across 5 domains (Calculus, Computer-Network,
Hermes, SillyTavern, Grok-Build) has **zero cross-domain edges**. Each domain
is a high-quality silo — an island with no bridges. The system knows about TCP
congestion control AND gradient descent, but doesn't know they share the same
feedback-control structure.

This is the difference between a knowledge base and a second brain.

### Architecture

```
Hermes Agent
    │ request bridge analysis
    ▼
BridgeGenerator (core/bridge/)
    │ candidate proposals
    ▼
Human Review (accept/reject)
    │ accepted
    ▼
KnowledgeEngine.relate()
```

**Red Line**: Bridge Generator NEVER modifies cards directly. All bridges
require explicit human accept before writing relations.

### Component Layout

```
core/bridge/
├── models.py      — BridgeProposal dataclass + BridgeStatus enum + BridgeType enum
├── analyzer.py    — Rule-based discovery (3 rules, no embedding/vector DB)
└── scorer.py      — Weighted confidence: 0.4×tag + 0.3×keyword + 0.3×structure

adapters/bridge/
└── bridge_adapter.py — analyze_domains / pending / accept / reject

applications/api/routes/
└── bridges.py    — POST /analyze, GET /pending, POST /accept, POST /reject
```

### BridgeProposal Model

```python
@dataclass
class BridgeProposal:
    source_card_id: str
    target_card_id: str
    source_title: str
    target_title: str
    source_domain: str
    target_domain: str
    bridge_type: BridgeType   # analogy | application | foundation | extends | contrasts
    explanation: str          # human-readable justification
    confidence: float         # 0.0-1.0 composite score
    evidence: list[str]       # shared keywords/tags
    status: BridgeStatus      # pending | accepted | rejected
```

### Five Bridge Types

| Type | Meaning | Example |
|------|---------|---------|
| analogy | Structural isomorphism | TCP拥塞控制 ↔ 梯度下降 (both feedback loops) |
| application | Theory → application | 微积分 → 梯度下降 |
| foundation | Foundation → upper layer | 线性代数 → 机器学习 |
| extends | Extension | HTTP → HTTPS |
| contrasts | Cross-domain contrast | TCP vs UDP (but across domains) |

### Three Discovery Rules

1. **Tag crossover**: Two domains share a non-domain tag (e.g. "optimization",
   "control") → candidate bridge.
2. **Keyword overlap**: Tokenized content shares conceptual vocabulary
   (e.g. "feedback", "adjust", "error", "window").
3. **Structure similarity**: Two cards have isomorphic relation patterns
   (same count, similar relation type distribution).

No embedding models. No vector databases. Pure rules for explainability
and zero new dependencies.

### Scoring Formula

```
confidence = 0.4 × tag_similarity + 0.3 × keyword_overlap + 0.3 × structure_similarity
```

Confidence threshold: 0.15 (production), 0.0 (testing).

### API Endpoints

```
POST /api/bridges/analyze  {domains: ["calculus","computer-network"]}
  → {count: N, bridges: [...]}

GET  /api/bridges/pending
  → {count: N, bridges: [pending proposals]}

POST /api/bridges/{id}/accept
  → applies Engine.resolve_relation(), changes status to "accepted"

POST /api/bridges/{id}/reject
  → changes status to "rejected", removes from pending view
```

### Frontend Integration

GraphPage.tsx adds:
- "Analyze Bridges" button → calls POST /analyze
- Bridge card UI: source ↔ target, type badge, confidence %, explanation
- Accept/Reject buttons per proposal

### Real-World Performance

On 4 Computer-Network + 18 Calculus cards (22 total), discovered 72 candidate
bridges. Most confidence is low (~0.30-0.40) due to thin test data without
shared domain-agnostic tags. Quality scales with content richness.

### Architecture Enforcement

`core/bridge/` must NOT import: fastapi, applications, react
It may import: core.models, core.engine, stdlib
