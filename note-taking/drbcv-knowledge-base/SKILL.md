---
name: drbcv-knowledge-base
description: "Use when batch-building DRBCV knowledge vaults from structured course materials (docx transcripts, textbooks). Covers the full pipeline: docx→md conversion, Grok Build batch card generation with chain-loaded domain rules, Obsidian graph configuration. For single-card creation use Hermes native write_file; for batch (10+ sources) use this workflow."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [DRBCV, knowledge-base, Grok-Build, batch-cards, Obsidian]
    related_skills: [git-github-windows-china]
---

# DRBCV 知识库批量构建

从讲课转录稿（docx）到 Obsidian 知识图谱的完整自动化管线。

## When to Use

- 批量建知识库：10+ 篇 docx 讲课稿/教材章节（需要 docx→md 转换）
- 需要 DRBCV 格式（frontmatter + 类型判定 + 正反例 + 生活类比 + 关系图）
- 目标学科有明确的章节结构

**不要用于**：
- 单张卡片（Hermes write_file 更快）
- 5–10 张卡、源文件已是干净 .md → 用 Hermes write_file 并行写卡（见 `references/hermes-native-mid-batch.md`）
- 无结构化原文、纯文本问答

## 完整流程

### 阶段 1：原文转换
```bash
python -c "
from docx import Document
# 批量转换 desktop-attachments/*.docx → Sources/*.md
# 清理文件名：去掉 _原文、 (1) 后缀
"
```
- 使用 Anaconda Python（`/c/ProgramData/anaconda3/python`），Hermes venv 的 Python 可能缺 python-docx
- 转换后清理混入的其他课程文件（按文件名正则过滤）

### 阶段 2：Vault 初始化

**基础路径**：`D:/Contents/`（Obsidian vault 根 + git 仓库根）

**目录结构**：
```
D:/Contents/                         ← git 仓库根 + Obsidian vault 根
├── .gitignore                       ← 排除 .sync/, research/*/repos/, **/.git/
├── .obsidian/                       ← vault 全局配置
├── DRBCV-Knowledge/                 ← 知识卡片（22 个领域）
│   ├── <Domain>/Concepts/           ← DRBCV 卡片 (.md)
│   ├── <Domain>/Sources/            ← 原始材料
│   └── <Domain>/Templates/          ← 领域卡片模板
├── research/                        ← 调研分析（REPORT + 卡片）
│   └── <YYYY-MM-DD_主题>/
├── process_research/                ← 处理中的调研
├── Contents/                        ← Obsidian 白板文件 (.canvas)
└── README.md
```

> **约定**：`D:/Contents/` 是整个 Obsidian vault 的根，git 仓库也在这个层级。`DRBCV-Knowledge/` 是卡片库，`research/` 是调研记录，`process_research/` 是进行中的调研。**不要在里面加 `content/` 子目录**——用户已明确拒绝这层额外收纳，仓库根就是 vault 根。Obsidian wikilink 按文件名匹配，不受子目录层级影响。

graph.json 模板：
```json
{
  "search": "-path:Sources -path:Templates -path:TASK -path:temp -path:media -path:Articles -path:Systems",
  "hideUnresolved": true,
  "collapse-filter": true
}
```

### 阶段 3：任务拆分

每批 **5-8 篇原文**（多了 Grok max_turns 触顶，少了浪费系统提示词）。按章节分组：

```
TASK-01-验证批.md   ← 先跑 5 篇验证
TASK-02-Ch1.md      ← 后续每批 6-8 篇
TASK-03-Ch2.md
...
```

TASK 文件格式：
```markdown
# 知识库建卡任务

## 建卡原则
严格遵循已有卡格式（frontmatter + 类型判定 + 是什么 + 正例 + 反例 + 详细解释 + 生活类比 + 个人见解留空 + 关系）。
区分 discriminant/connection/mixed。判别型=回答"是什么"，连接型=回答"会怎样/如何运作/如何计算"。每卡至少1个生活类比。

## 源文件（Sources/下）
- 001 xxx.md
- 002 xxx.md
...

## 关键概念提示
- 概念A → discriminant/connection（原因）
- 概念B → connection（含公式/算法）
```

### 阶段 4：Grok 批量建卡

```bash
cd "D:/Contents/DRBCV-Knowledge/<Vault-Name>"
grok -m deepseek-v4 -p "$(cat TASK-01-验证批.md)" --yolo --output-format json --max-turns 35
```

- **链式加载领域规则**：数学 vault 在 prompt 前拼接规范文件
  ```bash
  PROMPT="$(cat D:/Contents/DRBCV-Knowledge/Templates/数学公式规范.md; echo; cat TASK-xx.md)"
  grok -m deepseek-v4 -p "$PROMPT" --yolo --output-format json --max-turns 35
  ```
  非数学 vault 不加载，零额外 token。

- **并行执行**：多批可同时 background 提交（每批独立 Grok session，互不干扰）
  ```bash
  terminal(background=true, notify_on_complete=true)
  ```

- **验证批必须跑通再扩全量**：检查卡片格式、类型判定、生活类比、正反例。

### 阶段 5：核验与补漏

```bash
ls Concepts/ | wc -l          # 卡片数是否合理
grep -rl "关键概念" Sources/ | wc -l  # 原文是否有未覆盖概念
```

常见漏卡原因：
- **图片信息丢失**：docx 图片里的公式/拓扑图/时序图只靠文字无法提取。Sources/ 保留 md（给 Grok）+ 原始 docx（给人对照图片）
- **概念被合并**：如 ALOHA 被合并进"随机访问介质访问控制" → 手动补独立卡
- **max_turns 触顶**：轮次耗尽时 `stop_reason=max_turns_reached` → 拆分小批重跑

