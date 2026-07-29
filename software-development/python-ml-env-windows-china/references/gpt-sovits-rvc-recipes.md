# GPT-SoVITS & RVC Setup Recipes (2026-07-23)

## GPT-SoVITS v2Pro on Windows

**Repo**: `E:/GPT-SoVITS/` (cloned from `RVC-Boss/GPT-SoVITS`)
**Conda env**: `gpt-sovits` (Python 3.11.15)
**PyTorch**: 2.8.0+cu128 (used pre-downloaded cp311 wheel via `--target`)
**GPU**: RTX 4060 Laptop (8188 MiB)

### Dependency Quirks
- Gradio 4.44.1 + starlette 1.3.1 + jinja2 → `TypeError: unhashable type: 'dict'` in template cache
- Fix: `pip install "starlette<0.40"` → starlette 0.39.2
- Then: `pip install jinja2==3.1.4 markupsafe==2.1.5` (gradio requires markupsafe~=2.0)
- fastapi 0.139.2 requires starlette>=0.46.0 but continues to work with 0.39.2 for Gradio serving

### Missing Pretrained Models
All on HuggingFace `lj1995/GPT-SoVITS`:
- `v2Pro/s2Gv2Pro.pth`, `v2Pro/s2Dv2Pro.pth`
- `s1v3.ckpt`
- `chinese-roberta-wwm-ext-large/`
- `chinese-hubert-base/`

ModelScope `lj1995/GPT-SoVITS` returned 404. HF download through proxy timed out. `HF_ENDPOINT=https://hf-mirror.com` also failed.

### WebUI
- URL: `http://127.0.0.1:9874`
- Start: `python webui.py` (with PYTHONPATH, NO_PROXY, unset SSL_CERT_FILE)

---

## RVC (Retrieval-based Voice Conversion) on Windows

**Repo**: `E:/RVC/` (cloned from `RVC-Boss/Retrieval-based-Voice-Conversion-WebUI`)
**Conda env**: `rvc` (Python 3.12.13)
**PyTorch**: 2.7.1+cu128 (from NJU mirror — built into requirements!)
**GPU**: RTX 4060 Laptop

### Key Advantages
- Requirements file embeds mirror URLs: `--index-url https://mirrors.pku.edu.cn/pypi/simple`
- PyTorch install line in file header uses NJU mirror → no proxy workaround needed
- Gradio 3.14.0 (older, no starlette/jinja2 conflict)

### Dependency Quirks
- `websockets==10.4` build failed because Hermes venv's setuptools (65.5.0, Python 3.11) shadowed the env's
- Fix: `pip install --target "$SITE" setuptools==75.8.0` before requirements install

### WebUI
- URL: `http://127.0.0.1:7865`
- Detected: `cuda:0 | torch.float16`
- Two UIs: `go-webui.bat` (training/inference) and `go-realtime_gui.bat` (real-time voice changer)
