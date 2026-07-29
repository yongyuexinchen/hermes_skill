# RVC 常见错误速查

## 循环导入

**错误**：`ImportError: cannot import name 'utils' from partially initialized module 'train'`

**原因**：子进程运行 `train/` 下脚本时，Python 把脚本所在目录加入 sys.path，`import train` 找到 `train/train.py` 而非 `train/` 包。

**修复**：在 `train/preprocess.py`、`train/train.py`、`train/train_index.py` 开头加：
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

## ModuleNotFoundError: No module named 'i18n' / 'infer'

**错误**：子进程报找不到 `i18n`、`infer` 等模块

**原因**：启动 webui.py 时没设 PYTHONPATH

**修复**：启动命令必须带 PYTHONPATH
```cmd
set PYTHONPATH=E:\RVC;C:\Users\<用户名>\.conda\envs\rvc\Lib\site-packages
```

## FileNotFoundError: mute40k.wav / mute48k.wav

**错误**：训练时找不到 `logs/mute/0_gt_wavs/mute40k.wav`

**原因**：RVC 训练需要静音参考文件

**修复**：用 Python 生成对应采样率的静音文件（见 skill 主文档）

## Transformers HuBERT model not found

**错误**：`FileNotFoundError: Transformers HuBERT model not found`

**原因**：只下载了 `hubert_base.pt`，缺少 `config.json` 和 `pytorch_model.bin`

**修复**：需要从 HF 下载完整 4 文件到 `assets/hubert_base/`：
- config.json
- preprocessor_config.json
- pytorch_model.bin
- hubert_base.pt（可选，旧格式）

## PyTorch 下载慢 / SSL 错误

**方案**：使用国内镜像
- NJU 镜像（cu128 wheel）：`https://mirrors.nju.edu.cn/pytorch/whl/cu128`
- PKU 镜像（pip 包）：`https://mirrors.pku.edu.cn/pypi/simple`
- 清华镜像（conda）：`https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main`

## 模型下载（HF 被墙）

**方案**：使用 hf-mirror.com 镜像站
- 浏览器直接下载：`https://hf-mirror.com/lj1995/VoiceConversionWebUI/tree/main`
- 或 Python 设置 `HF_ENDPOINT=https://hf-mirror.com`
