# 多 Vault 结构

## 设计动机

用户明确要求每个领域独立隔离——打开酒馆 vault 时看不到 Hermes 卡片，反之亦然。同时保留"需要时合并"的能力。

## 目录布局

```
D:\DRBCV-Knowledge\
├── SillyTavern/       ← 独立 Obsidian vault
│   ├── Concepts/      （角色卡、世界书、Temperature…）
│   ├── Systems/
│   ├── Sources/
│   ├── Articles/
│   ├── Maps/
│   ├── Templates/
│   └── .obsidian/     ← 此 vault 专属的 Obsidian 配置
│
├── Hermes/            ← 独立 Obsidian vault
│   ├── Concepts/      （OpenAI 兼容 API、Provider、Kanban…）
│   ├── Systems/
│   ├── Sources/
│   ├── Articles/
│   ├── Maps/
│   ├── Templates/
│   └── .obsidian/
│
├── Calculus/          ← 独立 Obsidian vault（微积分 — 高数上/下）
│   ├── Concepts/      （导数定义、中值定理、泰勒公式…）
│   ├── Systems/
│   ├── Sources/
│   ├── Articles/      （B 站视频转录 / 教材原文）
│   ├── Maps/
│   ├── Templates/
│   └── .obsidian/
│
└── （未来更多：MacroEconomics/ 等）
```

## 使用方式

| 操作 | Obsidian 打开 | 可见范围 |
|------|-------------|---------|
| 专注酒馆 | `D:\DRBCV-Knowledge\SillyTavern\` | 只看到酒馆卡片 |
| 专注 Hermes | `D:\DRBCV-Knowledge\Hermes\` | 只看到 Hermes 卡片 |
| 专注微积分 | `D:\DRBCV-Knowledge\Calculus\` | 只看到微积分卡片 |
| 全局视图 | `D:\DRBCV-Knowledge\` | 所有领域卡片 + 跨领域 wikilink |

## 跨 Vault Wikilink

当两个领域有重叠概念时（如 `[[上下文窗口]]` 在酒馆和 Hermes 都相关），在卡片 frontmatter 中用 `cross_ref` 标记：

```yaml
---
name: Context Window（上下文窗口）
cross_ref: "[[上下文窗口]]"  # 酒馆 vault 已有的同名卡
---
```

Obsidian 打开父目录 `DRBCV-Knowledge\` 时会自动解析跨 vault 的 wikilink，图谱中会连线。

## 新建 Vault 清单

1. `mkdir -p D:\DRBCV-Knowledge\<新领域>\{Concepts,Systems,Sources,Articles,Maps,Templates,.obsidian}`
2. 复制 `Templates/名词卡片模板.md` 到新 vault
3. 复制 `.obsidian/` 基础配置（app.json, appearance.json, core-plugins.json）
4. 开始爆破名词