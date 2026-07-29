"""PaddleOCR 批处理图片 → 文本 — 支持测试/全量模式"""

import os, sys, time, json, glob, random

# === 清除 Hermes PYTHONPATH 污染 ===
os.environ['PYTHONPATH'] = ''
sys.path = [p for p in sys.path if 'hermes-agent' not in p and 'hermes' not in p]

# === 配置 ===
IMG_DIR = r"C:\Users\53028\Downloads\ToDesk\boss直聘2"   # 图片目录
OUT_DIR = os.path.join(IMG_DIR, "ocr_output")              # 输出目录
TEST_MODE = True                                            # True=测试, False=全量
TEST_COUNT = 5                                              # 测试模式采样数
# ===========

os.makedirs(OUT_DIR, exist_ok=True)

def get_files():
    files = sorted(glob.glob(os.path.join(IMG_DIR, "*.jpg")))
    assert files, f"No JPG files found in {IMG_DIR}"
    if TEST_MODE:
        random.seed(42)
        return random.sample(files, min(TEST_COUNT, len(files)))
    return files

from paddleocr import PaddleOCR

print("Loading PaddleOCR (ch)...")
ocr = PaddleOCR(lang='ch')
print("Ready.\n")

files = get_files()
results = []

for i, fpath in enumerate(files):
    fname = os.path.basename(fpath)
    print(f"[{i+1}/{len(files)}] {fname}...", end=" ", flush=True)
    t0 = time.time()

    # PaddleOCR 3.7: predict() returns list of dicts
    raw = ocr.predict(fpath)
    elapsed = time.time() - t0

    # Extract rec_texts from the result
    lines = []
    for item in raw:
        for text in item.get('rec_texts', []):
            lines.append(text)

    text = '\n'.join(lines)

    # Save individual .txt
    out_txt = os.path.join(OUT_DIR, fname.replace('.jpg', '.txt'))
    with open(out_txt, 'w', encoding='utf-8') as f:
        f.write(text)

    results.append({
        "file": fname,
        "lines": len(lines),
        "chars": len(text),
        "time": round(elapsed, 1)
    })
    print(f"{len(lines)} lines, {len(text)} chars [{elapsed:.1f}s]")
    print(text[:400])
    print("...\n" if len(text) > 400 else "\n")

# Save summary
summary_path = os.path.join(OUT_DIR, "_summary.json")
with open(summary_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"Done! Results in: {OUT_DIR}")
print(f"  {len(results)} .txt files + {summary_path}")
