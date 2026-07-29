---
name: browser-use-cli
slug: hermes-browser-use
displayName: Browser Use CLI（浏览器自动化备用方案）
version: "2.0.0"
description: browser-use CLI v0.13+ 浏览器自动化工具。使用 stdin 管道 Python 代码模式（非旧版子命令）。当 Hermes 内置浏览器工具无法满足需求时作为备用方案。已包含 Windows Chrome CDP 调试启动流程。
agent_created: true
source: 实地测试 browser-use v0.13.7，覆盖旧版 SkillHub skill（v2.x 接口已废弃）
allowed-tools: terminal
---

# Browser Use CLI (v0.13+) — Hermes 备用浏览器方案

> **定位**：Hermes 内置浏览器工具的备用方案。当前安装版本 v0.13.7，接口为 **stdin 管道 Python 代码**，不是旧版的子命令风格。

## ⚠️ 版本警告

SkillHub 上的 `@shawnpana/browser-use` 文档对应 **v2.x 旧接口**（`browser-use open/click/state` 等子命令），已在 v0.13+ 废弃。**本 skill 文档基于实地测试的 v0.13.7 实际接口**。

子命令被移除后，CLI 的提示信息：
```
The browser-use CLI changed in 3.0, and 'open' was removed.
The old preset subcommands are gone. To use the CLI, you write raw Python and
pipe it on stdin, and it runs in a persistent browser session.
```

## 何时用这套方案

| 场景 | 用 Hermes 内置 | 用 browser-use CLI |
|------|:---:|:---:|
| 简单导航+截图 | ✅ | 也行 |
| 表单填写、搜索 | ✅ | 也行 |
| 自定义 JS 提取 | ❌ | ✅ `js()` |
| CDP 底层控制 | ❌ | ✅ CDP |
| 复用用户 Chrome 登录态 | ❌ | ✅ 连接已登录 Chrome |
| 云端浏览器 | ❌ | ✅ Cloud API |

---

## 安装 & 前置条件

```bash
pip install browser-use
```

### Windows 上必须：先启动 Chrome 远程调试

browser-use 通过 CDP 连接 Chrome。Windows 上需要先：

```bash
# 1. 杀掉已有 Chrome
taskkill //F //IM chrome.exe 2>/dev/null; sleep 2

# 2. 后台启动带调试端口的 Chrome
"C:/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/Users/53028/chrome-debug-profile"
```

然后用 `browser-use --doctor` 验证连接状态。

---

## 核心接口：stdin 管道 Python

### 单行命令

```bash
echo 'print(page_info())' | browser-use
```

### 多行命令（heredoc）

```bash
browser-use <<'PY'
new_tab("https://example.com")
wait_for_load()
print(page_info())
PY
```

> **Windows git-bash 注意**：heredoc 内的 Python 字符串用双引号，避免单引号转义问题。JavaScript 代码用双引号包裹。

---

## 核心 Helper 函数

| Helper | 作用 | 示例 |
|--------|------|------|
| `new_tab(url)` | 打开新标签页（首次导航必须用这个） | `new_tab("https://zhihu.com")` |
| `goto_url(url)` | 当前标签页跳转 | `goto_url("https://example.com")` |
| `page_info()` | 返回 dict：url, title, 尺寸 | `print(page_info())` |
| `capture_screenshot(path)` | 截图保存 | `capture_screenshot("C:/Users/53028/Desktop/shot.png")` |
| `fill_input(selector, text)` | 填写输入框 | `fill_input("input[name='q']", "关键词")` |
| `press_key(key)` | 按键 | `press_key("Enter")` |
| `click_at_xy(x, y)` | 坐标点击 | `click_at_xy(500, 300)` |
| `type_text(text)` | 向聚焦元素输入 | `type_text("hello")` |
| `scroll(x, y)` | 滚动 | `scroll(0, 500)` |
| `js(code)` | 执行 JavaScript，返回值 | `js("document.title")` |
| `wait_for_load()` | 等待页面加载完成 | `wait_for_load()` |
| `wait_for_element(selector)` | 等待元素出现 | `wait_for_element(".result")` |
| `list_tabs()` | 列出标签页 | `print(list_tabs())` |
| `switch_tab(target)` | 切换标签页 | `switch_tab(1)` |
| `close_tab(target)` | 关闭标签页 | `close_tab(1)` |

---

## 实战工作流

### 1. 验证连接

```bash
echo 'print(page_info())' | browser-use
# 正常返回：{'url': 'chrome://new-tab-page/', 'title': '新标签页', ...}
```

### 2. 打开目标网站

```bash
browser-use <<'PY'
new_tab("https://www.zhihu.com")
wait_for_load()
print(page_info())
PY
```

### 3. 搜索/填表

```bash
browser-use <<'PY'
fill_input("input[placeholder*='搜索']", "A股市场")
press_key("Enter")
PY
```

### 4. 提取内容

```bash
browser-use <<'PY'
wait_for_load()
text = js("document.body.innerText.substring(0, 3000)")
print(text)
PY
```

### 5. 截图验证

```bash
browser-use <<'PY'
capture_screenshot("C:/Users/53028/Desktop/result.png")
PY
```

---

## 已验证的完整案例：知乎搜索

在 Windows + browser-use v0.13.7 上实际跑通的完整流程，见 `references/zhihu-search-session.md`。

核心步骤回顾：
1. 启动 Chrome CDP → `browser-use --doctor` 确认
2. `new_tab("https://www.zhihu.com")` → 知乎首页（已登录）
3. `fill_input(...)` + `press_key("Enter")` → 搜索
4. `js("document.body.innerText...")` → 提取结果文本

---

## 排查

| 症状 | 诊断/解决 |
|------|----------|
| `command not found` | `pip install browser-use`，然后用完整路径或确保在 PATH 中 |
| daemon 连接失败 | 先启动 Chrome CDP 调试端口，再跑 `browser-use --doctor` |
| `open` 等子命令报错 | 接口已变，用 stdin Python 模式 |
| heredoc 内 JS 语法报错 | JS 字符串用双引号；避免换行在字符串中间 |
| `fill_input` 找不到元素 | 用 `page_info()` 确认页面已加载；试不同的 CSS selector |

---

## 进阶参考

- **CDP 底层控制**：见 `references/cdp-python.md`（注意：部分内容可能随版本变化）
- **多浏览器会话**：见 `references/multi-session.md`（注意：部分内容可能随版本变化）
- **本次实地测试记录**：见 `references/zhihu-search-session.md`

---

## 📝 版本记录

| 版本 | 日期 | 更新 |
|------|------|------|
| v2.0.0 (Hermes) | 2026-07-29 | 重写：实地测试 v0.13.7，替换全部旧版子命令为 stdin Python 接口；新增 Windows Chrome CDP 前置步骤；新增实战案例 |
| v1.0.0 (Hermes) | 2026-07-29 | 从 SkillHub v2.0.1 初始适配（接口已过时） |
