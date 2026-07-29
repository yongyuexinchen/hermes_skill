---
name: china-ml-env-setup
description: Conda/pip/PyTorch 环境搭建 — 国内镜像、代理绕过、常见坑
---

# 国内 ML 环境搭建

## 触发条件

用户在 China 网络下需要：
- 创建 conda 环境并安装 PyTorch/ML 依赖
- pip 下载慢或被墙
- 代理（Clash/VPN）导致 SSL 错误

## 镜像速查

| 用途 | 镜像 |
|---|---|
| pip（首选） | `https://mirrors.aliyun.com/pypi/simple` |
| pip（备选） | `https://mirrors.pku.edu.cn/pypi/simple` |
| pip（清华） | `https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple` |
| PyTorch CUDA wheel（仅有） | `https://mirrors.nju.edu.cn/pytorch/whl/cu128` |
| conda channel（清华） | `https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main` |

## 核心流程

### 1. 创建 conda 环境（关代理、单频道）

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
conda create -n <name> python=3.11 \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main \
  -y --override-channels
```

**为什么**：conda 多频道并发请求时，Clash 代理容易触发 ConnectionResetError(10054)。单频道 + 关代理最稳。

### 2. 装 PyTorch CUDA 版

国内 pip 镜像（阿里/清华/北大）**只提供 CPU 版** PyTorch。CUDA 版有两种方式：

**方式 A：南大镜像（直连，快）**
```bash
unset http_proxy https_proxy
pip install torch==2.7.1+cu128 torchaudio==2.7.1+cu128 \
  --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu128 \
  --extra-index-url https://mirrors.pku.edu.cn/pypi/simple
```

**方式 B：conda 清华频道**
```bash
conda search pytorch -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch --override-channels
# 选带 cuda 的 build，如 py3.10_cuda12.4_cudnn9_0
conda install pytorch=2.5.1=py3.10_cuda12.4_cudnn9_0 torchaudio \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main \
  -y --override-channels
```

注意 conda 方式可能缺 `cuda-nvtx` 等依赖包。pip + 南大镜像更可靠。

### 3. 装项目依赖

```bash
unset http_proxy https_proxy
pip install -r requirements.txt  # 默认走阿里云镜像
```

## 常见坑

### pip 装到用户目录而非 conda 环境

现象：`Defaulting to user installation because normal site-packages is not writeable`

解决：用 `--target` 强指 conda 环境路径：
```bash
SITE=$(python -c "import site; print(site.getsitepackages()[1])")
pip install --target "$SITE" --ignore-installed -r requirements.txt
```

### 代理导致 pip/conda SSL 失败

现象：`ProxyError`、`SSLEOFError`、`ConnectionResetError(10054)`

三步走：
1. `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY` — 清环境变量
2. 换国内镜像（不走代理）
3. 如果必须走代理，确认 Clash 端口在线：`curl -s --connect-timeout 3 http://127.0.0.1:7897`

### Python 子进程循环导入（Windows）

现象：子进程跑脚本时 `ImportError: circular import`

根因：脚本目录被 Python 加入 sys.path，导致同目录的 `.py` 文件被当成包加载（如 `train/train.py` 被误加载为 `import train`）。

修复：在脚本最顶部插入项目根目录：
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### HuggingFace 下载

直连和代理都常 SSL 失败。用 hf-mirror：
```
https://hf-mirror.com/<user>/<repo>/resolve/main/<filepath>
```
但 curl/Python 也可能失败，最终可靠方案是用户浏览器 + VPN 手动下载。

### jinja2 + starlette 版本冲突

Gradio 4.x + starlette 1.x + jinja2 3.1.6 → `unhashable type: 'dict'`

修复：降 starlette + 固定 jinja2/MarkupSafe：
```bash
pip install jinja2==3.1.4 markupsafe==2.1.5 "starlette<0.40"
```

## 参考

- `references/rvc-gptsovits-quirks.md` — RVC / GPT-SoVITS 安装坑（模型下载、循环导入修复、mute 文件）