### 阶段 6：Obsidian 图谱配置

打开 vault → 图谱视图 → 验证只有概念卡，无原文/模板噪声。

## 批大小参考

| 每批篇数 | 轮次 | 结果 |
|----------|------|------|
| 5 篇 | ~25 轮 | EndTurn ✓ 最优 |
| 6-7 篇 | 19-23 轮 | EndTurn ✓ |
| 10 篇 | 19-35 轮 | 可能触顶 |
| 13+ 篇 | 10 轮 | Cancelled ✗ |

**5-8 篇是最优窗口**。多了 Grok 赶工漏概念，少了浪费系统提示词开销（每批 ~9K input）。

## 成本估算

已验证案例（计算机网络，107 篇原文 → 81 张卡）：
- DeepSeek 增量 input: ~440K tokens
- DeepSeek 缓存命中: ~10,600K tokens（几乎零成本）
- DeepSeek output: ~130K tokens
- **总成本**: ≈ ¥0.70
- **墙上时间**: ~25 分钟（含手动任务拆分）
- **手写对比**: ~6.75 小时

## 数学 vault 特殊规则

链式加载 `D:/Contents/DRBCV-Knowledge/Templates/数学公式规范.md`：
- LaTeX 单反斜杠（禁止 `\\int`）
- 禁止在 markdown 表格内用 `|`（用 `\lvert...\rvert` 替代）
- 积分号前加 `\displaystyle`
- `dx` 前加 `\,` 间距
- 不定积分末尾 `+C`
- **Grok 不适合做批量 LaTeX 修复**（逐卡读写太慢）→ 用 Python 脚本做机械替换

## 常见陷阱

1. **docx 路径**：desktop-attachments 在 `C:\Users\53028\.hermes\desktop-attachments\`，不在 E 盘
2. **Python 环境**：用 Anaconda Python，Hermes venv 缺 python-docx
3. **文件名冲突**：同一目录下可能有其他课程的 docx（微积分混入计算机网络）→ 按文件名正则过滤
4. **Grok 记忆关闭**：`~/.grok/config.toml` 已设 `memory.enabled = false`
5. **Grok 自述不可信**：卡片内容以 git diff 核验，不以 LLM 自述为准
6. **github push**：先确认 Clash 代理 7897 端口可达
7. **嵌套 .git 陷阱**：子目录内有自己的 `.git/`（如 research 中 Ventures 创建的 git 仓库），`git add` 会将其当成 submodule（mode 160000）。清理：`find . -name ".git" -type d -not -path "./.git" -exec rm -rf {} +` 后重新 `git add`。**删除嵌套 .git 后 git index 可能卡住**（`fatal: not recognized as a git repository`），此时 `rm -f .git/index && git add -A` 重建 index。
8. **残留 .obsidian 陷阱**：子目录中可能有早期独立 vault 留下的 `.obsidian/`（含 workspace.json 等），应在 `git add` 前删除。`.gitignore` 用 `**/.obsidian/workspace.json` 覆盖所有层级。
9. **第三方 git 克隆体积陷阱**：`research/*/repos/` 下可能缓存了克隆的 GitHub 仓库（memobase、SillyTavern 等），单个可达 500MB+。`.gitignore` 加 `research/*/repos/` 排除。这些仓库自有 GitHub 源，不需要镜像到你的知识库仓库。

## 验证清单

- [ ] 验证批 5 篇跑通（EndTurn，卡片格式正确）
- [ ] 全量批全部 EndTurn（或触顶但有产出）
- [ ] Concepts/ 卡片数 ≥ Sources/ 原文数 × 1.2（每篇至少 1 张卡）
- [ ] 抽检 3-5 张卡：类型判定、正反例、生活类比齐全
- [ ] graph.json 排除 Sources/Templates/TASK
- [ ] `git push` 到 GitHub

### 快速格式验证（Hermes-native 建卡后）
```bash
cd "D:/Contents/DRBCV-Knowledge/<Domain>/Concepts"
for f in *.md; do
  echo "=== $f ==="
  head -8 "$f"        # 检查 frontmatter
  echo "---"
  grep "^## " "$f"    # 检查 7 章节
  echo ""
done
```

## Vault 仓库设置

### 首次推送到 GitHub

Vault 根即 git 根（`D:/Contents/`），首次同步步骤：

```bash
cd "D:/Contents"

# .gitignore（关键：排除第三方克隆 + 嵌套 git）
cat > .gitignore << 'EOF'
.sync/
research/*/repos/
**/.git/
**/.obsidian/workspace.json
**/.obsidian/workspace-mobile.json
**/.obsidian/hotkeys.json
EOF

# 清理嵌套 .git（research 下 Ventures 创建的仓库）
find . -name ".git" -type d -not -path "./.git" -exec rm -rf {} +

# init + commit + push
git init && git add -A && git commit -m "init: Obsidian vault 完整同步"
git remote add origin https://github.com/<user>/<repo>.git
git push -u origin master
```

### 如果没有 gh CLI → Python 创建 GitHub 仓库

```python
import urllib.request, json
data = json.dumps({"name": "repo-name", "private": False}).encode()
req = urllib.request.Request("https://api.github.com/user/repos",
    data=data, headers={"Authorization": "token <PAT>", "Accept": "application/vnd.github+json"}, method="POST")
with urllib.request.urlopen(req) as r: print(json.loads(r.read())["html_url"])
```

> Obsidian wikilink（`[[卡片名]]`）按文件名匹配，不依赖目录路径。文件在 vault 内随意移动不会断链。
