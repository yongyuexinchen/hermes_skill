# Codebase-to-Cards: 从代码库分析生成 DRBCV 知识卡片

## 适用场景

当需要从以下来源创建知识卡片时使用本参考：
- 代码库架构分析（如 Grok Build 的 60+ crates Rust workspace）
- 集成方案设计文档的架构概念
- 对话中产生的架构决策和设计知识

## 与标准 DRBCV 流程的区别

标准流程（articles/courses）：
```
源材料 → Scanner扫描 → Merger合并 → Card-Writer生成 → Linker补关系 → Reviewer检查
```

代码库分析流程：
```
代码库 → 勘察结构 → 阅读关键文档 → 架构分析报告 → 提炼核心概念 → 写卡片
```

**关键差异**：
1. 没有"源材料"——概念来自对代码结构和文档的理解，不是提取
2. 卡片作者（Agent）同时也是分析师——没有 Scanner→Merger 多角色分工
3. 卡片之间的关系更强（系统架构天然是"依赖图"）

## 卡片类型选择

| 代码库概念类型 | 对应 DRBCV 类型 | 示例 |
|---|---|---|
| 核心系统/服务 | system | Hermes Architecture, Grok Build Overview |
| 机制/模式 | system | Goal Orchestration, Headless Mode |
| 配置/协议 | concept | Custom Models, Session Management |
| 集成桥接 | system | Hermes-Grok Integration |

## 卡片要素检查清单

每张代码库分析卡必须包含：

- [ ] **类型判定**：一句话说明是 system 还是 concept
- [ ] **是什么**：2-3 句清晰定义，避免术语堆砌
- [ ] **输入-输出空间**：这个系统/概念接受什么、产出什么
- [ ] **正例（≥2 个）**：具体 CLI 命令或使用场景
- [ ] **反例/边界（≥1 个）**：明确"这不是什么"或"不要做什么"
- [ ] **详细解释**：核心机制原理，含伪代码或架构图
- [ ] **细节备注**：子特性表格 + 使用原则
- [ ] **个人见解**：留空，给用户填写
- [ ] **关系**：depends-on + 被指向的双向 Wikilink

## 批量建卡节奏

当一次性需要建 6+ 张关联卡时：
1. 先建"总览"卡（Overview）——定义整个域的边界
2. 再建"机制"卡（Goal Orchestration, Tool Calling 等）——解释内部如何工作
3. 最后建"集成"卡（Integration）——解释外部如何接入

**不要一次全推**——每批 3 张，写完一批让用户确认风格和深度。

## 模板适配

代码库分析卡的 frontmatter 须对齐 vault 卡片格式：
```yaml
---
name: 概念名
type: system | concept        # system=机制/架构, concept=配置/协议
status: core | exploding
source: "[[源文档]]"
domain: hermes | grok-build  # 所属 vault
---
```

domain 字段用于跨 vault 引用——当 Hermes Architecture 卡引用 Grok Build 卡时，Obsidian 图谱能正确显示跨 vault 关系。
