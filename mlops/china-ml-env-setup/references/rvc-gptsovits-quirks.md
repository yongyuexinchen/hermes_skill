# RVC / GPT-SoVITS 安装坑

## RVC (`Retrieval-based-Voice-Conversion-WebUI`)

### Python 版本
- 用 Python 3.12，requirements 文件明确指定 `cu128_py312`
- 不要复用别的 conda 环境——依赖冲突多

### PyTorch
- 用南大镜像：`pip install torch==2.7.1+cu128 torchaudio==2.7.1+cu128 --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu128`
- 注意版本匹配：RVC 要求 torch < 2.8

### 循环导入修复
两个文件需要在顶部加 `sys.path.insert(0, project_root)`：
- `train/preprocess.py`（数据切分子进程）
- `train/train.py`（训练子进程）

根因：`python train/preprocess.py` 运行时，脚本目录 `train/` 被加入 sys.path，导致 `from train.dataset.slicer2 import Slicer` 把 `train/train.py` 当成包加载。

### 启动命令
```bash
conda activate rvc
export PYTHONPATH="<conda_site_packages>;E:/RVC"
cd E:/RVC && python webui.py
# → http://127.0.0.1:7865
```

### 模型文件
- HuBERT：需要 Transformers 格式（`config.json` + `pytorch_model.bin` + `preprocessor_config.json`），不是单文件 `hubert_base.pt`
- RMVPE：`rmvpe.pt`
- 训练底模：`pretrained_v2/` 下 12 个 `.pth`
- 下载：`https://hf-mirror.com/lj1995/VoiceConversionWebUI`

### mute 参考文件
训练前 RVC 会在 filelist 里自动插入 mute 行。需手动创建静音文件：
- `logs/<exp>/mute/0_gt_wavs/mute40k.wav` — 1 秒 40kHz 静音
- 对应 `.npy` 特征文件（全零向量）

---

## GPT-SoVITS

### Python 版本
- 用 Python 3.11，conda 环境 `gpt-sovits`

### PyTorch
- 手动下 wheel：从 `download.pytorch.org/whl/cu128/` 找到 `cp311` + `win_amd64`
- 走代理下载快（~10MB/s），直连慢（~230KB/s）
- 或走南大镜像

### jinja2 冲突
- 装完依赖后降级：`pip install jinja2==3.1.4 markupsafe==2.1.5 "starlette<0.40"`
- 否则启动报 `TypeError: unhashable type: 'dict'`

### 启动命令
```bash
conda activate gpt-sovits
export PYTHONPATH="<conda_site_packages>"
cd E:/GPT-SoVITS && python webui.py
# → http://127.0.0.1:9874
```
