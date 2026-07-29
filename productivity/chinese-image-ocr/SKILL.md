---
name: chinese-image-ocr
description: "OCR Chinese text from JPG/PNG screenshots, photos, and mobile app captures. Covers RapidOCR setup, batch processing, and structured regex extraction."
version: 1.0.0
author: Hermes Agent
platforms: [windows]
metadata:
  hermes:
    tags: [OCR, Chinese, Image, RapidOCR, Extraction]
---

# Chinese Image OCR

For Chinese-text images (screenshots, photos of documents, mobile app captures), use **RapidOCR** — ONNX Runtime-based, zero PaddlePaddle dependency, clean pip install.

## Why RapidOCR

| Engine | Chinese accuracy | Install pain | Recommendation |
|--------|-----------------|--------------|----------------|
| **RapidOCR (ONNX)** | ⭐⭐⭐⭐ | ~30s pip install | ✅ First choice |
| PaddleOCR | ⭐⭐⭐⭐⭐ | PaddlePaddle dependency hell (GPU/CPU version conflicts, OneDNN bugs) | ❌ Only if GPU PaddlePaddle already working |
| EasyOCR | ⭐⭐⭐ | Model download from GitHub needs proxy; CUDA detection finicky | ❌ |
| Tesseract | ⭐⭐ | Standalone .exe but Chinese accuracy poor | ❌ |

## Step 1: Create clean venv

**CRITICAL**: Must use a standalone venv. Do NOT install into a conda env that has PyTorch or into the hermes venv.

```bash
# Use Python 3.10 for maximum compatibility
/path/to/python3.10 -m venv ocr_venv
```

## Step 2: Install (MUST unset PYTHONPATH)

**PITFALL**: Hermes injects its own venv into `PYTHONPATH`, causing `pip install` to silently write packages into the hermes venv instead of your target. Always prefix with `unset PYTHONPATH`:

```bash
# China mirror for speed
unset PYTHONPATH && ocr_venv/Scripts/python -m pip install rapidocr-onnxruntime \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
```

Models download automatically on first `RapidOCR()` call (~100MB, cached in user directory).

## Step 3: OCR API

```python
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()                        # CPU-only, no GPU config needed
result, elapse = ocr("image.jpg")       # elapse = [det_time, rec_time, total_time]

# result: list of [bbox, text, confidence]
# bbox: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
# text: str — the recognized text
# confidence: float 0-1
```

## Step 4: Batch processing pattern

For multi-page screenshots with naming convention `{id}_{page}.jpg`:

```python
from collections import defaultdict
for f in glob("*.jpg"):
    job_id, page = re.match(r'(\d+)_(\d+)', f).groups()
    groups[int(job_id)].append((int(page), f))

for job_id, pages in sorted(groups.items()):
    all_text = []
    for page, fpath in sorted(pages):
        result, _ = ocr(fpath)
        if result:
            all_text.extend(item[1] for item in result)
    # Save combined text
```

## Step 5: Run

```bash
unset PYTHONPATH && ocr_venv/Scripts/python batch_ocr.py
```

**PITFALL**: `conda run` does NOT inherit proxy env vars and does NOT clear PYTHONPATH. Use direct venv python invocation instead.

## Structured extraction after OCR

When OCR output has predictable layout (fixed header → body → footer pattern), regex extraction can achieve 95%+ accuracy on Chinese job posting screenshots without LLM cost.

Key regex patterns (see `references/boss-zhipin-extraction.md`):
- Job title: first meaningful line
- Salary: `\d+-\d+K(?:·\d+薪)?` or `\d+-\d+元/天`
- City: word list match (深圳/北京/上海/...)
- Experience: `经验不限|\d+-\d+年`
- Degree: `本科|硕士|大专|博士|学历不限`
- Recruiter: `.+·(?:猎头|人事|招聘|HR|人力)`
- JD body: content between `职位描述` and recruiter line
- Skills: keyword matching against curated tech vocabulary

## Files

- `templates/batch_ocr.py` — Reusable batch OCR script (group by ID, save txt + summary JSON). Copy and modify `IMG_DIR` path.
- `references/boss-zhipin-extraction.md` — Boss直聘 job posting extraction patterns, regex recipes, JSON schema, accuracy benchmarks.
