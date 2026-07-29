# 搜索后端选型

## 中国用户搜索策略

### 主力：CDP 浏览器 + 百度

CDP 连接的本地 Chrome 直接搜索百度，能看到所有结果、浏览页面、提取内容。适合深度研究和需要登录的网站。

优势：零成本、无 API 限制、带用户登录态
劣势：速度慢（3-10秒/次）、需 Chrome 调试模式

### 备选：博查 API (Bocha)

国内专用搜索 API，可搜知乎、公众号、CSDN 等中文平台。

- 注册：https://open.bochaai.com
- 免费额度：1000次/月
- 配置（待验证）：
```bash
# .env
BOCHA_API_KEY=sk-xxx

# Hermes 可能需自定义 provider，或通过 web_search 插件接入
```

### 备选：SearXNG 自建

自托管元搜索引擎，可聚合百度、Bing、知乎等。

```bash
docker run -d -p 8080:8080 searxng/searxng
# 配置 settings.yml 启用百度引擎
```

### 不可用方案

| 方案 | 原因 |
|------|------|
| Google 搜索 | 国内无法直接访问 |
| Brave Search | 英文为主，中文差 |
| DuckDuckGo | 同上 |
| Tavily | 同上，且需付费 |

## Hermes 内置搜索插件

| 插件 | 状态 |
|------|------|
| Tavily | 已安装，不适合中文 |
| SearXNG | 已安装，可自建 |
| Brave Free | 已安装，英文为主 |
| DDGS | 已安装，英文为主 |
