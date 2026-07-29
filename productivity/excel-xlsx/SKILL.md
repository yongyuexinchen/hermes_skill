---
name: excel-xlsx
description: 创建、检查和编辑 Microsoft Excel 工作簿及 XLSX 文件，支持可靠的公式、日期、类型、格式、重算及模板保留功能。
agent_created: true
source: SkillHub
---
# Excel / XLSX

创建、检查和编辑 Microsoft Excel 工作簿。

## 依赖

```bash
pip install openpyxl
```

## 基本用法

```python
import openpyxl

# 创建工作簿
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Sheet名称"

# 写入数据
ws.append(["列1", "列2", "列3"])

# 设置列宽
ws.column_dimensions['A'].width = 20

# 保存
wb.save("output.xlsx")
```
