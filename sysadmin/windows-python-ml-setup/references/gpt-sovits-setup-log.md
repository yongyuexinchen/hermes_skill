# GPT-SoVITS v2Pro Setup on Windows (2026-07-23)

## Environment
- Host: ASUS TUF F16 FX607JV (RTX 4060 8GB, Windows 10)
- Python: conda env `gpt-sovits` with Python 3.11.15
- Proxy: Clash Verge v2.4.7 on 127.0.0.1:7897 (Mihomo mixed port)
- Repo: RVC-Boss/GPT-SoVITS (latest main, v2Pro)

## Dependency Installation Order
1. conda create env (Tsinghua single channel, no proxy)
2. PyTorch CUDA wheel (manual download, pip install locally)
3. requirements.txt + extra-req.txt (pip --target to conda env)
4. jinja2/markupsafe downgrade (gradio 4.44.1 compat)
5. starlette downgrade (<0.40 for template compat)

## PyTorch: What Worked
- Download torch-2.8.0+cu128-cp311-cp311-win_amd64.whl via curl (direct, ~10MB/s through proxy when healthy)
- pip install with --target to conda env site-packages
- Result: CUDA=True, GPU=NVIDIA GeForce RTX 4060 Laptop GPU

## WebUI Launch Command
```bash
source /c/ProgramData/anaconda3/etc/profile.d/conda.sh && conda activate gpt-sovits
unset SSL_CERT_FILE
export NO_PROXY="localhost,127.0.0.1,::1"
export PYTHONPATH="C:/Users/53028/.conda/envs/gpt-sovits/Lib/site-packages"
cd E:/GPT-SoVITS && python webui.py
# → http://0.0.0.0:9874
```

## Missing Pretrained Models
These 5 files need manual download (network blocked both HF and ModelScope):
- `GPT_SoVITS/pretrained_models/v2Pro/s2Dv2Pro.pth`
- `GPT_SoVITS/pretrained_models/v2Pro/s2Gv2Pro.pth`
- `GPT_SoVITS/pretrained_models/s1v3.ckpt`
- `GPT_SoVITS/pretrained_models/chinese-roberta-wwm-ext-large/`
- `GPT_SoVITS/pretrained_models/chinese-hubert-base/`

Source: https://huggingface.co/lj1995/GPT-SoVITS
China mirror: https://www.yuque.com/baicaigongchang1145haoyuangong/ib3g1e/dkxgpiy9zb96hob4#nVNhX

## Proxy Behavior Notes
- git clone: works through proxy (after user said "代理应该好了")
- download.pytorch.org: intermittent SSL failures through proxy; direct works but slow
- conda multi-channel: proxy causes SSL errors on repodata.json
- conda single channel (Tsinghua): works with proxy unset
- pip + Aliyun mirror: works for CPU packages without proxy
- ModelScope API: 404 on lj1995/GPT-SoVITS (repo not mirrored)
- HuggingFace through proxy: timeout/SSL failures
- hf-mirror.com: connection failures
