---
name: ml-python-windows-setup
description: Windows 上搭建 Python ML/AI 项目（PyTorch、conda、pip）的环境配置陷阱与解决方案。PyTorch CUDA 国内镜像下载、conda 代理干扰隔离、子进程 PYTHONPATH 继承、pip --target 权限绕过、Gradio 依赖版本冲突。任何在此机器上新建 Python ML 项目环境时加载。
---

# Windows ML Python 环境搭建

## 触发条件
在 Windows 上创建 conda 环境装 PyTorch、pip 安装失败/权限报错、子进程找不到模块、Gradio 启动报错。

## 一、PyTorch CUDA 版下载

### 关键发现
国内 pip 镜像（阿里云、清华）**只提供 CPU 版** PyTorch。CUDA 版只存在于官方源或特定镜像。

### 可用镜像（速度快）
| 镜像 | URL | 内容 |
|---|---|---|
| 南大 NJU | `https://mirrors.nju.edu.cn/pytorch/whl/cu128` | CUDA 版 wheel |
| 北大 PKU | `https://mirrors.pku.edu.cn/pypi/simple` | 通用依赖 |
| 清华 conda | `https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main` | conda 包 |

### 推荐安装流程
```bash
# Stage 1: PyTorch CUDA 从南大镜像
pip install torch==2.7.1+cu128 torchaudio==2.7.1+cu128 \
  --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu128 \
  --extra-index-url https://mirrors.pku.edu.cn/pypi/simple

# Stage 2: 其余依赖
pip install -r requirements.txt -i https://mirrors.pku.edu.cn/pypi/simple
```

### 手动下载 wheel（当 pip 代理干扰时）
```bash
# 先用 curl 直连确认可达
curl --noproxy '*' -sI "https://download.pytorch.org/whl/cu128/torch/" | head -20

# 单个下载
curl --noproxy '*' -L -O "https://download.pytorch.org/whl/cu128/torch-2.8.0%2Bcu128-cp311-cp311-win_amd64.whl"
```

### 国内镜像全不提供 CUDA 版（已验证）
- 阿里云 `mirrors.aliyun.com/pypi/simple` → 只有 CPU 版（如 torch 2.13.0+cpu）
- 清华 `mirrors.tuna.tsinghua.edu.cn/pypi/web/simple` → 同样只有 CPU 版
- 清华 conda pytorch 频道 → 有 CUDA 版但依赖链复杂（需要 cuda-nvtx 等 nvidia 频道包）

## 二、Conda 创建环境

### 代理干扰
Clash 代理（127.0.0.1:7897）会干扰 conda/pip 的 HTTPS 请求，导致 SSL 错误。

```bash
# 创建环境前必须 unset 代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY

# 用清华单频道（不用系统多频道配置，避免被代理干扰）
conda create -n <env_name> python=3.11 \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main \
  -y --override-channels
```

### 已安装的 conda envs
- `py31111` — Python 3.11, CPU torch, 用于 grok build
- `gpt-sovits` — Python 3.11, torch 2.8.0+cu128, GPT-SoVITS
- `rvc` — Python 3.12, torch 2.7.1+cu128, RVC

## 三、Pip 权限问题

### "Defaulting to user installation because normal site-packages is not writeable"

pip 无法写入 conda 环境 site-packages 时的绕过方案：

```bash
SITE="C:/Users/53028/.conda/envs/<env>/Lib/site-packages"
pip install --target "$SITE" --ignore-installed -r requirements.txt
```

注意：`--target` 安装后需要设置 PYTHONPATH 才能正确导入：

```bash
export PYTHONPATH="C:/Users/53028/.conda/envs/<env>/Lib/site-packages"
```

## 四、子进程 PYTHONPATH 继承

WebUI 项目（Gradio）通过 `subprocess.Popen` 启子进程执行训练/预处理脚本时，子进程**不自动继承 PYTHONPATH**。

### 解决方案
启动 webui 时显式设置：

**CMD:**
```cmd
set PYTHONPATH=E:\<project>;C:\Users\53028\.conda\envs\<env>\Lib\site-packages
python webui.py
```

**bash:**
```bash
export PYTHONPATH="E:/<project>;C:/Users/53028/.conda/envs/<env>/Lib/site-packages"
python webui.py
```

注意 Windows 下 PYTHONPATH 用**分号**分隔，不是冒号。

### 子进程 `sys.path` 陷阱
当脚本位于子目录（如 `train/preprocess.py`）时，Python 把脚本所在目录加入 sys.path。如果该目录下存在同名 `.py` 文件（如 `train/train.py`），`import train` 会找到模块而非包，触发循环导入。

**修复**：在脚本开头插入项目根目录：
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

## 五、Gradio 依赖版本冲突

GPT-SoVITS 等 Gradio 项目常见版本冲突：

| 冲突 | 修复 |
|---|---|
| `jinja2` + `starlette` → `TypeError: unhashable type: 'dict'` | `pip install jinja2==3.1.4` |
| `MarkupSafe` + `gradio` → 不兼容 | `pip install markupsafe==2.1.5` |
| `starlette>=1.0` + `fastapi` → 模板错误 | `pip install "starlette<0.40"` |

## 六、验证清单

- [ ] `python -c "import torch; print(torch.cuda.is_available())"` → True
- [ ] `python webui.py` → 无 ModuleNotFoundError
- [ ] 子进程能正常启动（触发训练/预处理验证）
- [ ] `curl -s http://127.0.0.1:<port>` 返回 HTML
