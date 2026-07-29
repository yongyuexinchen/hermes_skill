# Boss直聘 Screenshot OCR — Complete Session Record (2026-07-27)

## Input

- 578 JPG screenshots, 159MB, `C:\Users\53028\Downloads\ToDesk\boss直聘2\`
- Naming: `{job_id}_{page}.jpg` (two pages per job posting)
- Content: Boss直聘 mobile app job detail pages (Chinese)

## Engine Selection (3 attempts → 1 success)

| Attempt | Engine | Time Spent | Result |
|---------|--------|-----------|--------|
| 1 | EasyOCR | ~30 min | ❌ Model download from GitHub blocked (need proxy, can't pass to conda) |
| 2 | PaddleOCR | ~45 min | ❌ pydantic conflict with rvc conda env; CPU OneDNN bug; GPU import errors |
| 3 | **RapidOCR** | **~5 min** | ✅ ONNX Runtime, models from hf-mirror, zero deps |

## Working Setup

- **Engine**: RapidOCR 1.4.4 (rapidocr-onnxruntime)
- **Python**: 3.10.6 isolated venv at `C:\Users\53028\ocr_venv\`
- **Critical fix**: `unset PYTHONPATH` before every command (Hermes venv pollution)
- **Mirror**: `https://pypi.tuna.tsinghua.edu.cn/simple`

## Results

- **578 images → 289 job postings** (merged 2 pages per job)
- **Total time**: 2419s (40.3 min), avg 4.2s/image
- **Accuracy**: ~95% on clean mobile screenshots
- **Output**: `ocr_output/{job_id}.txt` + `_summary.json`

## Structured Extraction

- **Output**: `ocr_output/_structured.json` (289 records, 8 fields each)
- **Method**: Pure regex (no LLM), see `references/structured-extraction-pattern.md`
- **Accuracy**: salary 98.9%, city 98.9%, skills 100%

## Key Scripts

- `batch_ocr.py` → OCR batch processor (same as `scripts/batch_ocr.py` in this skill)
- `structure_jobs.py` → regex-based structured extractor
- `分析报告.md` → full market analysis report (market overview, skill gaps, learning roadmap)

## Files Location

```
C:\Users\53028\Downloads\ToDesk\boss直聘2\
├── *.jpg                    # 578 source images
├── batch_ocr.py             # OCR script
├── structure_jobs.py        # Structured extraction script
└── ocr_output/
    ├── 0.txt ~ 337.txt      # 289 OCR text files
    ├── _summary.json        # OCR batch statistics
    ├── _structured.json     # Final structured data (289 records)
    └── 分析报告.md           # Full analysis report
```
