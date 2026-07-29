# RapidOCR Batch Processing Template

Working template from the Boss直聘 578-image batch OCR session. Proven on Windows 10, Python 3.10.6, RapidOCR 1.4.4.

## Debugging Path (How We Got Here)

1. **EasyOCR**: Installed via `pip install --user easyocr`. Models hosted on GitHub → blocked in China. `conda run` doesn't inherit proxy env vars. **Abandoned.**

2. **PaddleOCR**: Installed via `pip install paddleocr` in rvc conda env. Hit cascading conflicts:
   - Hermes PYTHONPATH injected hermes venv's pydantic → `model_validator` missing (pydantic v1 vs v2)
   - Clean ocr_venv → PaddlePaddle CPU 3.3.1 → OneDNN crash on Windows (`ConvertPirAttribute2RuntimeAttribute not support`)
   - PaddlePaddle GPU 2.6.2 → `ImportError: cannot import name 'forward_complete_op_role'` (too old for PaddleX 3.7)
   - **Abandoned.**

3. **RapidOCR**: `pip install rapidocr-onnxruntime` in clean Python 3.10 venv. Zero dependency conflicts. ONNX models auto-download from modelscope (~50MB). **First try success.** 54 text blocks from a Boss直聘 screenshot in 1.5s CPU.

## Requirements

- Clean Python 3.10+ venv (NOT rvc/hermes conda env)
- `rapidocr-onnxruntime` (pip install from Tsinghua mirror)
- `unset PYTHONPATH &&` before every Python invocation

## Working Script

```python
"""RapidOCR batch processing with grouping by prefix"""
import os, sys, time, json, glob, re
from collections import defaultdict

os.environ['PYTHONPATH'] = ''
sys.path = [p for p in sys.path if 'hermes-agent' not in p]

IMG_DIR = r"C:\path\to\images"
OUT_DIR = os.path.join(IMG_DIR, "ocr_output")
os.makedirs(OUT_DIR, exist_ok=True)

# Group by prefix pattern: {id}_{page}.jpg
files = sorted(glob.glob(os.path.join(IMG_DIR, "*.jpg")))
groups = defaultdict(list)
for f in files:
    fname = os.path.basename(f)
    m = re.match(r'(\d+)_(\d+)\.jpg', fname)
    if m:
        job_id = int(m.group(1))
        page = int(m.group(2))
        groups[job_id].append((page, f))

print(f"{len(files)} images → {len(groups)} groups")

from rapidocr_onnxruntime import RapidOCR
ocr = RapidOCR()

results = []
for i, job_id in enumerate(sorted(groups.keys())):
    pages = sorted(groups[job_id])
    all_lines = []
    total_time = 0

    for page_num, fpath in pages:
        t0 = time.time()
        raw, _ = ocr(fpath)
        total_time += time.time() - t0

        if raw:
            for item in raw:
                text = str(item[1]).strip()
                if text:
                    all_lines.append(text)

    text = '\n'.join(all_lines)
    out_txt = os.path.join(OUT_DIR, f"{job_id}.txt")
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write(text)

    results.append({
        "job_id": job_id,
        "pages": len(pages),
        "lines": len(all_lines),
        "chars": len(text),
        "time": round(total_time, 1)
    })

    if (i+1) % 50 == 0:
        print(f"[{i+1}/{len(groups)}] {job_id}: {len(pages)}p, {len(all_lines)} lines [{total_time:.1f}s]")

# Summary JSON
with open(os.path.join(OUT_DIR, "_summary.json"), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

total = sum(r['time'] for r in results)
print(f"Done! {len(groups)} groups in {total:.0f}s ({total/60:.1f}min)")
```

## Invocation

```bash
unset PYTHONPATH && C:/Users/<user>/ocr_venv/Scripts/python batch_ocr.py
```

## Quality Results (Boss直聘 Mobile Screenshots)

From 5 test images, RapidOCR extracted:
- Job titles: ✅ (AI大模型应用开发工程师, 智能体应用开发工程师)
- Salary: ✅ (15-25K·14薪, 35-50K·15薪)
- Location/Experience/Education: ✅ (深圳 / 1-3年 / 本科)
- Skill tags: ✅ (Java, PostgreSQL, Redis, Docker, Python, Flask, Django, Pandas...)
- Full job descriptions: ✅
- Confidence: 0.98-1.00 across all blocks

Noise: UI chrome (收藏, 立即沟通, 热门职位 recommendations) is also extracted — post-processing needed for clean structured data.
