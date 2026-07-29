# Chinese PyTorch/Conda Mirror Reference (2026-07)

## Conda Channels (fast, no proxy needed)
| Mirror | URL |
|---|---|
| Tsinghua main | `https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main` |
| Tsinghua pytorch | `https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud/pytorch` |
| NJU | `https://mirrors.nju.edu.cn/anaconda/pkgs/main` |

## PyTorch CUDA Wheels
| Mirror | Path | Status |
|---|---|---|
| NJU (南大) | `https://mirrors.nju.edu.cn/pytorch/whl/cuXXX` | ✅ Has CUDA, occasional hash mismatch |
| Official | `https://download.pytorch.org/whl/cuXXX` | ⚠️ Proxy SSL unreliable, works direct with VPN |
| Aliyun pip | `https://mirrors.aliyun.com/pypi/simple` | ❌ CPU-only torch |
| Tsinghua pip | `https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple` | ❌ CPU-only torch |
| PKU pip | `https://mirrors.pku.edu.cn/pypi/simple` | ✅ Fast for pip deps, no CUDA torch |

## HF Mirror
- `https://hf-mirror.com` — for HuggingFace model downloads via browser

## ModelScope
- `https://modelscope.cn` — Alibaba-backed, fast for Chinese projects (CosyVoice, FunASR, etc.)
