# Wikipedia API 结构化提取技术

## 适用场景

在境内网络环境中，Google 搜索常被 CAPTCHA 拦截、Bing 搜索对金融/技术内容过滤严重时，Wikipedia API 是获取可靠结构化事实数据的高效替代渠道。

## 核心 API 端点

```
https://en.wikipedia.org/w/api.php?action=query&titles=<页面标题>&prop=extracts&explaintext=1&format=json
```

## 在 Python 中调用（推荐方式）

```python
import urllib.request, json

url = 'https://en.wikipedia.org/w/api.php?action=query&titles=AI_bubble&prop=extracts&explaintext=1&format=json'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
data = json.loads(urllib.request.urlopen(req).read().decode('utf-8'))
pages = data['query']['pages']
for pid, page in pages.items():
    text = page.get('extract', '')
    print(text[:8000])  # 可按需截取
```

## 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `action` | `query` | 查询操作 |
| `titles` | URL 编码的页面标题 | 支持管道符 `\|` 分隔多个页面 |
| `prop` | `extracts` | 返回纯文本提取 |
| `explaintext` | `1` | 返回纯文本（非 HTML） |
| `format` | `json` | JSON 格式响应 |
| `exsectionformat` | `plain`（可选） | 扁平化章节标题 |

## 与 browser_navigate 对比

| 维度 | Wikipedia API | browser_navigate |
|------|--------------|-----------------|
| 速度 | 秒级 | 数秒至数十秒 |
| 数据格式 | 结构化 JSON | 需解析 HTML 快照 |
| 截断问题 | 可控（API 限制 ~12万字） | 经常被截断（8000+ 字符） |
| 可靠性 | 稳定 | 可能被 CAPTCHA 拦截 |
| 提取特定章节 | 支持 `exsectionformat=plain` | 需手动滚动/全量快照 |

## 典型用例：提取 Wikipedia 条目的特定章节

```python
text = page.get('extract', '')
# 定位到关键章节
idx = text.find('Dot-com bubble comparisons')
if idx > 0:
    print(text[idx:idx+3000])
```

## 已知限制

1. **英中文条目标题差异**：中文维基条目名称可能与英文不同（需查 zh.wikipedia.org）
2. **extract 长度限制**：API 默认返回约 12 万字符，超长条目可能不完整
3. **更新频率**：Wikipedia 内容由社区维护，时效性不如实时新闻

## 适用条目示例（已验证）

| 条目（英文） | 用途 |
|------------|------|
| `AI_bubble` | AI 泡沫数据（市值、投资额、央行警告） |
| `Dot-com_bubble` | 互联网泡沫历史对照（Nasdaq 涨跌、幸存率） |
| `AI_boom` | AI 浪潮全貌（能源、文化、经济影响） |
| `AI_data_center` | 数据中心电力消耗、建设投资 |
| `AlphaFold` | AI 制药技术进展 |
| `Figure_AI` | 具身智能/人形机器人进展 |
| `Optimus_(robot)` | Tesla 机器人进展 |
| `Isomorphic_Labs` | DeepMind 药物发现分拆 |
