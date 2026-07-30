---
name: python-ml-env-windows-china
description: Set up isolated conda environments for ML/Python projects on Windows behind GFW — mirror selection, proxy interference workarounds, pip --target for user site-packages conflicts, Gradio localhost fixes.
---

# Python ML Environment Setup on Windows (China Network)

Trigger when: creating conda environments, installing PyTorch CUDA / ML dependencies, fixing pip/conda proxy interference, or debugging Gradio webui startup on a Windows host behind GFW.

## 1. Conda Environment Creation

Always use a single domestic mirror with `--override-channels` and unset proxy vars:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
conda create -n <name> python=3.11 \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main \
  -y --override-channels
```

**Pitfall**: `conda config --show channels` may list multiple mirrors. When proxy is still interfering, multi-channel repodata fetches can trigger SSL failures on some channels while others succeed — use `--override-channels` to limit to one mirror.

## 2. PyTorch CUDA Installation

**Chinese pip mirrors (Aliyun, Tsinghua) only carry CPU-only PyTorch wheels.** For CUDA wheels, use NJU (Nanjing University) mirror which carries full CUDA wheel sets:

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
pip install torch==2.7.1+cu128 torchaudio==2.7.1+cu128 \
  --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu128 \
  --extra-index-url https://mirrors.pku.edu.cn/pypi/simple
```

Other working mirrors for CUDA PyTorch:
- `https://download.pytorch.org/whl/cu128` (official, often blocked/dog-slow without VPN)
- NJU mirror verified fast (~600KB/s for 3.3GB wheel)

**Pitfall**: `pip install torch --index-url https://download.pytorch.org/whl/cu128` through Clash proxy (127.0.0.1:7897) intermittently fails with `ProxyError (10054)` or `SSLEOFError`. Clash rules for pytorch.org are unreliable. Use NJU mirror or direct connection (slow but stable at ~230KB/s).

**Pitfall**: `conda install pytorch pytorch-cuda=12.8 -c pytorch` from tsinghua mirror fails with missing `cuda-nvtx` dependency chain. Avoid conda for PyTorch CUDA; use pip.

## 3. Regular Python Dependencies

Preferred mirrors for pip (all verified working without proxy):
- PKU: `https://mirrors.pku.edu.cn/pypi/simple`
- Aliyun: `https://mirrors.aliyun.com/pypi/simple`
- Tsinghua pip: `https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple` (CPU-only torch)

Some projects (like RVC) embed mirror URLs in their requirements files — prefer those.

## 4. Proxy Interference Pattern

When commands fail with `ProxyError`, `SSLEOFError`, or `ConnectionResetError` even after `unset`:

1. **Conda**: The `unset` in the same command line before `source` may be re-set by conda activation scripts. Place `unset` AFTER `conda activate`.
2. **Pip**: Python's `urllib.request.getproxies()` reads Windows system proxy settings, bypassing shell env vars. Use `--proxy "" --no-proxy "*"` or unset + use domestic mirrors.
3. **Git**: `git -c http.proxy="" -c https.proxy="" clone` to bypass global proxy config.
4. **Curl**: `curl --noproxy '*'` for direct, `curl -x http://127.0.0.1:7897` for proxied.

## 5. User Site-Packages Conflicts (`pip --target`)

On Windows, pip may default to `C:\Users\<user>\AppData\Roaming\Python\Python3XX\site-packages` instead of the conda env's `Lib/site-packages`, printing `"Defaulting to user installation because normal site-packages is not writeable"`.

**Fix**: Use `--target` to force installation into the conda env:

```bash
SITE="C:/Users/<user>/.conda/envs/<name>/Lib/site-packages"
pip install --target "$SITE" --ignore-installed -r requirements.txt
```

Then set `PYTHONPATH` at runtime so Python prioritizes the conda env:
```bash
export PYTHONPATH="C:/Users/<user>/.conda/envs/<name>/Lib/site-packages"
```

Related: `setuptools` from the Hermes agent venv (`C:\Users\<user>\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages`) can shadow the conda env's setuptools, causing `AttributeError: module 'pkgutil' has no attribute 'ImpImporter'` when building wheels for Python 3.12. Fix by installing setuptools to the env's target first:
```bash
pip install --target "$SITE" setuptools==75.8.0 wheel packaging
```

## 6. Gradio WebUI Startup Issues

**jinja2 `unhashable type: 'dict'` error**: Caused by starlette >= 1.0 + jinja2 incompatibility. Downgrade:
```bash
pip install "starlette<0.40"
```

**"When localhost is not accessible"**: Gradio can't reach its own localhost due to proxy settings. Fix:
```bash
export NO_PROXY="localhost,127.0.0.1,::1"
```

**Missing SSL_CERT_FILE**: Conda may set `SSL_CERT_FILE` to a non-existent path. Unset it:
```bash
unset SSL_CERT_FILE
```

