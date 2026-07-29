---
name: python-china-env-setup
description: 中国大陆网络下 Python/Conda ML 环境搭建实战——镜像源、代理坑、导入调试、子进程 PYTHONPATH
---

## 触发条件
在中国大陆网络环境下创建 Conda 环境、安装 PyTorch CUDA 版、pip 依赖、或遇到 Python 导入/子进程问题时加载。

## 核心原则

1. **Conda 创建环境时关代理**：系统 `http_proxy` 变量会干扰 conda 即使配了国内镜像
2. **PyTorch CUDA 版只能从官方源或南大镜像获取**：阿里云/清华 pip 镜像只有 CPU 版
3. **子进程不会自动继承 PYTHONPATH**：需要显式 export
4. **新建环境比修旧环境快**：不要和已有环境纠缠权限/依赖冲突

## 镜像源速查

### Conda 创建环境（清华）
```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
conda create -n <name> python=3.12 \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main \
  -y --override-channels
```

### PyTorch CUDA 版（南大镜像，国内唯一可靠的 CUDA wheel 源）
```bash
pip install torch==2.7.1+cu128 torchaudio==2.7.1+cu128 \
  --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu128 \
  --extra-index-url https://mirrors.pku.edu.cn/pypi/simple
```
> 注意：南大镜像的 torch 版本可能比官方旧，选择可用的最新版即可。
> CUDA 12.8 对 RTX 4060 完全支持，12.4 也能用。

### Pip 通用依赖（北大镜像，比阿里云全）
```bash
pip install -r requirements.txt -i https://mirrors.pku.edu.cn/pypi/simple
```

### 备选
- 阿里云 pip：`https://mirrors.aliyun.com/pypi/simple`（快但只有 CPU 版 torch）
- 清华 conda pytorch：有 `pytorch=2.5.1=py3.10_cuda12.4` 版本
- 清华 pip：有 torch 但全是 CPU 版

## Python 导入调试

### 经典问题：脚本在 package 目录内运行触发循环导入
**症状**：`ImportError: cannot import name 'X' from partially initialized module`
**根因**：`python package/script.py` 运行时 Python 把 `package/` 放进 sys.path，导致 `import package` 找到 `package/some_module.py` 而非 `package/__init__.py`

**修复**：在入口脚本最开头插入项目根目录：
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### 子进程继承 PYTHONPATH
Windows 下用分号分隔：
```bash
export PYTHONPATH="C:/path/to/site-packages;E:/project-root"
```
确保在启动主进程前 export，子进程通过 `shell=True` + `Popen` 自动继承。

### 用户级 site-packages 污染
如果 pip 报 "Defaulting to user installation because normal site-packages is not writeable"：
```bash
pip install --target "C:/Users/<user>/.conda/envs/<env>/Lib/site-packages" --ignore-installed -r requirements.txt
```
之后必须 `export PYTHONPATH` 指向该目录。

### ⚠️ Hermes PYTHONPATH 污染（Windows 特有）

Hermes 的 `terminal` 工具运行时，环境变量 `PYTHONPATH` 已被注入 hermes venv 路径（`C:\Users\53028\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages`），导致所有 Python 命令的 `sys.path` 最前面都是 hermes 的包。与 conda env 的依赖冲突几乎无解。

**铁律：所有 `pip install` 和 `python` 命令都必须加 `unset PYTHONPATH` 前缀。**
否则 pip 会把包装到 hermes venv 而非目标环境 — 看起来安装成功，实际目标 venv 空空如也。`python -c "import X"` 也会从 hermes venv 加载旧版依赖（pydantic / PIL 冲突最常见）。

```bash
# ✅ pip 装到目标 venv（注意前缀 unset PYTHONPATH）
unset PYTHONPATH && "C:/path/to/venv/Scripts/python.exe" -m pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple

# ✅ 运行脚本
unset PYTHONPATH && "C:/path/to/venv/Scripts/python.exe" batch.py

# ❌ 包装到了 hermes venv — import 全找不到
"C:/path/to/venv/Scripts/python.exe" -m pip install paddleocr
```

- **推荐**: 用独立 Python 安装建 venv（如 `D:\python3.10.6`），全程 `unset PYTHONPATH`，完全避开 hermes 和 conda 依赖地狱
- **临时**: 脚本最开头执行 `os.environ['PYTHONPATH'] = ''; sys.path = [p for p in sys.path if 'hermes-agent' not in p]`
- **已踩坑**: 本机多次 pip 装完 import 找不到 — 每次都是忘了 `unset PYTHONPATH`
- 详见 `windows-gitbash-quirks` skill

## 代理排查

```bash
# 检查代理环境变量
echo "http_proxy=$http_proxy"
echo "https_proxy=$https_proxy"

# 测试代理端口
curl -s --connect-timeout 3 http://127.0.0.1:7897 && echo "在线" || echo "离线"

# Conda 操作前清理代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
```

代理间歇性 SSL 失败是 Clash 规则/节点问题——不是代码问题，等节点恢复或换直连。

## 已踩过的坑

- ❌ `pip install torch --index-url https://download.pytorch.org/whl/cu128` → 代理 SSL 失败
- ❌ 清华 pip 镜像 `torch==2.5.1+cu124` → 只有 CPU 版
- ❌ conda `pytorch-cuda=12.8` → 清华 conda 没有这个包
- ❌ conda 安装时 `unset` 放在 source conda.sh 之后 → 太晚了
- ✅ `unset` 放在 source conda.sh **之前** + `--override-channels` → 干净快速
- ✅ `sys.path.insert(0, ...)` 在入口脚本 → 根治循环导入
