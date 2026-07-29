---
name: windows-python-ml-setup
description: Setup Python ML environments (PyTorch CUDA, conda, pip) on Windows with China network constraints — proxy interference, mirror availability, wheel compatibility.
---

# Windows Python ML Environment Setup (China Network)

Setting up Python ML environments on Windows behind the Great Firewall with Clash proxy.

## Triggers

- Installing PyTorch (especially CUDA version) on Windows
- Setting up conda environments with network issues
- "site-packages is not writeable" errors from pip
- Chinese PyPI mirrors (Aliyun, Tsinghua) only returning CPU wheels
- Proxy (Clash/127.0.0.1:7897) interfering with pip/conda downloads

## Core Principles

1. **Chinese PyPI mirrors only carry CPU PyTorch.** CUDA wheels are exclusive to `download.pytorch.org`.
2. **Proxy (Clash) is unreliable** for conda/pip — use `unset` + direct connections or `--override-channels` with Tsinghua.
3. **Direct download is slow but stable.** `curl --noproxy '*'` for pytorch.org works; proxy causes SSL failures intermittently.
4. **Always create fresh conda environments.** Mixing with existing user-level packages causes version chaos.

## Conda Environment Creation

```bash
# Unset proxy, use Tsinghua single channel — fast and reliable
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
source /c/ProgramData/anaconda3/etc/profile.d/conda.sh
conda create -n <env_name> python=3.11 \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main \
  -y --override-channels
```

Multi-channel configs trigger proxy-related SSL failures. Single channel + `--override-channels` avoids this.

## PyTorch CUDA Installation

### Option A: Download wheel, install locally (recommended)

```bash
# 1. Find the right wheel on download.pytorch.org
curl --noproxy '*' -s "https://download.pytorch.org/whl/cu128/torch/" \
  | grep -oP 'torch-[^"]*cp3XX[^"]*win_amd64[^"]*\.whl'

# 2. Download (direct, no proxy — ~230KB/s, 2.7GB = ~3.5h)
curl --noproxy '*' -L -O "https://download.pytorch.org/whl/cu128/torch-X.Y.Z%2Bcu128-cp3XX-cp3XX-win_amd64.whl"

# 3. Fix URL-encoded '+' in filename
mv "torch-X.Y.Z%2Bcu128..." "torch-X.Y.Z+cu128..."

# 4. Install (use --target if "site-packages not writeable")
SITE=$(python -c "import site; print(site.getsitepackages()[1])")
pip install --target "$SITE" --force-reinstall --no-deps torch-X.Y.Z+cu128-cp3XX-cp3XX-win_amd64.whl
```

### Option B: pip from official index (proxy must be healthy)

Only works when proxy is stable. Index URL `https://download.pytorch.org/whl/cu128` requires proxy to complete SSL handshake — fails intermittently with `SSLEOFError`.

## "site-packages is not writeable" Fix

When pip says this, it installs to user-level `AppData/Roaming/Python/` instead of conda env. Fix:

```bash
SITE=$(python -c "import site; print(site.getsitepackages()[1])")
pip install --target "$SITE" --ignore-installed -r requirements.txt
```

Then ensure `PYTHONPATH` is set when running:
```bash
export PYTHONPATH="$SITE"
python webui.py
```

## Gradio Compatibility Fixes

Gradio 4.x on conda environments often hits these version conflicts:

| Problem | Fix |
|---|---|
| `TypeError: unhashable type: 'dict'` in jinja2 cache | `pip install jinja2==3.1.4 markupsafe==2.1.5` |
| `starlette>=0.46` breaks gradio templates | `pip install "starlette<0.40"` |
| `cannot import name 'HfFolder'` | PYTHONPATH must prioritize conda env over user site-packages |

## Pitfalls

- **Don't mix conda environments.** User site-packages (`AppData/Roaming/Python/`) leak into imports even when conda env is active. Use `--target` or `PYTHONPATH`.
- **curl URL encoding.** `%2B` in filenames from download.pytorch.org must be renamed to `+` before pip install.
- **ssl/cacert.pem missing.** Conda envs may set `SSL_CERT_FILE` to a non-existent path. `unset SSL_CERT_FILE` before running gradio apps.
- **`no_proxy` for localhost.** Gradio's launch check needs `NO_PROXY="localhost,127.0.0.1,::1"` or it fails with "localhost not accessible".
- **User corrected: don't context-switch mid-task.** When given a specific task (e.g., GPT-SoVITS setup), stay on it. Don't veer off to fix unrelated Python code even if the user mentions it.

## Verification

```bash
source /c/ProgramData/anaconda3/etc/profile.d/conda.sh
conda activate <env_name>
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}')"
```
