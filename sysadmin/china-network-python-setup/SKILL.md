---
name: china-network-python-setup
description: Create conda environments, install PyTorch/CUDA packages, and manage pip dependencies when operating behind China's GFW with a flaky proxy (Clash). Covers mirror selection, wheel download strategies, and the --target workaround for site-packages permission issues.
---

# China-Network Python Environment Setup

## When to Use

Trigger when:
- Creating conda environments or installing pip packages from behind China's GFW
- Proxy (Clash/Mihomo on 127.0.0.1:7897) causes SSL failures, ConnectionResetError, or ProxyError
- Need CUDA-enabled PyTorch (not CPU-only from Chinese mirrors)
- `pip install` reports "Defaulting to user installation because normal site-packages is not writeable"
- Gradio/Starlette/Jinja2 version conflicts at startup

## Quick Start: The Proven Pattern

```bash
# 1. Create conda env — use Tsinghua mirror ONLY, unset proxy
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
conda create -n <env-name> python=<version> \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main \
  -y --override-channels

# 2. For CUDA PyTorch: download wheel from official source, then install locally
#    (Chinese mirrors only carry CPU versions)
curl --noproxy '*' -L -O "https://download.pytorch.org/whl/cu128/torch-2.8.0%2Bcu128-cp311-cp311-win_amd64.whl"

# 3. Install wheel — use --target if site-packages has permission issues
SITE="C:/Users/<user>/.conda/envs/<env-name>/Lib/site-packages"
pip install --target "$SITE" --force-reinstall --no-deps <wheel-file>.whl

# 4. Install remaining dependencies — also via --target
pip install --target "$SITE" --ignore-installed -r requirements.txt

# 5. Launch with PYTHONPATH
PYTHONPATH="$SITE" python app.py
```

## Pitfalls

### Pitfall 1: conda SSL failures with multiple channels
Conda's default config may have 10+ mirror channels. When proxy is flaky, each channel triggers SSL retries, causing 2+ minute delays and eventual failure.
**Fix**: Use `--override-channels` with a single reliable channel (Tsinghua main).

### Pitfall 2: Chinese pip mirrors have NO CUDA PyTorch
Both `mirrors.aliyun.com` and `mirrors.tuna.tsinghua.edu.cn` only carry CPU versions of torch (122MB vs 3.3GB CUDA version).
**Fix**: Download CUDA wheels from `download.pytorch.org/whl/cu128/` directly (curl `--noproxy '*'`), then `pip install` the local file.

### Pitfall 3: "site-packages is not writeable" + user-site conflict
When pip installs to `%APPDATA%/Python/Python3XX/site-packages` instead of the conda env, two problems arise:
- Permission conflicts (files locked by other processes like Hermes)
- Version conflicts (old packages from user-site override conda env packages)
**Fix**: Always use `pip install --target <conda-env-site-packages>` and launch with `PYTHONPATH` set.

### Pitfall 4: Python version must match wheel cp tag
A `cp311` wheel will fail with "not a supported wheel on this platform" on Python 3.10.
**Fix**: Match Python version in conda env to the wheel you have, or download the correct cp tag.

### Pitfall 5: jinja2 3.1.6 + starlette 1.3.x incompatibility
Causes `TypeError: unhashable type: 'dict'` in Gradio template rendering.
**Fix**: Pin `jinja2==3.1.4`.

### Pitfall 6: SSL_CERT_FILE pointing to non-existent path
Conda may set `SSL_CERT_FILE` to a path that doesn't exist (especially after `--override-channels`).
**Fix**: `unset SSL_CERT_FILE` before running Python.

## Mirror Reference

| Source | Packages | Needs Proxy? |
|--------|----------|--------------|
| Tsinghua conda (`mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main`) | Base Python | No (unset proxy) |
| Aliyun pip (`mirrors.aliyun.com/pypi/simple`) | Most PyPI packages | No |
| PyTorch official (`download.pytorch.org/whl/cu128`) | CUDA torch ONLY | Yes (proxy required, ~10MB/s) or direct (slow, ~230KB/s) |
| HuggingFace (`huggingface.co`) | Pretrained models | Proxy hits SSL failures; use modelscope mirrors |

## GPT-SoVITS Specific Notes

- Requires Python 3.10 or 3.11 (README tested matrix)
- Requires CUDA PyTorch (not CPU)
- Pretrained models (v2Pro): ~2GB from HuggingFace → use modelscope mirror or manual download
- Requires FFmpeg in PATH
- Gradio WebUI on port 9874 by default
- The `go-webui.bat` launcher works for integrated packages, not source installs
