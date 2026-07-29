# Post-Grok Inspection Workflow

Grok 的 envelope 自报不可信。以下流程基于 Phase 1-3 的实战经验。

## 6 步 Checklist

### 1. 独立 pytest 复跑

```bash
# 用 Hermes 已知可用的 Python（而不是 adapter 用的）
/c/ProgramData/anaconda3/python -m pytest E:/hermes-mini-os/tests/ -q
```

> ⚠️ Hermes venv 的 Python 可能缺 pytest → 用 anaconda3 或其他已知有 pytest 的解释器。

### 2. 方法完整性扫描

```python
# execute_code 扫描关键方法是否存在
c = (BASE / "core/engine/engine.py").read_text()
for m in ["def create", "def get", "def find_related", "def validate_card"]:
    assert m in c, f"MISSING: {m}"
```

### 3. Scope 外文件检查

Grok 可能修改了不该碰的文件。

**实例（Phase 2）**: Grok 修改了 `core/models/card.py`、`pyproject.toml`、`tests/conftest.py` — 虽然改动无害，但超出 `storage/index/` 范围。

### 4. 架构合规

```python
# Core 层不应引入 fastapi / click / sqlite3 / applications / frontend
FORBIDDEN = ["fastapi","click","uvicorn","sqlite3","applications","frontend"]
```

### 5. 任务书对照

逐条对比任务书要求与 Grok 实际产出：

| 任务书要求 | Grok 实际 | 判定 |
|-----------|----------|------|
| `knowledge_engine.py` | `engine.py` | 命名偏差，接受 |
| `CardNotFoundError` 异常 | 无 | 缺失，Hermes 补建 |
| `find_related_cards()` | 无 | 缺失，Hermes 补写 |
| `validate_card()` | 无 | 缺失，Hermes 补写 |
| `get()` 不存在→抛异常 | 返回 `None` | 偏离，Hermes 重写 |

### 6. Hermes 修补 + 测试修复

Hermes 修补 Grok 的缺失后，Grok 写的测试可能因 Hermes 的修改而失败。

**实例（Phase 3）**: Hermes 将 `get()` 从返回 `None` 改为 `raise CardNotFoundError` → Grok 写的 2 个测试预期 `None` 而失败 → 需修改测试。

## 决策矩阵

| 偏离类型 | 决策 | 理由 |
|---------|------|------|
| 类名/文件名不同，功能完整 | 接受 | 重命名影响太多文件 |
| 缺少必需方法（≤20行） | Hermes 直接补写 | 比重委派 Grok 快 |
| 方法签名不同 | Hermes 修补 + 修复受影响的测试 | 同上 |
| 整个模块缺失 | resume Grok | 委派补做 |
| 测试因 Hermes 修补失败 | Hermes 修复测试 | 理解修改后改起来很快 |
| CLI 直接 import Storage | 移到 adapter 层工厂 | 见下方模式 C |

## 常见修复模式

### 模式 C: Application 层绕过 Adapter 直接调 Storage

**症状**: `applications/cli/main.py` 中有 `from storage.markdown import MarkdownStorage`。
**影响**: 打破分层 — Application 绕过 Adapter 直接依赖具体实现。
**修复**:
1. 在 `adapters/agent/agent_adapter.py` 添加 `build_adapter(cards_dir, index_dir)` 工厂函数
2. 工厂内部 `from storage.index import WhooshSearch`（延迟 import，不污染模块顶层）
3. CLI 改为 `from adapters.agent import build_adapter`
4. 测试用 `set_adapter(mock_adapter)` 注入 — 对 shell 命令无侵入
5. `grep "from storage" applications/` 确认零残留

### 模式 D: sed 破坏 Python 文件

**绝对禁止** `sed -i` 批量修改 Python 文件。缩进匹配规则对 .py 不可靠。
正确做法：用 `execute_code` 中的 Python 做精确字符串替换：
```python
content = open(path).read()
content = content.replace("old_pattern", "new_pattern")
open(path, "w").write(content)
```
