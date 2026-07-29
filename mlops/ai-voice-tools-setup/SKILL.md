---
name: ai-voice-tools-setup
description: Set up and debug AI voice tools (RVC, GPT-SoVITS, CosyVoice) on Windows with conda — mirror strategy, PyTorch CUDA, circular import fixes, PYTHONPATH, model downloads.
---

# AI Voice Tools Setup (RVC / GPT-SoVITS / CosyVoice)

## Triggers

- Setting up RVC, GPT-SoVITS, CosyVoice, Seed-VC, or similar AI voice tools
- "下载 RVC / GPT-SoVITS / CosyVoice"
- Circular import errors in train.py / preprocess.py subprocesses
- Missing models causing subprocess failures
- conda env creation + PyTorch CUDA install for voice tools

## Environment Strategy

### Conda Environment

```bash
# Always use --override-channels with a single Chinese mirror to avoid proxy interference
conda create -n <name> python=<version> \
  -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main -y --override-channels
```

### PyTorch CUDA — Chinese Mirror Priority

**Official PyTorch index is unreliable via proxy (SSL errors). Chinese mirrors preferred:**

| Mirror | URL | Notes |
|---|---|---|
| NJU (南大) | `https://mirrors.nju.edu.cn/pytorch/whl/cu128` | ✅ CUDA wheels, but hash sometimes mismatches |
| PKU (北大) | `https://mirrors.pku.edu.cn/pypi/simple` | For pip deps, not CUDA torch |
| Aliyun | `https://mirrors.aliyun.com/pypi/simple` | ❌ CPU-only torch |
| Tsinghua | `https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple` | ❌ CPU-only torch |

**If NJU hash fails:** fall back to `pip install --no-cache-dir torch==X.X.X+cuXXX --index-url https://download.pytorch.org/whl/cuXXX` (direct, slower but works when VPN is on).

### Dependencies — Avoid user site-packages conflict

When `pip install` defaults to `C:\Users\...\AppData\Roaming\Python\...` instead of conda env:

```bash
SITE="C:/Users/53028/.conda/envs/<name>/Lib/site-packages"
pip install --target "$SITE" --ignore-installed -r requirements.txt
```

Then always launch with:
```bash
export PYTHONPATH="C:/Users/53028/.conda/envs/<name>/Lib/site-packages;<project_root>"
```

## Pitfalls & Fixes

### Circular Import in train/train.py or preprocess.py

**Symptom:** `ImportError: cannot import name 'utils' from partially initialized module 'train'` when running as subprocess.

**Root cause:** `python train/preprocess.py` puts `train/` on `sys.path[0]`. Subsequent `from train.dataset.slicer2 import X` finds `train/train.py` as `train` module instead of the `train/` package.

**Fix:** Add at top of the script (after `import os, sys`):

```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

Apply to: `train/preprocess.py`, `train/train.py`, and any other script in `train/` that runs as a subprocess.

### Mute Reference File Missing

**Symptom:** `FileNotFoundError: .../logs/mute/0_gt_wavs/mute40k.wav` (or mute48k.wav)

**Fix:** Generate silence files:
```python
import numpy as np, soundfile as sf
sr = 40000  # or 48000
sf.write('E:/RVC/logs/mute/0_gt_wavs/mute{}.wav'.format(sr//1000), np.zeros(sr, dtype=np.float32), sr)
# Also create empty .npy files for feature/f0 dirs
```

### PYTHONPATH Not Inherited by Subprocess

**Symptom:** `ModuleNotFoundError: No module named 'infer'` or `'i18n'` in subprocess only.

**Fix:** Always export PYTHONPATH before `python webui.py`:
```bash
export PYTHONPATH="<conda_site_packages>;<project_root>"
export NO_PROXY="localhost,127.0.0.1,::1"
```

### HuBERT Model Format Mismatch

**Symptom:** `FileNotFoundError: Transformers HuBERT model not found: .../hubert_base` even though `hubert_base.pt` exists.

**Root cause:** RVC v2Pro+ uses Transformers format (needs `config.json` + `pytorch_model.bin`), not the single `.pt` file.

**Fix:** Download from hf-mirror.com: `hubert_base/config.json`, `hubert_base/preprocessor_config.json`, `hubert_base/pytorch_model.bin`.

## Model Download Strategy

1. **ModelScope** (preferred, fast in China):
   ```python
   from modelscope import snapshot_download
   snapshot_download('repo/id', cache_dir='E:/target')
   ```

2. **hf-mirror.com** (browser manual download):
   `https://hf-mirror.com/<user>/<repo>/tree/main`

3. **GitHub clone via gitee mirror** when GitHub is blocked:
   `git clone https://gitee.com/mirrors/<repo>.git`

## Voice Tool Comparison

| Tool | Type | Best For |
|---|---|---|
| **RVC** | Voice Conversion | AI翻唱、变声、音色迁移 |
| **GPT-SoVITS** | TTS + Singing | 文字→歌声、零样本语音合成 |
| **CosyVoice 3** | TTS | 多语种零样本朗读、有声书 |
| **Seed-VC** | Voice Conversion | 零样本翻唱（不训练） |
