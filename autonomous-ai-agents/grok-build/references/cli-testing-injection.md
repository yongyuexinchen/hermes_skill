# CLI Testing with Mock Adapter Injection

Pattern for testing CLI layers in a layered architecture where Application must not import Storage implementations directly.

## Problem

CLI commands call `_get_adapter().engine.method()`. Tests need to mock the engine/adaptor, but the CLI creates its own adapter internally. How to inject mocks without the CLI importing test-only code?

## Solution: Module-level set_adapter() + _get_adapter()

```python
# applications/cli/main.py

_current_adapter: KnowledgeAgentAdapter | None = None

def set_adapter(adapter: KnowledgeAgentAdapter) -> None:
    """注入适配器（测试用）"""
    global _current_adapter
    _current_adapter = adapter

def _get_adapter() -> KnowledgeAgentAdapter:
    """获取适配器：注入的优先，否则构建生产实例"""
    if _current_adapter is not None:
        return _current_adapter
    return build_adapter(DEFAULT_CARDS_DIR, DEFAULT_INDEX_DIR)
```

All commands use `_get_adapter()` (never `build_adapter()` directly).

## Test Fixture

```python
@pytest.fixture
def mock_adapter() -> KnowledgeAgentAdapter:
    adapter = MagicMock(spec=KnowledgeAgentAdapter)
    eng = adapter.engine = MagicMock()
    # Mock engine methods — CLI calls engine.* directly
    eng.get.return_value = mock_card
    eng.create.return_value = mock_card
    eng.delete.return_value = True
    eng.list_all.return_value = [mock_card]
    eng.search.return_value = [mock_card]
    eng.stats.return_value = {"total_cards": 10, ...}
    set_adapter(adapter)
    return adapter

@pytest.fixture
def runner(mock_adapter) -> CliRunner:
    return CliRunner()
```

## Key: Mock `adapter.engine.*`, NOT `adapter.*`

CLI commands typically access `adapter.engine.method()` directly (for non-wrapped engine operations like `get`, `list_all`, `delete`). Mock the engine object, not the adapter's wrapper methods.

## Pitfalls

1. **Duplicate `_get_adapter()` function**: If defined twice, the second overrides the first. The one with `_current_adapter` check must come LAST or there must be only one definition.
2. **Click underscore→hyphen conversion**: `def list_cards` becomes `list-cards` command. Tests must use hyphen form.
3. **`set_adapter` doesn't work**: Check `_current_adapter is not None` — if `_get_adapter()` always calls `build_adapter()`, the global state check is broken.
4. **`sed -i` destroys Python indentation**: Never use sed for Python refactors. Use `execute_code` with Python string replacement.
5. **Don't test exit_code == 0 blindly**: Some CLI commands print errors but don't exit non-zero on ValueError. Check output content for error messages instead.
