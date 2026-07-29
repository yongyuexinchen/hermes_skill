# Windows Subprocess .CMD 陷阱

## 问题

在 Windows 上，npm 全局安装的 `grok` 实际是 `grok.CMD` wrapper。当 Python 的 `subprocess.run(['grok', ...])` 调用时：

```
FileNotFoundError: [WinError 2] 系统找不到指定的文件。
```

即使 `shutil.which('grok')` 返回 `C:\Users\...\npm\grok.CMD`，`subprocess.run` 也会失败。

## 根因

Windows `CreateProcess` API 不识别 `.CMD` 文件扩展名作为可执行文件。`shutil.which()` 能找到它，但 `subprocess.run` 最终调用 `CreateProcess`，后者需要 `.exe` 扩展名或 shell 介入。

## 修复 (applied to adapter v0.2.1)

```python
# 修复前 (v0.2.0) —— Windows 上失败
cmd = [cfg["grok"]["binary"], "-p", task, ...]  # ['grok', ...] → FileNotFoundError

# 修复后 (v0.2.1)
binary = shutil.which(cfg["grok"]["binary"]) or cfg["grok"]["binary"]
# binary = 'C:\\Users\\...\\npm\\grok.CMD' (完整路径)
cmd = [binary, "-p", task, ...]  # ✅
```

`subprocess.run` 接受完整路径时，Windows 通过文件关联处理 `.CMD`。

## 绕过方案

直接用 bash shell 调 grok（不经过 Python subprocess）：

```bash
grok -p "<task>" -m deepseek-v4 --output-format json --cwd "E:/path"
```

Bash 的进程衍生原生处理 `.CMD` 解析，无需额外处理。

## 复现条件

- OS: Windows
- Grok 安装: `npm i -g @xai-official/grok`（产生 `grok.CMD` 在 `%APPDATA%/npm/`）
- Python: 任意版本，`subprocess.run(['grok', ...])` 不带 `shell=True`
