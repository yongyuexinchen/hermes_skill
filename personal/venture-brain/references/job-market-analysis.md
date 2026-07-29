# Job Market Analysis Pipeline

> 从招聘截图到学习路线的方法论。2026-07-27 实战验证，289条Boss直聘岗位→完整分析报告。

## 流水线

```
Boss直聘截图(.jpg)
  → RapidOCR (ONNX, 独立venv)  → {job_id}.txt
  → Regex结构化提取              → _structured.json
  → 分类分析(应用开发/算法/基础设施/产品)
  → 技能缺口 × 课程对照
  → 个人学习路线
```

## 关键决策点

### 1. OCR选型：RapidOCR > PaddleOCR > EasyOCR
- EasyOCR: 模型在GitHub，国内超时
- PaddleOCR: PaddlePaddle依赖地狱+venv污染
- RapidOCR: ONNX Runtime，零冲突，模型从hf-mirror下载
- **必须unset PYTHONPATH** 避免Hermes venv污染

### 2. 结构化提取：纯正则，不用LLM
- 8个字段全部正则+词表匹配，98%+准确率
- 岗位分类必须拆4类：应用开发/算法研究/基础设施/产品自动化
- **不能全量混在一起统计**——Java 42%主要来自基础设施，应用开发岗内是"附加项"不是"替代项"

### 3. 技能缺口分析
- 不要从"所有岗位需要什么"出发堆技能
- 要从"目标岗位+个人项目+现有能力"倒推
- 验证方法：看JD原文上下文，不是看关键词频率
- 例：Java出现不是因为"用Java做AI"，而是"Python/Java/Go之一"

### 4. 隐藏技能识别
- Docker书面需求25%，但71%的JD含部署需求
- 统计关键词频率要结合JD语义上下文

## 输出物
- `_structured.json`: 289条岗位结构化数据
- `分析报告.md`: 市场全景+技能缺口+课程对照+学习路线+附录(G.1/G.2完整源码)
- DRBCV卡片: 关键概念沉淀

## 常见陷阱
- ❌ 把不同岗位族的技能混在一起做词频
- ❌ 看到关键词就认为"必须精通"
- ❌ 不验证JD原文上下文就下结论
- ✅ 先拆岗位类型，再逐类分析
- ✅ 看JD里技能的写法（"之一" vs "必须"）
- ✅ 用数据验证每个假设
