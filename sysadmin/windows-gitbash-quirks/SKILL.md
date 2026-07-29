---
name: windows-gitbash-quirks
description: Windows git-bash/MSYS 环境下的路径转换陷阱与 GitHub 网络访问模式。git clone 目标盘符跑偏、Hermes 文件工具/原生 python 的路径格式要求、代理端口探测与镜像加速降级。任何在此机器上 clone 仓库、跨盘操作文件、或 GitHub 访问失败时加载。
---

# Windows git-bash 路径与网络陷阱

## 触发条件
在这台 Windows 机器 (git-bash/MSYS shell) 上: git clone/push、跨盘符文件操作、调用 python 脚本、GitHub 访问失败/代理问题。

## 一、路径转换陷阱（都是实际踩过的）

### 1. git clone 目标路径跑偏 ⚠️ 最阴险
`git clone <url> /e/foo` 会打印 `Cloning into '/e/foo'` 并"成功"，但原生 git.exe 实际把 `/e/foo` 解析成**当前盘符根下的 \e\foo**（cwd 在 C: 时 → `C:\e\foo`）。输出完全看不出问题。

- **规则**: clone/checkout 目标一律用 Windows 正斜杠格式 `E:/foo`，或先 `cd /e` 再用相对路径。
- **必须验证**: clone 完立刻 `ls <目标>` 确认文件真的在。不在时查 `C:\e\`、`C:\Program Files\Git\<路径>`。
- 搬运补救: `mv /c/e/foo /e/foo && rmdir /c/e`（bash 的 mv 是 MSYS 程序, 正确理解 /e/ 挂载）。

### 2. Hermes 文件工具不认 MSYS 路径
`read_file`/`search_files` 传 `/e/foo` 报 "Path not found"。**必须用 `E:\foo` 或 `E:/foo`**。terminal 里的 bash 命令 (ls/mv/grep) 则两种都认。

### 3. 原生 python 不认 /c/ 路径
本机 python 是 anaconda 原生 exe: `python /c/Users/x/script.py` 报 "can't open file 'C:\\c\\Users\\...'"（MSYS 参数转换没生效时直接拼盘符）。**传脚本路径用 `C:/Users/x/script.py`**。

### 4. npm config prefix 跑偏 ⚠️
`npm config set prefix /e/npm-global` → npm 解析为 `C:\e\npm-global`（当前盘符根下），而不是 E 盘。
- **规则**: npm config 传路径一律用 Windows 格式 `"E:\\npm-global"`，不用 MSYS `/e/...`。
- **验证**: `npm config get prefix` 确认输出是 `E:\\npm-global` 而非 `C:\\e\\npm-global`。
- **清理**: 跑偏后 `rm -rf "C:/e/npm-global"` + 修正 prefix + 重装。

### 5. 通用规则
正斜杠 Windows 路径 `C:/Users/...` 在 bash、python、git、Hermes 工具里全部通用 — 拿不准就用它。
- 扩展: 不仅仅是 Hermes 文件工具和 git，**npm/yarn/pnpm 等 Node 生态工具的 config 路径也受此影响**，传路径前先想清楚用的是 MSYS 感知程序还是原生 Win32 程序。

## 二、GitHub 访问决策链

```
1. 探测代理:  timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/<端口>' && echo OK || echo DOWN
   本机端口: 7897 = Clash Verge 混合端口(常开); 10809 = Clash HTTP(S) 代理(实测稳定);
   10808 = V2Ray(git 全局配置写的是它); 7890 = Clash 旧端口(时常离线)
   ⚠️ 多个代理不一定同时在跑 — 用循环探测找到可用端口再配环境变量
2. 代理通    → 直接 git clone/push
3. 代理不通  → 镜像加速 + 临时绕过 git 全局代理配置:
   git clone -c http.proxy= -c https.proxy= --depth 1 \
     https://ghfast.top/https://github.com/<owner>/<repo>.git E:/<dest>
   (ghfast.top 前缀加速, 实测满速; 失效备选: gh-proxy.com, ghproxy.net)
