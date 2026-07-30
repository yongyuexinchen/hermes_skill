# AI 记忆系统选型结论（2026-07-30 调研）

> 场景：用户正在开发 AI 伴侣系统「永月」，需要选型记忆系统。
> 结论：Letta 主引擎 + Memobase 补充。

## 五套方案速查

| 方案 | 结论 | GitHub | 一句话 |
|------|------|--------|--------|
| **Letta** (原 MemGPT) | 🟢 主方案 | 24k ⭐, letta-ai/letta | 唯一原生支持 Agent 人格记忆 + Dreaming 离线巩固 |
| **Memobase** | 🟡 补充 | ~2k ⭐, memodb-io/memobase | 结构化 JSON 用户画像，官网已下线但 GitHub 活跃 |
| **Mem0** | 🟡 备选 | 62k ⭐, mem0ai/mem0 | 生态最大但记忆偏"用户 CRM"，需外层补人格 |
| **Zep** | 🔴 排除 | ~7k ⭐, getzep/zep | 企业治理导向，核心闭源 |
| **LangChain Memory** | 📖 基线 | N/A | 会话级，无跨会话持久化，仅学习用 |

## 为什么 Letta

Letta 的三层记忆架构恰好匹配永月的需求：
- Persona 块 → 永月人设记忆（可随时间演化）
- Human Profile → 关于用户的记忆
- Archival Memory → 全部对话归档
- Dreaming → 用户不在时自动整理记忆、更新自我认知

⚠️ 注意：Letta 最新 SDK 是 TypeScript（@letta-ai/letta-agent-sdk），Python SDK（letta-client）是 V1 旧版。MVP 阶段 Python SDK 够用。

## 学习路径（4 步，约 10 天）

```
Day 1   → LangChain Memory 基线（理解四种模式）
Day 2-6 → Letta 完整试用（Docker部署 → Agent → Persona → Dreaming）
Day 7-9 → Mem0 对比试用（理解"扁平事实"vs"分层记忆"）
Day 10  → Memobase 评估（不稳定则手写 LLM+JSON Schema 替代）
```

完整调研报告：`D:\Contents\learning-plan\memory-systems\RESEARCH.md`
