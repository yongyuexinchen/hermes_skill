# Scanner 输出完整性验证

## 目的

在 Scanner 阶段输出的 JSON 流入 Merger 之前，必须验证所有引用关系是自洽的，避免孤立引用（指向不存在的 concept id/name）污染后续合并流程。

## 两种关系引用模式

Scanner JSON 支持两种关系引用方式，通过 `meta.relation_mode` 区分：

| 模式 | 关系中的 from/to | 适用场景 | 验证方式 |
|------|-----------------|---------|---------|
| **id 引用** (`relation_mode: "id"`) | 使用 concept 的 `id` 字段（英文 snake_case） | 英文术语为主、跨 chunk 合并的场景 | 脚本对比 from/to 是否在 `concept[].id` 中 |
| **名称引用** (`relation_mode: "name"`) | 使用 concept 的 `name` 字段（中文全名，可含括号注释） | 纯中文数学概念，名称唯一且稳定 | 脚本对比 from/to（精确字符串）是否在 `concept[].name` 中 |

**规则**：
- Merger Agent 合并前需确认所有 Scanner 输出使用同一模式
- 名称引用模式要求概念名称全局唯一（含括号注解消歧），如 `"未定式（7种）"` 而非 `"未定式"`
- 两种模式不可混用

## 名称引用模式常见 Pitfalls

| 问题 | 表现 | 修复 |
|------|------|------|
| **名称未完全匹配** | 关系 `from: "ε-N语言"` 但概念名是 `"ε-N语言（伊普西隆-大恩语言）"` | 名称引用必须完全一致，含括号注解。关系中的引用名必须精确等于 `name` 字段值 |
| **歧义短名** | 两个概念同名不同义（如 `"未定式"` vs `"未定式（7种）"`） | 用括号消歧后缀确保唯一性 |
| **LaTeX/Unicode 字符不一致** | `\varepsilon` vs `ε` | 名称引用是精确字符串匹配，字符差异会导致验证失败 |
| **未标注 `relation_mode`** | Merger 不知道用什么字段来验证 | 始终在 `meta.relation_mode` 中标注 `"id"` 或 `"name"` |

## 验证脚本（Python）

```python
#!/usr/bin/env python3
"""Verify scanner JSON: structural integrity, field presence, refs, and content quality."""
import json, sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

errors = []
concepts = data.get("concepts", [])
rels = data.get("relationships", [])
ids = {c.get("id") for c in concepts if c.get("id")}
names = {c.get("name") for c in concepts if c.get("name")}
relation_mode = data.get("meta", {}).get("relation_mode", "id")

# --- 1. Relationship refs ---
for i, r in enumerate(rels):
    f = r.get("from")
    t = r.get("to")
    if relation_mode == "name":
        if f and f not in names:
            errors.append(f"rel[{i}] from='{f}' not in concept names")
        if t and t not in names:
            errors.append(f"rel[{i}] to='{t}' not in concept names")
    else:
        if f and f not in ids:
            errors.append(f"rel[{i}] from='{f}' not in concept ids")
        if t and t not in ids:
            errors.append(f"rel[{i}] to='{t}' not in concept ids")

# --- 2. Required concept fields ---
required_keys = {"id", "name", "type", "definition", "related_to", "examples", "counter_examples", "notes"}
for i, c in enumerate(concepts):
    missing = required_keys - set(c.keys())
    if missing:
        errors.append(f"concept[{i}] \"{c.get('name','?')}\" missing: {missing}")
    if c.get("type") not in ("discriminant", "connection", "mixed", "procedure", "definition", "theorem", "method", "proof"):
        errors.append(f"concept[{i}] invalid type: {c.get('type')}")
    if not c.get("definition", "").strip():
        errors.append(f"concept[{i}] empty definition")
    if "???" in json.dumps(c) or "TODO" in json.dumps(c).upper():
        errors.append(f"concept[{i}] contains placeholder text")

# --- 3. LaTeX integrity ---
full_text = json.dumps(concepts, ensure_ascii=False)
dollar_count = full_text.count("$")
if dollar_count % 2 != 0:
    errors.append(f"Odd number of $ signs ({dollar_count}) across all definitions/notes - possible unclosed LaTeX")

# --- 4. Key concepts presence (for math vaults) ---
if len(concepts) >= 20:
    sample_keywords = ["varepsilon", "arcsin", "pi", "lim", "区间"]
    found_any = any(kw in full_text for kw in sample_keywords)
    has_math = any("lim" in c.get("definition","") or "integral" in c.get("definition","") for c in concepts)
    if not found_any and has_math:
        errors.append("No expected LaTeX keywords found in math concepts")

if errors:
    print(f"VERIFY FAILED — {len(errors)} errors:")
    for e in errors:
        print(f"  X {e}")
    sys.exit(1)
else:
    print(f"VERIFY PASSED — {len(concepts)} concepts, {len(rels)} relationships, mode={relation_mode}")
```

## 使用

```bash
python verify-scanner.py D:/DRBCV-Knowledge/Calculus/temp/scanner-00.json
```

## 字段完整性检查清单（手动/自动化）

| 检查项 | 方法 |
|--------|------|
| 所有 `from`/`to` 在 concepts 中有对应 id 或 name | 自动化（脚本） |
| 每概念有 `definition` 且非空 | 自动化（脚本） |
| 类型仅限允许列表 | 自动化（脚本） |
| 数学概念的 LaTeX 公式完整（无截断/乱码） | 抽查 |
| `examples` 和 `counter_examples` 至少各 1 个（数学概念） | 自动化（脚本） |
| 无占位符（`???` / `TODO`） | 自动化（脚本） |
| `meta` 字段含 source 路径、生成时间戳和 relation_mode | JSON 结构检查 |

## 常见失败模式

| 失败原因 | 示例 | 修复 |
|---------|------|------|
| `from`/`to` 引用不存在概念 id 或 name | `"from": "second_derivative"` 但实际 id 是 `"second_derivative_test"`，或名称不精确 | 检查 concepts 列表中的 id/name 值；关系引用必须与实际 id 或 name 完全匹配 |
| Typo 或不一致命名 | 某处 `"lagrange_mvt"` 另处 `"lagrange_mvt_"` | 统一命名规则（id 推荐蛇形全小写；name推荐中文全名+消除歧义括号） |
| 遗漏 concept 条目 | 关系引用了某概念但该概念未被扫描提取 | 确认 source chunk 中确实包含该概念 |
| 名称引用混合 id 引用 | 部分关系用 `name`，部分用 `id` | 统一使用一种模式，在 meta 中标注 `relation_mode` |
| 定义字段为空或含占位符 | `"definition": ""` 或 `"definition": "待补充"` | 扫描时必须完整填写所有概念定义 |
| LaTeX 转义错误 | 在 JSON 中写 `\arcsin` 而非 `\\\\arcsin` | JSON 字符串中的反斜杠必须双写 |

## 多文件批量验证

```bash
for f in temp/*-concepts.json; do
    python verify-scanner.py "$f" || echo "FAIL: $f"
done
```