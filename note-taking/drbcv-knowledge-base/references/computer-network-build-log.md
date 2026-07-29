# 计算机网络知识库构建实录

日期: 2026-07-19
工具链: Hermes → Grok Build + DeepSeek v4

## 产出
- 107 篇 docx → md 转录稿
- 81 张 DRBCV 知识卡片（Ch1-6 全覆盖）
- 总成本: ≈¥0.70（DeepSeek 缓存命中率 ~96%）
- 墙上时间: ~25 分钟（vs 手写 ~6.75 小时）

## 执行批次

| 批次 | 源文件 | 卡片 | 轮次 | 结果 |
|------|--------|------|------|------|
| 验证批 | 5 篇 Ch1 | 9 | 25 | EndTurn |
| Ch1+Ch2 | 13 篇 | 1 | 10 | Cancelled（过大） |
| 2A Ch1 | 7 篇 | ~10 | 19 | EndTurn |
| 2B Ch2 | 6 篇 | ~6 | 23 | EndTurn |
| Ch3早期 | 10 篇 | ~12 | 19 | EndTurn |
| Ch3中期 | 10 篇 | ~10 | 35 | max_turns |
| Ch3后期 | 7 篇 | ~8 | 33 | EndTurn |
| Ch4A | 11 篇 | ~8 | ~25 | EndTurn |
| Ch4B | 17 篇 | ~10 | ~25 | EndTurn |
| Ch5 | 13 篇 | ~4 | ~25 | EndTurn |
| Ch6 | 7 篇 | ~7 | ~20 | EndTurn |

## 踩坑
1. 13 篇批被 Cancelled → 拆为 6-7 篇小批
2. CSMA/CA 批触顶 35 轮（图片引用过多）
3. ALOHA 被合并漏掉 → 手动补卡
4. 微积分文件混入 Sources → 正则过滤
5. Obsidian 81 个幽灵 image 节点 → graph.json 排除 media/

## 数学模型改进
- 基本积分公式: 表格 `|` 冲突 + 双反斜杠 → 改为列表格式 + `\lvert\rvert`
- 数学公式规范.md 创建 → 后续数学 vault 链式注入避免同类问题
