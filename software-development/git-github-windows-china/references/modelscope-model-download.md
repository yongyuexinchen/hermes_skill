# 🇨🇳 中国网络下载 AI 模型：ModelScope > HuggingFace

## 铁律

在中国网络环境下，**ModelScope 比 HuggingFace 快 10-100 倍且不需要代理**。

| 渠道 | 速度 | 代理 | SSL 问题 |
|---|---|---|---|
| HuggingFace 直连 | ❌ 基本不通 | — | GFW SNI 干扰 |
| HuggingFace 代理 | 不稳 | 需 Clash | 偶发 `schannel: failed to receive handshake` |
| hf-mirror.com | 不稳定 | 有时不通 | — |
| **ModelScope** | ✅ 10-30MB/s | **不需要** | 无 |

## ModelScope 下载模型

```python
from modelscope import snapshot_download

result = snapshot_download(
    'iic/CosyVoice-300M',  # 模型 ID
    cache_dir='E:/CosyVoice',  # 目标目录
)
# 模型会放到: E:/CosyVoice/models/iic--CosyVoice-300M/snapshots/master/
```

### 查模型 ID

在 https://modelscope.cn/models 搜模型名，URL 里的路径就是 ID。例如：
- `https://modelscope.cn/models/iic/CosyVoice-300M` → ID: `iic/CosyVoice-300M`
- `https://modelscope.cn/models/FunAudioLLM/Fun-CosyVoice3-0.5B-2512` → ID: `FunAudioLLM/Fun-CosyVoice3-0.5B-2512`

### 允许单文件下载

```python
snapshot_download(
    'lj1995/GPT-SoVITS',
    allow_patterns=['s1v3.ckpt', 'v2Pro/*.pth'],
    cache_dir='E:/GPT-SoVITS/GPT_SoVITS/pretrained_models',
)
```

### ⚠️ 注意

- 模型 ID 区分大小写，ModelScope 有时 404 返回 `record not found` → 去网页确认准确 ID
- 大模型（>1GB）用 `cache_dir` 而非 `local_dir`，否则会下两份（缓存 + 目标目录）
- 模型和代码是分开的：ModelScope 下权重，GitHub/Gitee 下代码

## Gitee 镜像获取代码

ModelScope 只有模型权重没有代码。GitHub 代码走 Gitee 镜像：

```bash
# 搜 Gitee 镜像
git clone https://gitee.com/mirrors/CosyVoice.git E:/CosyVoice

# 常见模式：https://gitee.com/mirrors/<repo名>.git
# 不一定都有，搜不到就等网络好了走 GitHub
```

## 典型流程（以 CosyVoice 3 为例）

```bash
# 1. 代码：Gitee 镜像
git clone https://gitee.com/mirrors/CosyVoice.git E:/CosyVoice

# 2. 模型：ModelScope
conda activate rvc  # 或任何有 modelscope 的环境
python -c "
from modelscope import snapshot_download
snapshot_download('FunAudioLLM/Fun-CosyVoice3-0.5B-2512', cache_dir='E:/CosyVoice')
"

# 3. 环境：新建 conda + pip（国内镜像）
conda create -n cosyvoice python=3.11 -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main -y --override-channels
conda activate cosyvoice
pip install -r requirements.txt -i https://mirrors.pku.edu.cn/pypi/simple
```
