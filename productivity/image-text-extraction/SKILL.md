---
name: image-text-extraction
description: "Extract text from images/screenshots — RapidOCR for Chinese, batch processing, venv isolation patterns."
---

# Image Text Extraction (OCR)

For **JPG/PNG screenshots and photos** (not PDFs — see `ocr-and-documents` for those).

## Decision: Which Engine?

| Engine | Chinese Quality | Install Size | Windows Reliability |
|--------|----------------|-------------|---------------------|
| **RapidOCR** | ⭐⭐⭐⭐⭐ | ~50MB (ONNX) | ✅ Gold standard |
| PaddleOCR | ⭐⭐⭐⭐⭐ | ~500MB | ❌ PaddlePaddle hell |
| EasyOCR | ⭐⭐⭐ | ~300MB | ❌ Model download from GitHub |
| Tesseract | ⭐⭐ | ~50MB | ✅ Works, poor Chinese |

**Default choice: RapidOCR.** ONNX-based, no CUDA/PaddlePaddle needed, models auto-download from modelscope/huggingface (mirrors work in China).

## Setup

```bash
# 1. Create clean venv (NEVER use rvc/hermes conda envs)
/d/python3.10.6/python -m venv C:/Users/<user>/ocr_venv

# 2. Install — ALWAYS unset PYTHONPATH (see pitfall below)
unset PYTHONPATH && C:/Users/<user>/ocr_venv/Scripts/python -m pip install \
  rapidocr-onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## API

```python
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
result, elapse = ocr("image.jpg")
# result: list of [[bbox_4pts], "text_string", confidence_float] or None
# elapse: [det_ms, rec_ms, total_ms]
```

## Batch Processing Pattern

See `references/rapidocr-batch-template.py` for the full working template. Key patterns:
- Group images by prefix (e.g., `{job_id}_{page}.jpg`) before OCR
- Use `unset PYTHONPATH &&` prefix for the Python invocation
- Save per-group combined output, not per-image

## Critical Pitfalls

### PYTHONPATH Pollution
Hermes sets global `PYTHONPATH` → all Python processes pick up Hermes venv packages. Fix: **`unset PYTHONPATH &&` before every non-Hermes Python command**. Inline `os.environ['PYTHONPATH'] = ''` is too late — sys.path is baked at startup. See `python-ml-env-windows-china` skill section 9.

### Dependency Hell (PaddleOCR / EasyOCR)
- PaddleOCR 3.7 needs PaddlePaddle 3.x which has OneDNN crash on Windows CPU; GPU version 2.6.2 is too old and has import errors
- EasyOCR models hosted on GitHub — blocked in China without proxy; proxy env vars don't survive `conda run`
- **Both are avoidable — use RapidOCR**

### pip --target for User Site-Packages
When pip says "Defaulting to user installation", packages land in `AppData\Roaming\Python` instead of the venv. Use `--target`:
```bash
unset PYTHONPATH && pip install --target "C:/Users/<user>/ocr_venv/Lib/site-packages" <pkg>
```

## Working Example

```python
from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()
result, _ = ocr(r"C:\Users\53028\Downloads\boss直聘2\1_1.jpg")
for item in result:
    bbox, text, conf = item
    print(f"[{conf:.2f}] {text}")
```
