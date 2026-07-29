# `kos health` CLI Command

On-demand knowledge base health report, added in Phase ~10.

## Architecture

```
kos health ──► CLI (click) ──► _get_adapter().engine ──► MaintenanceAdapter
                                                              │
                                              ┌───────────────┼───────────────┐
                                              ▼               ▼               ▼
                                        health_scan()   quality_review()  relation_review()
                                        growth_report()
```

`MaintenanceAdapter` (`adapters/maintenance/maintenance_adapter.py`) provides four read-only analysis methods. The CLI is a thin rendering layer — no business logic.

## Usage

```bash
kos health                      # terminal rich output
kos health --output report.md   # write .md file
```

## Output Format (matching `knowledge/reports/YYYY-MM-DD.md`)

```
# Knowledge Health Report — YYYY-MM-DD

## Health Scan
- Cards: N
- Relations: N
- Avg Degree: N.N
- Health Score: N/100

## Quality Review
- A: N / B: N / C: N

## Relation Review
- Dangling: N
- Self-loops: N

## Growth
- Total: N
- New today: N
```

## Test Pattern

```python
# tests/test_cli.py — TestHealth
class TestHealth:
    @pytest.fixture(autouse=True)
    def _setup_mock(self, mock_adapter):
        """Extend mock with cards that have relations, content, created_at."""
        c1 = MagicMock(id="a1b2c3d4", title="TCP", type="discriminant",
                       tags=["network"], content="## 是什么\n...",
                       relations=["depends_on:e5f6g7h8"],
                       created_at="2026-07-19T00:00:00Z")
        c2 = MagicMock(id="e5f6g7h8", title="UDP", ...,
                       relations=["depends_on:e5f6g7h8"])  # self-loop
        mock_adapter.engine.list_all.return_value = [c1, c2]
        mock_adapter.engine.get.side_effect = lambda cid: ...

    def test_health_default(self, runner, mock_adapter):
        result = runner.invoke(cli, ["health"])
        assert result.exit_code == 0
        assert "Health Scan" in result.output
        assert "Dangling" in result.output

    def test_health_output_file(self, runner, mock_adapter, tmp_path):
        outpath = tmp_path / "health.md"
        result = runner.invoke(cli, ["health", "--output", str(outpath)])
        assert outpath.exists()
        content = outpath.read_text(encoding="utf-8")
        assert "Knowledge Health Report" in content
```

## Dry-run note

The CLI delegates to `MaintenanceAdapter` which is read-only — no cards are ever modified. The `--output` flag uses `save_report()` which writes to `knowledge/reports/{today}.md` then copies to the user-specified path.