4. 镜像只解决 clone/pull; push 回 GitHub 仍需真代理/VPN
```

### 代理干扰 conda/pip ⚠️
Clash 代理 (127.0.0.1:7897) 即使 `conda config --show proxy_servers` 显示 `{}`，**系统环境变量 `http_proxy`/`https_proxy` 仍会劫持 conda 和 pip 的 HTTPS 请求**，导致 SSL 握手失败 (`SSLEOFError`, `ConnectionResetError 10054`)。

- **解决**: 使用 conda 或 pip 前 `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY`
- **pip 专用**: `pip install --proxy "" ...` 也能禁用代理
- **国内镜像加速**: conda 用清华单频道 `--override-channels -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main`（只走一个频道，减少代理干扰点）

### PYTHONPATH 子进程继承
Windows CMD 下启动 Python WebUI 项目时，子进程 (`subprocess.Popen`) **不自动继承父进程的 PYTHONPATH**。必须显式设置:
```cmd
set PYTHONPATH=E:\项目根;C:\Users\53028\.conda\envs\<env>\Lib\site-packages
```
Windows 下 PYTHONPATH 用**分号 `;`** 分隔路径。

### ⚠️ Hermes PYTHONPATH 全局污染（核心大坑）

**症状**: 任何 `terminal` 里跑的 Python 命令，import 包时都会混入 Hermes venv 的旧版本依赖（PIL, pydantic, protobuf, yaml 等），导致:
- `ModuleNotFoundError` / `ImportError`（pydantic v1/v2 冲突、PIL._imaging 找不到）
- pip 安装成功但 import 失败
- conda env 的包被 hermes venv 的包 shadow

**根因**: Hermes 启动时注入了环境变量:
```
PYTHONPATH=C:\Users\53028\AppData\Local\hermes\hermes-agent;
           C:\Users\53028\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages
```
`terminal` 工具执行的命令继承此变量，导致 `sys.path` 最前面就是 hermes 的包。

**解决优先级**:

1. **脚本内修复**（临时）：在 `import` 任何东西之前
```python
import os, sys
os.environ['PYTHONPATH'] = ''
sys.path = [p for p in sys.path if 'hermes-agent' not in p]
```
⚠️ 限制：如果某包在脚本修复前被导入（如通过 `sitecustomize.py`），此方法失效。

2. **独立 Python 安装 + venv**（推荐，根治）：
```bash
# 用非 conda 的独立 Python（本机 D:\python3.10.6\python.exe）
/d/python3.10.6/python -m venv /c/Users/53028/<venv_name>
/c/Users/53028/<venv_name>/Scripts/python -m pip install <packages>
```
独立 Python 不依赖 conda activate，sys.path 完全干净。

3. **不要尝试的**：
- ❌ `unset PYTHONPATH && python ...` — git-bash 的 export 有 UTF-16 BOM 问题（见下方）
- ❌ `conda run -n <env> python ...` — 内部仍继承 PYTHONPATH
- ❌ 在已有 conda env 里 `pip install --user` / `--target` — 依赖地狱不可解

### git-bash export 的 UTF-16 BOM 陷阱

```bash
export HTTP_PROXY=http://127.0.0.1:10809 && python script.py
```
在 git-bash 中会报 `bash: $'\377\376export': command not found`。
`\377\376` = UTF-16 LE BOM，说明脚本文件或 heredoc 被编码成 UTF-16。

**修复**: 不要在同一行写 export + python。用独立脚本文件，或在脚本内 `os.environ['VAR'] = 'value'` 设置。

- `-c http.proxy= -c https.proxy=` 是**单次命令级**覆盖, 不污染全局配置, 优于改 `git config --global`。
- GitHub API 搜索 (api.github.com) 国内常可直连, 找仓库全名可以先 `curl -s "https://api.github.com/search/repositories?q=..."` 不需要代理。

## 三、启动 Windows GUI 程序

从 git-bash 启动 Windows GUI 程序（安装包、桌面应用等）时，直接跑 exe 可能不弹窗口。

**推荐方法（按可靠性排序）：**

```bash
# 1. cmd start /B — 最可靠
cmd.exe /c "start /B C:\path\to\app.exe"

# 2. PowerShell Start-Process — 适合需要参数的程序
powershell.exe -Command "Start-Process 'E:/path/to/installer.exe'"
```

- `explorer.exe <exe路径>` 经常失败（exit code 1），不推荐
- `start "" "path"` 在 git-bash 中行为不稳定，用 `cmd /c start` 包装

## 四、NSIS 安装包静默安装 ⚠️ 可能跑偏

NSIS（Nullsoft Installer）安装包用 `/S /D=目标路径` 参数做静默安装时，**可能表面成功但文件未写入目标目录**——文件实际被解压到 `%TEMP%/nskXXXX.tmp/7z-out/`。

**症状：** 命令返回 `exit 0`、打印 "INSTALL DONE"，但目标目录为空或只有部分文件。

**修复：**
```bash
# 1. 找到临时解压目录
find /c/Users/$USERNAME/AppData/Local/Temp -maxdepth 1 -name "nsk*.tmp" 2>/dev/null

# 2. 手动搬运
cp -r "/c/Users/$USERNAME/AppData/Local/Temp/nskXXXX.tmp/7z-out/"* "/c/目标路径/"
```

**根本方案：** 对 NSIS 安装包优先用 GUI 安装（`powershell -Command "Start-Process ..."` 弹窗让用户点），静默安装在 Windows 下成功率不稳定。

## 五、验证清单
- clone 后: `ls <目标目录>` + `du -sh` 确认非空
- 改代理后: 先 /dev/tcp 探测端口再跑 git, 别用 git 报错当探测器 (报错慢且信息混淆)
