# Wikipedia API 研究数据采集方法

## 高效采集流程

### 1. 获取页面介绍（extract intro）
```python
url = f'https://en.wikipedia.org/w/api.php?action=query&titles={page}&prop=extracts&exintro=1&explaintext=1&format=json'
```
适用场景：快速了解人物概要，2500字符以内。

### 2. 枚举所有章节（sections list）
```python
url = f'https://en.wikipedia.org/w/api.php?action=parse&page={page}&prop=sections&format=json'
```
返回所有章节标题和索引号（`index`）。用于定位目标章节——无需加载整页。

### 3. 按索引提取章节内容（section text）
```python
url = f'https://en.wikipedia.org/w/api.php?action=parse&page={page}&section={idx}&prop=text&format=json'
```
返回该章节的 HTML 文本，用 `re.sub('<[^>]+>', ' ', html)` 粗去标签。

### 4. 关键章节索引速查

| 人物 | 关键章节 | 索引 |
|------|---------|------|
| Carl Jung | Break with Freud | 9 |
| Carl Jung | Midlife isolation / Red Book | 11, 12 |
| Philip K. Dick | Mental health | 4 |
| Philip K. Dick | Paranormal experiences (2-3-74) | 5 |
| Philip K. Dick | Personal life | 6 |
| Nikola Tesla | Early years / Childhood (OCD traits) | 1, 2 |
| Nikola Tesla | Personal life and character | 29 |
| John Nash | Mental illness (schizophrenia) | 7 |
| John Nash | Recognition and later career | 8 |
| Franz Kafka | Early life (father relationship) | 2 |
| Franz Kafka | Personality | 7 |
| Franz Kafka | Personal life (engagements) | 5 |
| Franz Kafka | Max Brod (未烧毁手稿) | 16 |

## 速率限制

Wikipedia API 无官方速率限制文档，但实际经验：
- 快速连续请求（<1s间隔）会触发 HTTP 429 Too Many Requests
- 安全间隔：每次请求后 `time.sleep(1-3)` 秒
- 被限流后：`sleep(10)` 再重试
- 批量请求策略：每批 3-4 个请求，批间 sleep(5)

## 替代方案

- **browser_navigate + browser_snapshot**：对于含大量表格/侧边栏的 Wikipedia 页面，快照文本量巨大（10000+行），不适合直接提取内容
- **browser_console innerText**：`.mw-parser-output` 选择器在 Wikipedia 新皮肤下可能返回空
- **curl 直接请求**：比浏览器快但无 JavaScript 渲染（Wikipedia 静态内容不需要 JS）
