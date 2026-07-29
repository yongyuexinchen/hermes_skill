# RVC (Retrieval-based Voice Conversion) Windows 搭建实录

## 环境需求
- Python 3.12
- PyTorch 2.7.1+cu128 (CUDA 12.8)
- 南大+北大镜像链

## 关键修复清单

### 1. 循环导入 (train/train.py + train/preprocess.py)
**症状**: 子进程报 `ImportError: cannot import name 'utils' from partially initialized module 'train'`

**根因**: 子进程运行 `train/preprocess.py` 或 `train/train.py` 时，Python 把 `train/` 加入 sys.path，`import train` 找到 `train/train.py` 而非包。

**修复**: 在两个文件开头（import os 之后）插入：
```python
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

**失败方案**: `from train import utils` → `from . import utils` — 相对导入在子进程中报 `attempted relative import with no known parent package`

### 2. 缺失 __init__.py
```bash
touch E:/RVC/train/__init__.py
touch E:/RVC/train/dataset/__init__.py
```

### 3. 静音参考文件 (mute)
训练需要 `E:\RVC\logs\mute/` 目录下的静音参考文件。RVC 自动插入 filelist，但文件需要在用户重跑训练前创建：

```python
import numpy as np, soundfile as sf
for sr, name in [(40000, 'mute40k.wav'), (48000, 'mute48k.wav')]:
    sf.write(f'E:/RVC/logs/mute/0_gt_wavs/{name}', np.zeros(sr, dtype=np.float32), sr)
np.save('E:/RVC/logs/mute/3_feature768/mute.npy', np.zeros((1, 768), dtype=np.float32))
np.save('E:/RVC/logs/mute/2a_f0/mute.wav.npy', np.zeros((1,), dtype=np.float32))
np.save('E:/RVC/logs/mute/2b-f0nsf/mute.wav.npy', np.zeros((1,), dtype=np.float32))
```

### 4. 模型文件清单
从 https://hf-mirror.com/lj1995/VoiceConversionWebUI 下载：

**推理必须:**
| 文件 | 路径 |
|---|---|
| `hubert_base/config.json` | `assets/hubert_base/config.json` |
| `hubert_base/preprocessor_config.json` | `assets/hubert_base/preprocessor_config.json` |
| `hubert_base/pytorch_model.bin` | `assets/hubert_base/pytorch_model.bin` |
| `hubert_base.pt` | `assets/hubert_base/hubert_base.pt` (旧格式，可能不需要) |
| `rmvpe.pt` | `assets/rmvpe/rmvpe.pt` |

**训练底模 (v2):**
`pretrained_v2/` 下全部 12 个 `.pth` → `assets/pretrained_v2/`

注意：RVC 新版使用 Transformers 格式 HuBERT（需要 config.json + pytorch_model.bin），不是旧版单文件 hubert_base.pt。

### 5. 启动命令 (CMD)
```cmd
conda activate rvc
set PYTHONPATH=E:\RVC;C:\Users\53028\.conda\envs\rvc\Lib\site-packages
set NO_PROXY=localhost,127.0.0.1,::1
cd E:\RVC
python webui.py
```

## 训练流程
1. 数据切分 → F0 提取 (rmvpe) → HuBERT 特征提取 → 训练
2. 跳过 "音高全部为0" 的片段是正常的（静音/噪音）
3. HuBERT 特征显示 `(N, 768)` — v2 格式正确
4. 训练时黑窗实时显示 loss，每 200 步打印一次
