---
name: image-ocr
description: "OCR Chinese text from JPG/PNG images — RapidOCR (ONNX), engine selection, batch processing, Hermes PYTHONPATH workaround, and regex-based structured extraction."
version: 2.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [OCR, Images, Chinese, Screenshots, RapidOCR, Batch-Processing, Structured-Extraction]
    related_skills: [ocr-and-documents, python-china-env-setup]
---

# Image OCR (JPG/PNG screenshots)

Extract Chinese text from standalone images — mobile screenshots, app captures, photos.
NOT for PDFs (see `ocr-and-documents`).

## Engine selection

| Engine | Chinese | Install | Windows(CN) | Recommendation |
|--------|---------|---------|-------------|----------------|
| **RapidOCR** | Excellent | ~200MB (ONNX) | ✅ hf-mirror, no proxy | **Primary choice** |
| EasyOCR | Good | ~300MB (PyTorch) | ❌ Models on GitHub, proxy hell | Fallback only |
| PaddleOCR | Best (Baidu) | ~500MB (PaddlePaddle) | ❌ pydantic conflicts, GPU/CPU mismatch | Avoid on Windows |
| Tesseract | Mediocre | ~50MB | ✅ Manual install | English-only |

### Why RapidOCR wins on Windows in China

| Engine | Failure mode |
|--------|-------------|
| EasyOCR | Models on GitHub → download blocked; proxy can't reach `conda run` subprocess; PyTorch CUDA path lost when unsetting PYTHONPATH |
| PaddleOCR | PaddlePaddle 3.x CPU has OneDNN bug on Windows; GPU 2.6.2 has import errors with Python 3.10; pydantic version conflicts with existing conda envs |
| **RapidOCR** | ✅ ONNX Runtime — zero framework dependencies. Models from hf-mirror.com (China CDN, no proxy needed). Never conflicts with conda/venv/PYTHONPATH. |

## Setup

```bash
# Create isolated venv (Python 3.10 recommended for ONNX compatibility)
python3.10 -m venv ocr_venv

# Install (Tsinghua mirror in China)
unset PYTHONPATH
ocr_venv/Scripts/pip install rapidocr-onnxruntime -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## ⚠️ CRITICAL: always `unset PYTHONPATH`

Hermes Agent injects its venv into `PYTHONPATH`. This causes:
- `pip install` to put packages into hermes venv (not your target venv)
- `import` to load hermes packages (pydantic/PIL/PyYAML conflicts)

**Every command must be prefixed:**

```bash
# ✅ pip install
unset PYTHONPATH && ocr_venv/Scripts/pip install rapidocr-onnxruntime

# ✅ run script
unset PYTHONPATH && ocr_venv/Scripts/python batch_ocr.py

# ❌ without unset → installs to hermes venv, imports fail
ocr_venv/Scripts/python batch_ocr.py
```

`sys.path` filtering (`sys.path = [p for p in sys.path if 'hermes-agent' not in p]`) is NOT sufficient — pip still installs to wrong location. Always `unset PYTHONPATH` at the shell level.

See `python-china-env-setup` skill for full PYTHONPATH documentation.

## Basic usage

```python
from rapidocr_onnxruntime import RapidOCR

ocr = RapidOCR()
result, elapse = ocr("screenshot.jpg")
# result: [[bbox_4pts, text, confidence], ...]
# elapse: [det_time, cls_time, rec_time]

for box, text, conf in result:
    print(f"[{conf:.2f}] {text}")
```

First run downloads ~100MB models to `~/.rapidocr/`. Cached thereafter.

## Batch processing pattern

When images named `{group_id}_{page}.jpg` (e.g., Boss直聘 `1_1.jpg`, `1_2.jpg`):

```python
import os, glob, re, time, json
from collections import defaultdict
from rapidocr_onnxruntime import RapidOCR

groups = defaultdict(list)
for f in sorted(glob.glob("images/*.jpg")):
    m = re.match(r'(\d+)_(\d+)\.jpg', os.path.basename(f))
    if m:
        groups[int(m.group(1))].append((int(m.group(2)), f))

ocr = RapidOCR()
for job_id in sorted(groups):
    lines = []
    for _, fpath in sorted(groups[job_id]):
        raw, _ = ocr(fpath)
        if raw:
            for item in raw:
                text = str(item[1]).strip()
                if text:
                    lines.append(text)
    with open(f"output/{job_id}.txt", "w", encoding="utf-8") as f:
        f.write('\n'.join(lines))
```

## Post-OCR: regex-based structured extraction

**Regex works for predictable layouts.** We proved 95%+ accuracy on 289 Boss直聘 job postings with pure regex — no LLM needed.

| Field | Method | Accuracy |
|-------|--------|----------|
| Title | First line, regex strip trailing OCR noise digits | ~95% |
| Salary | `\d+-\d+K(?:·\d+薪)?` or `\d+-\d+元/天` | 98.9% |
| City | Word-list match (34 Chinese cities) in first 8 lines | 98.9% |
| Experience | `经验不限` / `\d+-\d+年` / `\d+年以上` | ~95% |
| Education | Word-list: 博士/硕士/本科/大专/学历不限 | ~95% |
| Recruiter | `.+(猎头|人事|招聘|HR|人力)` from tail | ~80% |
| Skills | 75-tech-keyword table match against full text | 100% |
| UI noise | Filter: 收藏\|立即沟通\|去App\|热门职位\|... | — |

LLM enhancement is only worth it for:
- Fixing OCR-garbled job titles (rare, ~5% of images)
- Identifying skills NOT in the keyword table

See `references/structured-extraction-pattern.md` for full 8-field extractor.

## Performance

- **Speed**: 3-10s per image on CPU (ONNX)
- **Chinese accuracy**: ~95% on clean mobile screenshots
- **GPU**: Not needed for batch OCR — ONNX CPU is fast enough
- **578 images → 289 jobs**: 40 minutes on CPU (RTX 4060 laptop, but ONNX runs CPU)

## Failed approaches (don't retry)

These were tested and failed on Windows + China network:

1. **EasyOCR + conda run**: model download from GitHub blocked → proxy not inherited by conda subprocess
2. **PaddleOCR + rvc conda env**: pydantic version conflict (rvc needs old, paddlex needs new)
3. **PaddleOCR + GPU**: paddlepaddle-gpu 2.6.2 has broken imports on Python 3.10
4. **PaddleOCR + CPU**: paddlepaddle 3.3.1 CPU has OneDNN bug on Windows (`ConvertPirAttribute2RuntimeAttribute`)
5. **venv without unset PYTHONPATH**: pip installs to hermes venv, imports find wrong packages
