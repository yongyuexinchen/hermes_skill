# Knowledge Curator Skill Pattern

Four operations for knowledge quality analysis — read-only, never modifies cards.

## Operations

### 1. scan — coverage analysis
```
Input:  { domain, concepts[] }
Output: { coverage_rate, covered[], partial[], missing[] }
```
Searches knowledge-os for each concept. Classifies as:
- **covered**: exact title match
- **partial**: related cards exist but no exact match
- **missing**: no results

### 2. review — quality audit
```
Input:  { domain? }
Output: { quality_score, isolated_cards[], broken_relations[], weak_cards[] }
```
Checks: DRBCV section completeness (是什么/正例/反例/详细解释/关系), isolation, broken relations, content length ≥ 200 chars.

### 3. plan — task generation
```
Input:  { domain, gap_report }
Output: { batches: [{priority: P0|P1|P2, tasks: ≤5}] }
```
Priority: P0 (missing fundamentals) > P1 (missing connections) > P2 (extensions).
Max 5 tasks per batch.

### 4. explain — dependency graph
```
Input:  { concept }
Output: { concept, prerequisite[], role, importance, why }
```
Helps Hermes decide: "which missing concept should I fill first?"

## Integration

Curator calls knowledge-os for reads (search, validate), but NEVER:
- Calls create/update/delete
- Modifies markdown files
- Generates card content

## Real Audit Example (Phase 8.2)

Computer Network audit on 81-card DRBCV vault:
- 50 standard concepts across 5 OSI layers
- Coverage: 72% (36 covered, 14 partial, 0 missing)
- Best: Transport layer 100%, weakest: Data Link 45%
- Found: TLS/HTTPS/IPv6/HDLC as partial → created in Phase 8.3
