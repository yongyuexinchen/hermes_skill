---
name: product-comparison-research
description: >
  硬件产品/技术品类的竞品调研与结构化对比分析。用于快速摸清一个品类的主要产品、
  核心参数、市场地位，输出结构化 Markdown 对比表。
  v1.0：Wikipedia 浏览器提取技巧 + 对比表输出格式规范。
version: 1.0.0
category: research
triggers:
  - 调研
  - 产品对比
  - 竞品分析
  - 对比表
  - 帮我整理一下这个品类的产品
  - 分析一下这个市场
  - 硬件产品参数对比
---

# 产品对比调研 (Product Comparison Research)

## 定位

针对 **硬件产品 / 技术品类** 的快速竞品调研，输出结构化 Markdown 对比表 + 市场概况。

适用场景：智能眼镜、MR 头显、智能手表、TWS 耳机、无人机、机器人等硬件品类。

## 工作流

### Phase 1：锁定品类 & 候选产品清单

1. 确认品类边界（如"AI 音频眼镜" vs "AR 眼镜"——分清楚）
2. 列出品类内主要产品（国内外、高中低价位段至少各 2-3 款）
3. 确定对比维度：品牌、型号、发布时间、价格、重量、芯片、显示/摄像头、AI 能力、续航、亮点、不足

### Phase 2：数据采集

**首选：Wikipedia 浏览器提取**（🔑 关键技巧）

终端 `curl` 在中国网络下对 Wikipedia 经常超时或返回空，但 `browser_navigate` 走的浏览器网络栈往往可达。因此：

1. 用 `browser_navigate` 打开 Wikipedia 产品页面
2. 用 `browser_console` 执行 JavaScript 提取正文：

```js
// 提取 Wikipedia 正文
(() => {
  const content = document.querySelector('#bodyContent') || document.querySelector('#mw-content-text');
  if (!content) return 'No content found';
  return content.innerText.substring(0, 8000);  // 分段提取
})();

// 继续提取剩余内容（偏移 8000）
content.innerText.substring(8000, 16000);
```

> 为什么用这个方法：Wikipedia 页面通过浏览器加载走的是与终端不同的网络路径（浏览器可能有代理/VPN），且 JavaScript 方式提取纯文本比滚动快照更高效。

**备选：产品官网**

用 `browser_navigate` 访问产品官网获取定价、SKU、最新型号信息（如 meta.com/ai-glasses/）。

**补充：公开报道**

对没有 Wikipedia 条目的产品（如国产中小品牌），搜索公开新闻稿/评测文章补充参数。

### Phase 3：输出结构化对比表

标准输出格式：

```
## 品类名称对比表

| 品牌 | 型号 | 发布时间 | 价格 | 重量 | 芯片 | 核心参数A | 核心参数B | AI/系统 | 续航 | 亮点 | 不足 |
|------|------|----------|------|------|------|----------|----------|---------|------|------|------|
```

#### 输出要求

- **每个品类一个主表**，同类产品全部纳入一条表
- **维度与品类对齐**：智能眼镜的核心维度是摄像头/AI/续航，MR头显的核心维度是显示分辨率/芯片/透视方式
- **标注最新代际**：用加粗或 🆕 标记当前最新一代产品
- **附带品类市场概况摘要**：1-2 段概述出货量、市占率、价格带、增长趋势
- **文末附数据来源说明**：Wikipedia 条目链接、官网、公开报道

### Phase 4：验收

- [ ] 对比表覆盖品类内主要玩家（国内 + 国外，≥5 款）
- [ ] 所有维度的数据均来自实际抓取/查阅，非凭空编造
- [ ] 价格、重量、发布时间等关键字段均已填充
- [ ] 表后有品类市场概况段落
- [ ] 有数据来源说明

## 常见陷阱

### 陷阱 1：Wikipedia 终端 curl 不可达（🔴 高频）

在中国网络下，`curl https://en.wikipedia.org/...` 经常超时或返回空响应。

**症状**：`json.decoder.JSONDecodeError: Expecting value`（curl 返回空），或 `Command timed out`

**解决**：切换到 `browser_navigate` + `browser_console` JavaScript 提取方案（见 Phase 2）。

### 陷阱 2：中文搜索 URL 编码问题

`browser_navigate` 到中文 Google 搜索 URL（含 `hl=zh-CN` 参数）可能因编码问题失败：
```
'utf-8' codec can't decode byte 0xb2...
```

**解决**：始终使用英文搜索词（`hl=en`），产品名用英文/拼音。对于中文特有产品，直接用 Wikipedia 或百度百科页面。

### 陷阱 3：产品官网是 SPA 动态加载

像 meta.com 等现代官网大量使用 JavaScript 动态渲染，`browser_snapshot` 可能只抓到 loading 状态。

**解决**：用 `browser_console` 执行 `document.title` 或读取关键 DOM 元素；对于重度 SPA，直接从 Wikipedia 获取整合后的参数更高效。

## 参考文件

- `references/ai-glasses-mr-headsets-2025.md` — 2025年7月 AI 音频眼镜 + MR 头显调研数据快照，可作为下次同类调研的 baseline 起点

## 参考数据源

| 类型 | 来源 | 用法 |
|------|------|------|
| Wikipedia | en.wikipedia.org/wiki/<产品名> | 参数表、发布时间、芯片型号 |
| 产品官网 | meta.com, apple.com, huawei.com 等 | 最新定价、SKU、在售型号 |
| GSMArena 类 | gsmarena.com（手机）/ vr-compare.com（VR） | 硬件参数交叉验证 |
| 公开报道 | The Verge, UploadVR, 36氪, 虎嗅 | 国产产品参数、中国定价 |
