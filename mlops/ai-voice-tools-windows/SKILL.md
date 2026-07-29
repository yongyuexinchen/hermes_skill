---
name: ai-voice-tools-windows
description: Install, configure, and debug RVC, GPT-SoVITS, and similar AI voice/singing tools on Windows with Chinese network constraints.
---

# AI Voice Tools on Windows

## Quick Bootstrap (RVC)

```cmd
conda create -n rvc python=3.12 -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main -y --override-channels
conda activate rvc
git clone https://github.com/RVC-Boss/Retrieval-based-Voice-Conversion-WebUI.git E:\RVC
cd E:\RVC
pip install torch==2.7.1+cu128 torchaudio==2.7.1+cu128 --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu128 --extra-index-url https://mirrors.pku.edu.cn/pypi/simple
pip install -r requirments_cu128_py312.txt
```

## Quick Bootstrap (GPT-SoVITS)

Use `py31111` conda env or create Python 3.10:
```cmd
conda create -n gpt-sovits python=3.10 -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main -y --override-channels
```

## Critical Fixes

### Circular Import in RVC subprocesses

`python train/preprocess.py` and `python train/train.py` fail because the script directory shadows the package name. Fix both files:

**train/preprocess.py** — add before `from infer.audio import load_audio`:
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**train/train.py** — add after `import os`:
```python
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Subprocess PYTHONPATH

When spawning subprocesses, set PYTHONPATH to include the project root:
```cmd
set PYTHONPATH=E:\RVC;C:\Users\<user>\.conda\envs\rvc\Lib\site-packages
python webui.py
```

### jinja2/starlette version conflict (GPT-SoVITS)

```cmd
pip install jinja2==3.1.4 markupsafe==2.1.5
```

## Model Downloads (Chinese Network)

### PyTorch CUDA — use domestic mirrors

Never use `download.pytorch.org` directly (SSL/GFW interference). Use:
- NJU mirror: `https://mirrors.nju.edu.cn/pytorch/whl/cu128`
- PKU mirror for deps: `https://mirrors.pku.edu.cn/pypi/simple`

### HuggingFace models — always via hf-mirror.com

https://hf-mirror.com/lj1995/VoiceConversionWebUI/tree/main

The proxy (`127.0.0.1:7897`, Clash Verge) causes intermittent SSL failures for HF domains. Download via browser with VPN, never try curl/pip direct.

### ModelScope for Alibaba models

CosyVoice, FunASR models: use `snapshot_download('iic/xxx', cache_dir=...)`. Works without proxy.

## RVC Training

### Mute reference file

RVC inserts `mute` entries into filelist. Must create a silent WAV at the matching sample rate:

```python
import numpy as np, soundfile as sf
sr = 48000  # match training sample rate
sf.write('E:/RVC/logs/mute/0_gt_wavs/mute48k.wav', np.zeros(sr, dtype=np.float32), sr)
```

Also create dummy `.npy` files for F0/HuBERT features in the mute directory.

### Batch size for long audio

- 10 min: batch_size=4
- 1 hour: batch_size=2 (4060 8GB VRAM limit)

### Epochs by data size

- 10 min dry vocals: 400-500 epochs
- 1 hour dry vocals: 150-200 epochs

### Prevent sleep during training

```cmd
powercfg -change -standby-timeout-ac 0
```

## Pitfalls

- **Never HTTPS-clone GitHub repos when proxy is flaky**: use gitee mirrors or ModelScope `snapshot_download`
- **ModelScope model IDs are not the same as HF**: verify with `modelscope.cn` search first
- **PowerShell encoding**: Chinese log files render as garbled unless `-Encoding UTF8` on `Get-Content`
- **CMD vs PowerShell**: use CMD for conda envs; `set VAR=value` in CMD, `$env:VAR="value"` in PS
- **`tail` not available in CMD**: use `Get-Content file -Tail N` in PowerShell, or Python one-liner
