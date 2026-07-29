"""RapidOCR batch processor — groups images by ID and merges pages.
Usage: unset PYTHONPATH && ocr_venv/Scripts/python batch_ocr.py

Image naming: {group_id}_{page_num}.jpg → output/{group_id}.txt
"""
import os, sys, time, json, glob, re
from collections import defaultdict

# === Config ===
os.environ['PYTHONPATH'] = ''
sys.path = [p for p in sys.path if 'hermes-agent' not in p and 'hermes' not in p]

IMG_DIR = os.getcwd()  # override to your image directory
OUT_DIR = os.path.join(IMG_DIR, "ocr_output")
os.makedirs(OUT_DIR, exist_ok=True)

# === Group images ===
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
ocr = RapidOCR()
print("Ready.\n")

results = []
for i, group_id in enumerate(sorted(groups)):
    pages = sorted(groups[group_id])
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
    out_txt = os.path.join(OUT_DIR, f"{group_id}.txt")
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write(text)

    results.append({
        "id": group_id, "pages": len(pages),
        "lines": len(all_lines), "chars": len(text),
        "time": round(total_time, 1)
    })

    if (i + 1) % 50 == 0 or i == len(groups) - 1:
        print(f"[{i+1}/{len(groups)}] {group_id}: "
              f"{len(pages)}p, {len(all_lines)}L, {len(text)}C [{total_time:.1f}s]")

# === Summary ===
summary_path = os.path.join(OUT_DIR, "_summary.json")
with open(summary_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

total = sum(r['time'] for r in results)
print(f"\nDone! {len(groups)} groups → {OUT_DIR}")
print(f"Total: {total:.0f}s ({total/60:.1f} min) | Avg: {total/len(groups):.1f}s/group")
