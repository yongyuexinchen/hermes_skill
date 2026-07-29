---
name: paddleocr-image-batch
description: "Batch OCR Chinese images/screenshots with PaddleOCR — setup, run, and pitfalls."
version: 1.0.0
platforms: [windows, linux]
metadata:
  hermes:
    tags: [OCR, PaddleOCR, Chinese, Batch, Image-to-Text]
    related_skills: [python-china-env-setup, ocr-and-documents]
---

# PaddleOCR Image Batch OCR

Use when the user asks to extract text from a batch of standalone images (JPG/PNG) — especially Chinese screenshots (Boss直聘, WeChat, mobile apps). PaddleOCR is the best open-source Chinese OCR engine; models download from domestic mirrors at full speed.

## When to Use

- Batch OCR of JPG/PNG screenshots with Chinese text
- Mobile app screenshots (Boss直聘, 微信, 淘宝, etc.)
- Any batch image→text task where marker-pdf is overkill or doesn't apply
- User says "图片转文本", "OCR这批截图", "提取招聘信息文字"

## When NOT to Use

- PDF documents → use `ocr-and-documents` skill (pymupdf / marker-pdf)
- Single image with structured extraction needed → consider vision API (if available)
- English-only documents → Tesseract may be lighter

## Setup (Windows, independent venv)

**Critical**: Hermes injects PYTHONPATH into all terminal sessions. ALWAYS use `unset PYTHONPATH` prefix.

```bash
# 1. Create clean venv from standalone Python
/d/python3.10.6/python -m venv C:/Users/53028/ocr_venv

# 2. Install (must unset PYTHONPATH or packages go to hermes venv!)
unset PYTHONPATH && "C:/Users/53028/ocr_venv/Scripts/python.exe" -m pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. Verify
unset PYTHONPATH && "C:/Users/53028/ocr_venv/Scripts/python.exe" -c "from paddleocr import PaddleOCR; print('OK')"
```

First run downloads ~77MB models from hf-mirror / Baidu (~30MB/s in China, ~4 seconds total).

## PaddleOCR 3.7 API

**API changed from 2.x**: `ocr()` is deprecated; use `predict()`. `cls=True` parameter removed.

```python
from paddleocr import PaddleOCR
ocr = PaddleOCR(lang='ch')       # Chinese + English

# v3.7: use predict()
raw = ocr.predict(img_path)      # returns list of dicts

# Extract text lines from result
for item in raw:
    rec_texts = item.get('rec_texts', [])
    rec_scores = item.get('rec_scores', [])
    for text, score in zip(rec_texts, rec_scores):
        print(f"[{score:.2f}] {text}")
```

## Batch Script Template

See `scripts/batch_ocr_paddle.py` for a ready-to-use batch processor that:
- Samples N images in TEST_MODE, or processes all in production mode
- Outputs one `.txt` per image
- Saves `_summary.json` with timing stats
- Handles the `os.environ['PYTHONPATH'] = ''` workaround inline

Run:
```bash
unset PYTHONPATH && "C:/Users/53028/ocr_venv/Scripts/python.exe" batch_ocr.py
```

## Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: pydantic_core._pydantic_core` | PYTHONPATH loading hermes venv's broken pydantic | `unset PYTHONPATH` before python command |
| `pip install` succeeds but `import` fails | pip installed to hermes venv, not target venv | `unset PYTHONPATH` before pip command |
| `TypeError: got unexpected keyword argument 'cls'` | Using v2 API on v3 | Change `ocr.ocr(path, cls=True)` to `ocr.predict(path)` |
| `Engine 'paddle_static' is unavailable` | Missing paddlepaddle runtime | `pip install paddlepaddle` (CPU, ~500MB) |
| EasyOCR model download timeout | GitHub blocked in China | Switch to PaddleOCR (domestic mirrors) |

## Comparison: PaddleOCR vs EasyOCR

| | PaddleOCR | EasyOCR |
|---|---|---|
| Chinese accuracy | ★★★★★ Best in class | ★★★☆ Good |
| Model download | Domestic mirrors, fast | GitHub only, needs proxy |
| Install size | ~600MB (paddle + models) | ~300MB (torch + models) |
| API | `ocr.predict(path)` | `reader.readtext(path)` |
| GPU support | CUDA auto-detect | CUDA auto-detect |
