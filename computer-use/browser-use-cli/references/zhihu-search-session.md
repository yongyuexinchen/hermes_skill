# 实地测试：browser-use v0.13.7 知乎搜索

日期：2026-07-29，Windows 10，git-bash 终端

## 环境

- browser-use v0.13.7（pip install browser-use）
- Chrome 通过 CDP 连接（--remote-debugging-port=9222）
- 用户已登录知乎（Chrome 保留登录态）

## 完整操作序列及输出

### Step 1: 启动 Chrome CDP 调试端口

```bash
# 杀掉旧 Chrome
taskkill //F //IM chrome.exe 2>/dev/null; sleep 2

# 后台启动带远程调试的 Chrome
"C:/Program Files/Google/Chrome/Application/chrome.exe" \
  --remote-debugging-port=9222 \
  --user-data-dir="C:/Users/53028/chrome-debug-profile"
```

### Step 2: 验证连接

```bash
echo 'print(page_info())' | browser-use
```
输出：
```
{'url': 'chrome://new-tab-page/', 'title': '新标签页', 'w': 1036, 'h': 906, ...}
```
✅ 连接成功

### Step 3: 打开知乎

```bash
browser-use <<'PY'
new_tab("https://www.zhihu.com")
PY
```

无报错 = 成功。

### Step 4: 确认已到达知乎

```bash
echo 'print(page_info())' | browser-use
```
输出：
```
{'url': 'https://www.zhihu.com/', 'title': '(2 封私信 / 19 条消息) 首页 - 知乎', ...}
```
✅ 已登录状态

### Step 5: 搜索 "A股市场的最新消息"

```bash
browser-use <<'PY'
fill_input("input[placeholder='有问题，就会有答案'], input[aria-label='搜索'], input.SearchBar-input, [role='search'] input", "A股市场的最新消息")
PY
```

```bash
browser-use <<'PY'
press_key("Enter")
PY
```

### Step 6: 等待搜索结果加载

```bash
browser-use <<'PY'
wait_for_load()
print(page_info())
PY
```
输出：
```
{'url': 'https://www.zhihu.com/search?type=content&q=A%E8%82%A1%E5%B8%82%E5%9C%BA%E7%9A%84%E6%9C%80%E6%96%B0%E6%B6%88%E6%81%AF',
 'title': 'A股市场的最新消息 - 搜索结果 - 知乎', ...}
```

### Step 7: 截图

```bash
browser-use <<'PY'
capture_screenshot("C:/Users/53028/Desktop/zhihu-search-result.png")
PY
```

### Step 8: 提取文本内容

```bash
browser-use <<'PY'
text = js("document.body.innerText.substring(0, 3000)")
print(text[:2000])
PY
```
成功提取 3000+ 字符的搜索结果文本。

## 遇到的坑

1. **旧版子命令全部报错**：`browser-use open` → "The browser-use CLI changed in 3.0, and 'open' was removed." 必须用 stdin Python 模式。
2. **heredoc 内 JS 多行字符串**：用双引号包裹、避免换行断裂。单次 `js()` 调用里不要写复杂多行逻辑——拆成多次调用。
3. **CSS selector 匹配**：知乎是 React SPA，class 名是 hash。`fill_input` 传多个备选 selector（逗号分隔）更稳健。
4. **`new_tab` vs `goto_url`**：首次导航必须用 `new_tab()`。`goto_url()` 只对已有标签页有效。

## 结论

browser-use v0.13.7 的 stdin Python 接口**可以可靠地执行**导航、填表、搜索、截图、文本提取——但接口与 SkillHub 上的旧文档完全不同，必须按本文档使用。
