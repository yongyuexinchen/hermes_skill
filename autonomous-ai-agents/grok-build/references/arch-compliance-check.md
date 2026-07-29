# 架构合规检查

每个 Phase 完成后运行（Phase 0 后、每次 Grok task 后、Phase 5 前），确保 Core 和 Storage 层未越界 import。

## 检查清单

1. Core 层：不 import `fastapi` / `click` / `uvicorn` / `sqlite3` / `applications` / `frontend`
2. Storage 层：不 import `applications` / `frontend`
3. Protocol 合规：实现类满足接口契约（如有疑虑，额外检查）
4. 文件完整性：预期文件全部存在，旧文件已清理

## 脚本

```python
"""Architecture compliance check — run after every Grok Phase."""
import re
from pathlib import Path

BASE = Path("E:/hermes-mini-os")  # adjust per project

FORBIDDEN_IN_CORE = ["fastapi", "click", "uvicorn", "sqlite3", "applications", "frontend"]
FORBIDDEN_IN_STORAGE = ["applications", "frontend"]

violations = []

for py_file in BASE.rglob("*.py"):
    if "__pycache__" in str(py_file):
        continue
    rel = str(py_file.relative_to(BASE))
    content = py_file.read_text(encoding="utf-8")
    imports = re.findall(r'^\s*(?:import|from)\s+(\S+)', content, re.MULTILINE)

    if rel.startswith("core"):
        for imp in imports:
            for banned in FORBIDDEN_IN_CORE:
                if imp.startswith(banned):
                    violations.append(f"❌ {rel}: imports forbidden '{imp}'")

    if rel.startswith("storage"):
        for imp in imports:
            for banned in FORBIDDEN_IN_STORAGE:
                if imp.startswith(banned):
                    violations.append(f"❌ {rel}: imports forbidden '{imp}'")

if violations:
    print(f"VIOLATIONS: {len(violations)}")
    for v in violations:
        print(f"  {v}")
else:
    print("✅ ZERO architecture violations")
```

## 典型违规及修复

| 违规 | 修复 |
|------|------|
| `core/engine.py: from fastapi import APIRouter` | 移到 `applications/api/` |
| `storage/markdown.py: from applications.cli import format` | 格式化逻辑应在 Application 层 |
| `core/models.py: import sqlite3` | SQLite 只能出现在 Storage 或 Application 层元数据 |

## 与 Grok 验收的关系

架构合规检查是 Grok 验收流程的第 2 步（在 pytest 全绿之后）。如果 Grok 在实现过程中越界 import，说明 task context 中的约束不够明确——在下一个 Phase 的 task 中明确写出禁止 import 的模块列表。
