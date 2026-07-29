# PaddleOCR Windows 搭建实录

## 环境

- Windows 10, git-bash
- GPU: RTX 4060 Laptop 8GB (CUDA 12.8)
- Python: 系统装 D:\python3.10.6 (独立安装，不受 conda/hermes 污染)
- 网络: Clash Verge 代理 127.0.0.1:10809
- 清华 pip 镜像: `https://pypi.tuna.tsinghua.edu.cn/simple`

## 搭建步骤（已验证成功）

```bash
# 1. 创建独立 venv
/d/python3.10.6/python -m venv C:/Users/53028/ocr_venv

# 2. 装 PaddleOCR（全程 unset PYTHONPATH！）
unset PYTHONPATH && "C:/Users/53028/ocr_venv/Scripts/python.exe" -m pip install paddleocr -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 首次运行自动下载模型（~77MB, 清华镜像 ~30MB/s）
unset PYTHONPATH && "C:/Users/53028/ocr_venv/Scripts/python.exe" -c "from paddleocr import PaddleOCR; ocr = PaddleOCR(lang='ch')"
```

## 踩坑全记录

| # | 方案 | 失败原因 | 教训 |
|---|------|----------|------|
| 1 | EasyOCR + GPU | 模型需从 GitHub 下载，代理传不进 conda run | 国内 OCR 首选 PaddleOCR |
| 2 | PaddleOCR 装到 rvc conda env | pydantic 版本冲突（rvc 老版 vs paddlex 新版） | 不和已有 conda env 共享 |
| 3 | PaddleOCR 装到 rvc conda env + `--user` | pip 装到了 hermes venv（PYTHONPATH 劫持） | `pip install` 也必须 `unset PYTHONPATH` |
| 4 | 独立 venv + `unset PYTHONPATH` | ✅ 成功！ | 这是唯一可靠方案 |

## API 迁移

PaddleOCR 3.7 与 2.x 不兼容：

```python
# ❌ v2.x API（已废弃）
ocr = PaddleOCR(use_angle_cls=True, lang='ch')
result = ocr.ocr(img_path, cls=True)

# ✅ v3.7 API
ocr = PaddleOCR(lang='ch')
result = ocr.predict(img_path)
for item in result:
    for text in item.get('rec_texts', []):
        print(text)
```

## 依赖清单（venv 内）

- paddleocr 3.7.0
- paddlex 3.7.2
- paddlepaddle 3.3.1 (CPU)
- opencv-contrib-python 4.10
- numpy, pillow, requests, pyyaml 等

总计约 600MB（含模型缓存）。
