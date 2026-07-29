# Full Vault Health Audit Pattern (Phase 8.6)

## Audit Dimensions

| Part | What | Key Metric |
|------|------|------------|
| Size | Cards/domain, relations | avg degree |
| DRBCV Quality | Random 25% sample per domain | section completeness |
| Graph Health | Isolated nodes, broken edges, in-degree | top-cited concepts |
| Coverage | Keyword coverage per domain | found/total |
| Dependency Chains | Longest prerequisite chain depth | max chain length |
| Asset Rating | S/A/B/C/D per domain | DRBCV score + avg degree |
| Agent Readiness | Can Agent autonomously diagnose gaps? | 0-100 score |

## Graph Shape Classification

| Degree | Shape | Character |
|--------|-------|-----------|
| >3.0 | **Mesh (★)** | High-density knowledge web — concepts heavily interlinked |
| 1.5-3.0 | **Chain (-)** | Moderate — concepts flow in prerequisite order |
| <1.5 | **Sparse (·)** | Isolated or loosely connected |

Real Phase 8.6 results: Calculus 8.0 (mesh), Computer-Network 3.2 (mesh),
Hermes 3.8 (mesh), SillyTavern 2.3 (chain).

## Cross-Domain Edges

The key indicator of "second brain" maturity. A knowledge system with 5 domains
but 0 cross-domain edges is a collection of silos, not an integrated brain.

Cross-domain targets:
- Calculus → Computer-Network (optimization → routing algorithms)
- Hermes → SillyTavern (Skill system → Prompt engineering)
- Computer-Network → Hermes (distributed systems → agent architecture)

## Agent Readiness Scoring

| Capability | Weight |
|------------|--------|
| Can find existing concepts by name | 20 |
| Can trace dependency chains | 20 |
| Has cross-domain bridges | 20 |
| Can navigate graph by relations | 20 |
| Has deep enough chains (≥3 layers) | 20 |

Phase 8.6 result: 80/100 (missing cross-domain bridges).

## Five-Tier Asset Rating

| Rating | Criteria |
|--------|----------|
| **S** | DRBCV ≥80%, avg degree ≥1.5, 0 isolated, Agent can maintain |
| **A** | DRBCV ≥70%, avg degree ≥1.0, minimal isolation |
| **B** | Rich content, relations insufficient |
| **C** | Note collection, no graph structure |
| **D** | Fragments |

## Audit Execution Pattern

```python
# Scan vault (read-only, 300ms for 418 files)
result = scan_vault("D:/DRBCV-Knowledge")

# Build graph
for card in result["cards"]:
    for rel in card["relations"]:  # "type:target_id"
        graph[card["id"]].append(target_id)
        # Count cross-domain edges
        if target["_domain"] != card["_domain"]:
            cross_domain += 1

# Rate domains
for domain, cards in by_domain.items():
    score = domain_scores[domain]
    avg_degree = sum(len(c["relations"]) for c in cards) / len(cards)
    isolated = sum(1 for c in cards if not c["relations"])
    
    if score >= 80 and avg_degree >= 1.5 and isolated == 0:
        rating = "S"
```

## Pitfall: DFS Chain Detection Timeout

Recursive DFS with `visited.copy()` on 268 cards causes exponential blowup.
Use iterative bounded search (max depth 20) instead:

```python
# ITERATIVE (safe)
depth, current, visited = 0, card["id"], {card["id"]}
while depth < 20:
    card = id_to_card.get(current)
    if not card: break
    for rel in card.get("relations", []):
        if rel_type in ("depends_on","extends","prerequisite"):
            if target not in visited:
                current = target; visited.add(target); depth += 1; break
    else: break  # no matching relation found
```
