---
name: rvc-setup
description: 在 Windows + conda 上完整搭建 RVC (Retrieval-based Voice Conversion)，包括环境、依赖、模型下载、Bug 修复、训练和推理。
triggers:
  - "装 RVC"
  - "搭建 RVC"
  - "RVC 训练"
  - "翻唱/变声 环境"
  - "AI 翻唱"
---

# RVC 完整搭建（Windows + conda）

## 环境

```cmd
conda create -n rvc python=3.12 -y
conda activate rvc
```

## 安装步骤

```cmd
# 1. 克隆代码
git clone https://github.com/RVC-Boss/Retrieval-based-Voice-Conversion-WebUI.git E:\RVC
cd E:\RVC

# 2. PyTorch CUDA 12.8（南大镜像，国内快）
pip install torch==2.7.1+cu128 torchaudio==2.7.1+cu128 \
  --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu128 \
  --extra-index-url https://mirrors.pku.edu.cn/pypi/simple

# 3. 项目依赖
pip install -r requirments_cu128_py312.txt
```

## 必下模型

浏览器开 VPN 访问 https://hf-mirror.com/lj1995/VoiceConversionWebUI/tree/main

| 下载 | 放置路径 |
|---|---|
| `hubert_base/config.json` | `assets/hubert_base/config.json` |
| `hubert_base/pytorch_model.bin` | `assets/hubert_base/pytorch_model.bin` |
| `hubert_base/preprocessor_config.json` | `assets/hubert_base/preprocessor_config.json` |
| `rmvpe.pt` | `assets/rmvpe/rmvpe.pt` |
| `pretrained_v2/` 下全部 `.pth` | `assets/pretrained_v2/` |

⚠️ HuBERT 需要 Transformers 格式（config.json + pytorch_model.bin），不是单文件 `.pt`。

## 关键 Bug 修复

### 1. 循环导入（三个文件都要修）

子进程 `python train/xxx.py` 运行时，Python 把 `train/` 放入 sys.path，导致 `import train` 找到 `train/train.py` 而非包。在每个脚本开头插入：

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

需修复的文件：
- `train/preprocess.py` — 在 `os.environ["RVC_AUDIO_FORCE_CPU"]` 前
- `train/train.py` — 在 `import logging` 前
- `train/train_index.py` — 在 `import traceback` 前

### 2. 启动必须带 PYTHONPATH

```cmd
set PYTHONPATH=E:\RVC;C:\Users\<用户名>\.conda\envs\rvc\Lib\site-packages
python webui.py
```

否则子进程找不到 `i18n`/`infer` 等模块。

### 3. 训练缺 mute 文件

训练时需要静音参考文件。缺了会报 `FileNotFoundError: mute40k.wav`（或 mute48k）：

```python
import numpy as np, soundfile as sf
sr = 48000  # 根据采样率调整
sf.write('E:/RVC/logs/mute/0_gt_wavs/mute48k.wav', np.zeros(sr, dtype=np.float32), sr)
np.save('E:/RVC/logs/mute/3_feature768/mute.npy', np.zeros((1, 768), dtype=np.float32))
np.save('E:/RVC/logs/mute/2a_f0/mute.wav.npy', np.zeros((1,), dtype=np.float32))
np.save('E:/RVC/logs/mute/2b-f0nsf/mute.wav.npy', np.zeros((1,), dtype=np.float32))
```

### 4. F0 提取大量静音片段

`音高全部为0，该音频无意义，跳过` — 正常现象，RVC 自动跳过呼吸/空白片段。

## 训练流程

1. WebUI 打开 http://127.0.0.1:7865
2. **实验名**：填一个名字
3. **目标采样率**：推荐 48k
4. **F0 提取方法**：rmvpe（比 pm 准，尤其低质量音频）
5. 点击 **一键训练**

### 训练参数建议

| 数据量 | batch_size | 总训练轮数 |
|---|---|---|
| 10 分钟 | 4 | 400-500 |
| 1 小时 | 2（防爆显存） | 150-200 |

## 推理/拷走模型

训练完成后拷走两个文件：
- `assets/weights/实验名.pth`（~55MB）
- `assets/indices/实验名_added_*.index`（~600MB）

推理：WebUI 推理标签页 → 选模型 → 丢干声 → 输出。