## 7. Full Startup Recipe

```bash
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY SSL_CERT_FILE
export NO_PROXY="localhost,127.0.0.1,::1"
export PYTHONPATH="C:/Users/<user>/.conda/envs/<name>/Lib/site-packages"
source /c/ProgramData/anaconda3/etc/profile.d/conda.sh
conda activate <name>
cd /e/<project>
python webui.py
```

## 9. Hermes PYTHONPATH Pollution

Hermes Agent sets a global `PYTHONPATH` pointing to its own venv (`C:\Users\<user>\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages`). This contaminates **every** Python process launched through the terminal:

- `pip install` targets the Hermes venv instead of your conda env
- `import` resolution finds Hermes' stale packages (pydantic, PIL, yaml) before your env's
- New venvs inherit this path, causing cross-contamination

**Fix**: Always prefix non-Hermes Python commands with `unset PYTHONPATH &&`:

```bash
# WRONG — installs into hermes venv, or breaks with pydantic/PIL conflicts
python -m pip install some-package

# RIGHT
unset PYTHONPATH && python -m pip install some-package

# RIGHT — run a script in a clean venv
unset PYTHONPATH && /path/to/venv/Scripts/python script.py
```

**Detection**: If you see `ImportError` for pydantic/pydantic_core or PIL from a path containing `hermes-agent`, PYTHONPATH is the culprit.

**Note**: `os.environ['PYTHONPATH'] = ''` inside a script is too late — the polluted sys.path was already baked in at interpreter startup. Must be cleared BEFORE the Python process starts.

## 10. Anaconda Qt5 DLL Pollution with PyQt6 / Qt6 Apps

**Symptom**: `from PyQt6.QtCore import QT_VERSION_STR` fails with `ImportError: DLL load failed while importing QtCore: 找不到指定的程序。` — even when `PyQt6` and `PyQt6-Qt6` are correctly installed in the venv and `os.add_dll_directory(qt6_bin)` is called.

**Root cause**: Anaconda ships its own Qt5 DLLs at `C:\ProgramData\anaconda3\Lib\site-packages\PyQt5\Qt5\bin\`. These are in the Anaconda Python's DLL search order and load BEFORE Qt6 DLLs. Qt5 and Qt6 DLLs are binary-incompatible — mixing them causes WinError 127.

**Why export PATH / os.add_dll_directory don't help**: The Anaconda Python interpreter itself has a baked-in DLL search that picks up Qt5 before Qt6. Even `uv sync` will pick Anaconda Python if it's the only 3.11 on the system (`Using CPython 3.11.7 interpreter at: C:\ProgramData\anaconda3\python.exe`).

**Fix — uv standalone Python** (cleanest, recommended):

```bash
# 1. Install a standalone Python managed by uv (NOT Anaconda)
uv python install 3.11

# 2. Rebuild venv pointing to standalone Python
cd <project>
rm -rf .venv
uv sync --extra dev --python 3.11.15

# 3. Now Qt6 imports cleanly
uv run python -c "from PyQt6.QtCore import QT_VERSION_STR; print(QT_VERSION_STR)"
```

**Verification**: The uv standalone Python lives at `~/.local/share/uv/python/cpython-3.11.X-.../` — check with `uv run python -c "import sys; print(sys.executable)"`. It should NOT contain `anaconda3` in the path.

**Alternative — conda install PyQt6**: `conda install -c conda-forge pyqt` handles Qt runtime dependencies correctly. But this may install PyQt5 not PyQt6; check `conda search pyqt` first. Pip-installed PyQt6 wheels assume a clean Windows environment without Anaconda Qt5 pollution.

**When to suspect this**: Any `ImportError: DLL load failed` involving Qt, especially on machines that have Anaconda AND a pip/uv-installed Qt6 project. Test Qt5 first: `python -c "from PyQt5.QtCore import *; print('works')"` — if Qt5 works but Qt6 doesn't, this is the cause.

## 11. Independent Venv for Tools (Avoid Dependency Hell)

When installing a new tool that has conflicting dependencies with rvc/gpt-sovits/cosyvoice environments, create a clean standalone venv:

```bash
# Use system Python, NOT conda env Python
/d/python3.10.6/python -m venv C:/Users/<user>/tool_venv

# Install with PYTHONPATH cleared
unset PYTHONPATH && C:/Users/<user>/tool_venv/Scripts/python -m pip install <package> \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
```

This avoids the cascading dependency conflicts (pydantic v1 vs v2, protobuf version mismatches, yaml file locks) that plague the shared conda environments.

See [`references/gpt-sovits-rvc-recipes.md`](references/gpt-sovits-rvc-recipes.md) for full GPT-SoVITS and RVC setup on this machine — dependency quirks, exact version pinning, model download status.
