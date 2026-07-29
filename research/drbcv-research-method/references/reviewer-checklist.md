# Reviewer 硬规则检查清单

## 目的

在 LLM Reviewer 做语义抽查之前，先运行自动化脚本做字符串级硬规则检查。这是 V0.5 的核心改进——**预防 2026-07-17 事故重演**（83 张卡含「待补充」占位符但 Reviewer 虚报通过）。

## 脚本位置

```
scripts/reviewer_check.py
```

## 使用方法

```bash
# 基本用法（数学 vault）
python scripts/reviewer_check.py D:/DRBCV-Knowledge/Calculus/Concepts

# 通用 vault（不检查数学专属 section）
python scripts/reviewer_check.py D:/DRBCV-Knowledge/SillyTavern/Concepts --vault-type general

# 保存 JSON 报告
python scripts/reviewer_check.py D:/DRBCV-Knowledge/Calculus/Concepts --report temp/review-report.json
```

## 检查项

### 1. 占位符扫描（★ 最关键）

搜索以下所有模式：

| 模式 | 说明 |
|------|------|
| `待补充` | 最常见的模板占位符 |
| `待爆破` | 另一种占位符变体 |
| `TODO` | 通用 TODO 标记 |
| `???` | 通用占位符 |
| `（待补充...）` | 含括号的变体，如 `（待补充具体例子）` |
| `（待爆破...）` | 含括号的变体 |
| `(待补充...)` | 半角括号变体 |
| `(待爆破...)` | 半角括号变体 |

**发现任何占位符 → 该卡直接 FAIL，打回 Card-Writer 修复。**

### 2. LLM 思考过程泄露

搜索子 Agent 可能写入卡片的内部思考文本：

| 模式 | 说明 |
|------|------|
| `Wait,` / `Actually,` / `Let me` / `Hmm,` | LLM 推理过程开头 |
| `I should` / `looking at` / `recheck` / `double-check` | LLM 自言自语 |
| `tool_calls` / `invoke name` / `parameter name` | Agent 框架泄露 |
| `<thinking>` / `end.*thinking` | 思维链标签泄露 |
| `I'll now/first/start` / `Let's look/check/read/start` | LLM 行动描述 |
| `First, I` | LLM 步骤描述 |

**发现任何泄露 → 该卡 FAIL，打回 Card-Writer 清理。**

### 3. Frontmatter 完整性

检查以下字段存在且非空：

| 格式 | 必需字段 |
|------|---------|
| 新格式 | `name`, `type`, `status` |
| 旧格式 (concept-card) | `title` |

### 4. Wikilink 存在

每张卡至少 1 个 `[[wikilink]]`（排除命名空间标签如 `[[Calculus]]`）。

### 5. 数学 vault 专属检查

仅当 `--vault-type math` 时执行：

| 检查项 | 合格标准 |
|--------|---------|
| 推导过程 section | `## 推导过程` 或 `## 详细解释` 存在 |
| 经典例题 section | `## 经典例题` 或 `## 正例` 存在 |
| 类比 section | `## 类比` 存在 |
| 关系 section | `## 关系` 存在 |
| 例题数量 | ≥ 2 题 |

### 6. LaTeX 平衡性（Warning 级别）

检查 `$` 符号数量为偶数（非阻断性警告）。

## 输出格式

```
============================================================
DRBCV Reviewer Check Report
Directory: D:/DRBCV-Knowledge/Calculus/Concepts
Vault type: math
Total cards: 112
Passed: 110
Failed: 2
Total errors: 5
============================================================

FAILED CARDS:

  [黎曼和.md]
    X PLACEHOLDERS FOUND (12): ['待补充', '待补充', '待补充', '待补充', '待补充']
    X math card missing section: derivation

  [倒代换.md]
    X PLACEHOLDERS FOUND (12): ['待补充', '待补充', '待补充', '待补充', '待补充']
    X LLM LEAKAGE (2): ['Let me', 'Actually,']

REVIEW FAILED — 2 cards need repair.
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 所有卡片通过硬规则检查 |
| 1 | 有卡片未通过，需修复 |

## 与 Reviewer Agent 的关系

```
Card-Writer 完成
  ↓
Linker 完成
  ↓
reviewer_check.py (硬规则脚本)  ← 本脚本
  ↓ Pass
Reviewer Agent (LLM 语义抽查)
  ↓ Pass
✅ 验收完成
```

**硬规则检查是 Gate**：不通过则 Reviewer Agent 不启动，直接打回 Card-Writer。

## 在 Kanban 中的位置

Reviewer Agent 的 Kanban 任务 body 中应包含：

```
1. 先运行: python scripts/reviewer_check.py <concepts_dir>
2. 如果硬规则检查失败 → 打回 Card-Writer，Reviewer 任务保持 in_progress
3. 如果硬规则检查通过 → 进行语义抽查（随机抽 3-5 张卡）
4. 语义抽查通过 → 标记 Reviewer 为 done
5. 语义抽查不通过 → 打回 Card-Writer 重写
```

**禁止**：在硬规则检查未运行或未通过时标记 Reviewer 为 done。
