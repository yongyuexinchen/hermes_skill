# Maintenance Cron System Pattern

Phase 9.3 — Applied when a knowledge system needs to evolve from passive
query to active self-maintenance.

## Architecture

```
Cron/Manual Trigger
    │
MaintenanceScheduler (5 jobs, no external deps)
    │
MaintenanceAdapter (read-only analysis bridge)
    │
KnowledgeEngine (zero changes to Core)
    │
MarkdownStorage + WhooshSearch
```

## 5 Maintenance Jobs

| Job | Method | Output |
|-----|--------|--------|
| `health_scan` | `adapter.health_scan()` | cards, relations, isolated, empty_content, health_score |
| `quality_review` | `adapter.quality_review()` | A/B/C grades for DRBCV section compliance |
| `relation_review` | `adapter.relation_review()` | dangling refs, self-loops, domain distribution |
| `growth_report` | `adapter.growth_report()` | new_today, updated_today, per-domain counts |
| `evolution_suggestion` | `adapter.evolution_suggestion()` | bridge candidates via BridgeAnalyzer (read-only) |

## Scheduler Pattern

```python
# applications/maintenance/scheduler.py
class MaintenanceScheduler:
    def register(name, job): ...
    def run_all() -> {job_name: result, "report_path": str}: ...

# Factory
def create_scheduler(adapter) -> MaintenanceScheduler:
    s = MaintenanceScheduler(adapter)
    s.register("health_scan", adapter.health_scan)
    s.register("quality_review", adapter.quality_review)
    # ... all 5 jobs
    return s
```

No external scheduler dependency (no APScheduler). Lightweight manual/cron-triggered.

## API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/maintenance/health` | GET | Single health scan |
| `/api/maintenance/report` | GET | Full report (health+quality+relations+growth) |
| `/api/maintenance/run` | POST | Run all 5 jobs, save report to `knowledge/reports/YYYY-MM-DD.md` |

## Report Output

```
knowledge/reports/2026-07-19.md

# Knowledge Health Report — 2026-07-19

## Health Scan
- Cards: 268
- Relations: 1335
- Avg Degree: 5.0
- Health Score: 95/100

## Quality Review
- A: 200, B: 50, C: 18

## Relation Review
- Dangling: 0, Self-loops: 0

## Growth
- Total: 268, New today: 3
```

## Real Results (Phase 9.3)

- 350 tests, 6.08s (17 new maintenance tests)
- API: 3 endpoints
- Report auto-saved to `knowledge/reports/`
- Core: zero modifications
- Maintenance adapter never writes to cards/

## Key Constraint

Maintenance is **observer only**. It never modifies cards, relations, or
markdown files. Any fix must go through: Hermes Agent → human approve →
KnowledgeEngine.relate().
