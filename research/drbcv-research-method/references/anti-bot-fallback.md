# 信源反爬应对参考

## 知乎 (zhihu.com)

**问题**：知乎使用自研 `zse-ck` JavaScript 挑战机制防爬。即使设置正确的 User-Agent、Referer、Accept-Language 等请求头，仍然返回 403 + 空 body（仅含 zse-ck 脚本）。

**表现**：
```
status=403, body=<html>...<meta id="zh-zse-ck" content="...">...</html>
```

**验证记录（2026-07-15）**：
- curl + Chrome UA → 403
- Python requests + fake-useragent → 403
- Python requests + mobile UA → 403
- Hermes browser_navigate → 403 (snapshot 只显示 zse-ck 错误)
- 知乎 API (`api.zhihu.com/v4/articles/...`) → 同样 403

**根本原因**：zse-ck 要求客户端执行 JavaScript 计算动态 token，纯 HTTP 请求库无法完成。

**绕过方案（按优先级）**：
1. **换信源** — 同一篇文章经常被转载到腾讯云开发者社区、CSDN、博客园、公众号。搜索文章标题即可找到镜像。
2. **用户粘贴** — 让用户直接复制粘贴文章内容，最可靠。
3. **无头浏览器** — 使用 Playwright/Puppeteer 等真浏览器引擎（复杂度高，不推荐用于单篇文章）。

**原则**：不要因为一个信源打不开就停止 Recon。多信源冗余是 Recon 阶段的正常状态。

## 通用反爬信号

如果遇到以下情况，直接切换信源，不要浪费时间调试：
- 返回 403 + 页面包含 `<meta id="zh-zse-ck">` 或类似 JS challenge 标签
- 返回 503 + Cloudflare challenge
- 返回空 body 但有 JS redirect
- 返回验证码页面
