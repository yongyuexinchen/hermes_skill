# Grok 批量文件构建模式

## 适用场景
- 从多篇源文件提取概念 → 批量创建 DRBCV 知识卡片
- 对大量文件做同类型修改（加段落、改格式、补交叉引用）
- 初始化新 vault（从课程大纲建 20+ 张卡）

## 工作流

### 1. 源文件准备
```bash
# docx → md 文本抽取
python -c "
from docx import Document
doc = Document('source.docx')
text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
" > source.md
```

### 2. 验证批（先跑 5 篇）
- 选 3-5 个代表性源文件
- 任务书含完整卡模板 + 类型判定指导（discriminant / connection / mixed）
- Grok 跑完 → 抽查 2-3 张卡质量 → 确认格式/类型无误

### 3. 全量拆批
- 每批 ≤ 10 个源文件
- `--max-turns 30-35`
- 并行提交：`background=true, notify_on_complete=true`

### 4. 异常处理

| 现象 | 原因 | 处理 |
|------|------|------|
| `stopReason=Cancelled`，轮次少，产出卡远少于源文件数 | 批次过大（13 篇→ 10 轮被截） | 拆为 5-6 篇小批重跑 |
| `stopReason=max_turns_reached` | 触顶但仍有产出（部分卡已写入） | 补批覆盖未处理源文件 |
| 卡内容质量低（类型错标、概念遗漏） | 任务书指导不足 | 在任务书中加"关键概念提示"段 |

### 5. 结果核验
```bash
ls Concepts/ | wc -l          # 卡数
grep -l '如图所示' Sources/*.md | wc -l  # 图片引用文件（可能遗漏）
```

## 成本参考

实测：45 篇转录稿（~250K 字）→ 44 张知识卡

| 指标 | 数值 |
|------|------|
| 增量 input tokens | ~220K |
| 缓存命中 tokens | ~6.5M |
| 总批次数 | 7 批 |
| DeepSeek 费用 | ≈ ¥0.2 |

关键：DeepSeek 对重复读取的源文件内容缓存极好（`cache_read_input_tokens` >> `input_tokens`），批量越大越划算。

## 图片信息丢失（已知限制）

转录稿中"如图所示""如下图"处，图片内容（协议时序图、拓扑图、状态机）不会被 LLM 读取。

**缓解**：
- 高图片引用文件（如 CSMA/CA 有 6 处）→ 用火山方舟豆包视觉模型单独扫描 docx 图片
- 纯 text 的 95% 内容足够建基础卡，图片信息作为后续补丁
- Sources/ 保留原始 .docx 供人工对照

## Windows 特殊处理
- workdir 必须用 `E:/path` 或 `E:\\path` 格式
- `grok_adapter.py` 已处理 subprocess 路径；裸 terminal 调用时注意 shell 转义
