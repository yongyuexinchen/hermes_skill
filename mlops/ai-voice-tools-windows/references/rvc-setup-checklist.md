# RVC Complete Setup Checklist

Session: 2026-07-24, Windows 10, RTX 4060 8GB, conda, Chinese network

## 1. Clone + Env
- [x] `conda create -n rvc python=3.12 -c tsinghua`
- [x] `git clone RVC-Boss/Retrieval-based-Voice-Conversion-WebUI E:\RVC`
- [x] `pip install torch==2.7.1+cu128 torchaudio==2.7.1+cu128 -i nju`
- [x] `pip install -r requirments_cu128_py312.txt`

## 2. Bugfixes (critical — training fails without)
- [x] `train/preprocess.py`: add `sys.path.insert` before line 20
- [x] `train/train.py`: add `sys.path.insert` after `import os`
- [x] `train/__init__.py` and `train/dataset/__init__.py`: create empty files

## 3. Models (browser download from hf-mirror.com)
- [x] `hubert_base/config.json` → `assets/hubert_base/`
- [x] `hubert_base/preprocessor_config.json` → `assets/hubert_base/`
- [x] `hubert_base/pytorch_model.bin` → `assets/hubert_base/`
- [x] `hubert_base.pt` → `assets/hubert_base/` (optional, old format)
- [x] `rmvpe.pt` → `assets/rmvpe/`
- [x] `pretrained_v2/*.pth` (12 files) → `assets/pretrained_v2/`

## 4. Mute Reference
- [x] Create `logs/mute/0_gt_wavs/mute48k.wav` (1 sec silence at training SR)
- [x] Create `logs/mute/3_feature768/mute.npy` (zeros, shape (1,768))
- [x] Create `logs/mute/2a_f0/mute.wav.npy` (zeros)
- [x] Create `logs/mute/2b-f0nsf/mute.wav.npy` (zeros)

## 5. Launch
```cmd
set PYTHONPATH=E:\RVC;C:\Users\53028\.conda\envs\rvc\Lib\site-packages
set NO_PROXY=localhost,127.0.0.1,::1
python webui.py
```

## 6. Training Config (1 hour dry vocals, RTX 4060)
- batch_size: 2
- epochs: 200
- save_every_epoch: 5
- F0 method: rmvpe
- sample rate: 48k (or 40k)
- "仅保存最新": Yes (save disk space)

## Known Issues Fixed
1. Circular import: `from train import utils` → `sys.path.insert` fix
2. FileNotFoundError mute48k.wav → created mute directory and files
3. jinja2/starlette conflict → downgrade jinja2 to 3.1.4
4. Subprocess PYTHONPATH → set in launch command
5. HF download SSL failures → browser + hf-mirror.com
