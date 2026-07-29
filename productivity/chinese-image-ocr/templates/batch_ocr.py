"""RapidOCR 批处理模板 — 中文截图 OCR
用法: unset PYTHONPATH && python batch_ocr.py
"""
import os, sys, time, json, glob, re
from collections import defaultdict

# === 配置 ===
IMG_DIR = r"图片目录路径"
OUT_DIR = os.path.join(IMG_DIR, "ocr_output")
os.makedirs(OUT_DIR, exist_ok=True)

# === 按 ID 分组（如：{id}_{page}.jpg）===
files = sorted(glob.glob(os.path.join(IMG_DIR, "*.jpg")))
groups = defaultdict(list)
for f in files:
    fname = os.path.basename(f)
    m = re.match(r'(\d+)_(\d+)\.jpg', fname)
    if m:
        groups[int(m.group(1))].append((int(m.group(2)), f))

print(f"Total: {len(files)} images → {len(groups)} groups\n")

# === RapidOCR ===
from rapidocr_onnxruntime import RapidOCR
print("Loading RapidOCR (ONNX)...")
ocr = RapidOCR()
print("Ready.\n")

results = []
for i, job_id in enumerate(sorted(groups.keys())):
    pages = sorted(groups[job_id])
    all_lines = []
    total_time = 0

    for page_num, fpath in pages:
        t0 = time.time()
        raw, _ = ocr(fpath)
        elapsed = time.time() - t0
        total_time += elapsed

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
        "id": job_id, "pages": len(pages),
        "lines": len(all_lines), "chars": len(text),
        "time": round(total_time, 1)
    })

    if (i+1) % 50 == 0:
        print(f"[{i+1}/{len(groups)}] {job_id}: {len(pages)}p, {total_time:.1f}s")

# 保存汇总
with open(os.path.join(OUT_DIR, "_summary.json"), 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

total = sum(r['time'] for r in results)
print(f"\nDone! {len(groups)} groups → {OUT_DIR}")
print(f"Total time: {total:.0f}s ({total/60:.1f} min)")
