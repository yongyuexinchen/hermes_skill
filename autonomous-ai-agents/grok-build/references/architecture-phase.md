# Hermes-Grok 协作：Phase -1 架构先行 + Phase 0..N 委派模式

## 完整流程

```
Phase -1 (Hermes, 不派 Grok — 架构师的核心交付)
├── 1. 分析需求，设计模块层次
├── 2. 记录 ADR（每项非平凡决策一张）
├── 3. 定义 Provider 接口（Python Protocol — 这就是契约）
├── 4. 输出 architecture.md（单源真理）
└── 5. 用户确认 → 进入 Phase 0

Phase 0 (Hermes 直接执行 — Pitfall #11)
└── mkdir + touch + 空文件。绝不派 Grok 做脚手架。

Phase 1..N (Grok Build — 每个 Phase 一个独立 task)
└── 严格按接口实现。完成后 Hermes 逐项核验。
```

## 为什么 Phase -1 不可跳过

| 跳过 Phase -1 | 有 Phase -1 |
|--------------|------------|
| Grok 自行决定类名、目录结构 | 接口约束类名、方法签名 |
| 无架构文档，无法验收 | architecture.md 是验收基准 |
| Implementation 与 Application 紧耦合 | Provider 接口解耦，测试用内存 mock |
| 换人看不懂设计意图 | ADR 记录了 "为什么" |

## Grok Task 模板（Phase 1..N）

```json
{
  "task": "Phase N: 目标描述 + 可核验验收标准 + '完成后≤200字总结'",
  "context": "已有代码结构、类名、导入路径、要实现的 Provider 接口定义",
  "constraints": "禁止修改的目录 / 禁止 import 的模块 / 硬性限制",
  "workspace": "E:/absolute/path"
}
```

接口定义必须写入 `context` — 接口就是约束，Grok 只能在约束内实现。

## Grok 验收流程

完成后 Hermes 逐项核验（顺序不能乱）：

1. **pytest 全绿** — 最基本门槛
2. **架构合规检查** — Core 层未越界 import（见 `arch-compliance-check.md`）
3. **Protocol 合规** — 实现类满足接口契约

### 命名偏离处理（Pitfall #12）

Grok 经常忽略任务书中的精确类名/字段名。验收矩阵：

| Grok 偏离 | 判定 | 动作 |
|-----------|------|------|
| 类名不同但 Protocol 合规 | ✅ 接受 | 命名是风格问题，不值得改所有引用 |
| 缺少必需字段 | ❌ 拒绝 | resume 修复，这是功能缺陷 |
| type 枚举值与用户指定不同 | ⚠️ 修正 | 用户指定了 → 必须改 |
| type 枚举值 Grok 自创但未被指定 | ✅ 接受 | 逻辑正确即可 |
| 多余字段（如 pinned）| ❌ 修正 | 多余字段会污染序列化格式 |

**底线：Protocol 合规 + 测试全绿 > 命名匹配。**

## 架构漂移处理

当脚手架/用户指令与 architecture.md 冲突时，创建 ADR 解决：

```
脚手架说: FastAPI + SQLite  vs  architecture.md: CLI + Markdown
                     │
              ADR-004 分层 ✅
                     │
    Application Layer (CLI + Web, 可替换)
           │
    Core Layer (Engine, 稳定)
           │
    Storage Layer (Markdown, 真理来源)
```

分层规则：
- Core 不依赖任何 Application（无 fastapi/click import）
- 知识资产在 Markdown 文件中（不在 SQLite）
- SQLite 仅用于应用元数据
