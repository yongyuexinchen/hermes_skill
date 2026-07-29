# 分层架构强制模式

在 Hermes-Grok 协作项目中，架构边界由代码强制执行（不是靠文档或约定）。

## 三层结构

```
Application Layer → Adapter → Core Layer ← Storage Layer
     ↑                          ↑              ↑
   CLI + Web          只依赖 Provider 接口    实现接口
```

## 强制机制

| 层 | 机制 | 检查 |
|----|------|------|
| Core | `core/__init__.py` 顶部注释列出禁止 import 的模块 | `grep "from (fastapi\|click\|sqlite3)" core/` |
| Storage | `storage/__init__.py` 禁止 import applications | `grep "from applications" storage/` |
| Application | 通过 `adapters/agent/build_adapter()` 工厂获取引擎，不直接 `import storage.*` | `grep "from storage" applications/` |
| Adapter | 唯一的 wiring 层，工厂函数做延迟 import 具体实现 | — |

## 依赖注入契约

```python
# Core 只依赖接口
class KnowledgeEngine:
    def __init__(self, storage: StorageProvider, search: SearchProvider):
        ...

# Adapter 工厂做 wiring（延迟 import 防污染）
def build_adapter(cards_dir, index_dir):
    from storage.index import WhooshSearch       # 不在顶层 import
    from storage.markdown import MarkdownStorage  # 只在工厂内 visible
    engine = KnowledgeEngine(MarkdownStorage(cards_dir), WhooshSearch(index_dir))
    return KnowledgeAgentAdapter(engine)
```

## 测试注入

Application 层提供 `set_adapter(mock)` 函数供测试注入 mock engine：
```python
# tests/test_cli.py
@pytest.fixture
def runner(adapter):
    set_adapter(adapter)  # 注入 mock，不启动真实 storage
    return CliRunner()
```

## 架构合规检查脚本

每次 Grok Phase 后用 `execute_code` 跑：
- Core 层无 Web/CLI/DB import
- Storage 层无 Application import
- Application 层无直接 Storage import
- Protocol 接口完整性
