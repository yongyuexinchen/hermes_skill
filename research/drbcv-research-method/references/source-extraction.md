# 原文提取模式

从 docx/pdf 逐字稿批量提取文本到 `Sources/` 目录。

## 工具

- **docx**: `python-docx`（`pip install python-docx`）
- **pdf**: `pymupdf`（轻量）或 `marker-pdf`（需要 OCR 时）

## docx 提取脚本模板

```python
from docx import Document
import os, glob

base = r"C:\Users\53028\.hermes\desktop-attachments"
out_dir = r"D:\Contents\DRBCV-Knowledge\<Domain>\Sources"
os.makedirs(out_dir, exist_ok=True)

files = sorted(glob.glob(os.path.join(base, "*原文*.docx")))

for f in files:
    bn = os.path.basename(f).replace(".docx", ".txt")
    out_path = os.path.join(out_dir, bn)
    doc = Document(f)
    # 提取段落，跳过标题行和时间戳
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    text_lines = [
        p for p in paragraphs
        if not p.startswith("202") and not p.startswith("发言人")
    ]
    text = "\n\n".join(text_lines)
    with open(out_path, "w", encoding="utf-8") as fout:
        fout.write(text)
```

## 命名规范

建议重命名为统一格式方便 agent 定位：
```
ch<章号>-<节号> <概念名>.txt
```
例如：`ch1-3 行列式的定义.txt`、`ch7-5-1 散列表的基本概念.txt`

## 注意事项

- 不要在 Sources 目录放不相关课程的文本（如数据结构目录里混入计算机网络文件）
- 提取后抽样 2-3 个文件验证内容完整性
- 跳过重复文件（如 `(1)` `(2)` 后缀的副本）
