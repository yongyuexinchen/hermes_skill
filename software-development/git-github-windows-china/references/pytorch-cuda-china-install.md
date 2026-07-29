# PyTorch CUDA 版安装：中国网络实战记录

> 会话 1：2026-07-23 GPT-SoVITS v2Pro 环境搭建
> 会话 2：2026-07-24 RVC 环境搭建
> 主机：天选 5 Pro (RTX 4060 Laptop, 8GB VRAM)，Windows 11

## 最终成功方案

### 方案 A：南大镜像（RVC 实战，推荐）
```bash
pip install torch==2.7.1+cu128 torchaudio==2.7.1+cu128 \
  --index-url https://mirrors.nju.edu.cn/pytorch/whl/cu128 \
  --extra-index-url https://mirrors.pku.edu.cn/pypi/simple
```
3.3GB ~6 分钟，稳定无 SSL 问题。南大是**唯一提供 CUDA wheel 的国内镜像**。

### 方案 B：手动下载 wheel + pip 本地安装（GPT-SoVITS 实战）
1. `curl -L -O` 从 download.pytorch.org 直连下载（~230KB/s 慢但可靠）或走代理（快但不稳定）
2. 文件名 `%2B` → `+`：`mv "torch-2.8.0%2Bcu128-..." "torch-2.8.0+cu128-..."`
3. `pip install "E:/path/torch-2.8.0+cu128-cp311-cp311-win_amd64.whl"`
4. 确保 cp 版本匹配 conda env 的 Python 版本

### 方案 C：新建 conda 环境 + --target（避权限问题）
`site-packages is not writeable` → 新建环境可根治：
```bash
conda create -n gpt-sovits python=3.11 -c https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main -y --override-channels
pip install --target "C:/Users/.../.conda/envs/gpt-sovits/Lib/site-packages" <wheel>
```

## GPT-SoVITS 结果
- ✅ PyTorch 2.8.0+cu128 + RTX 4060 CUDA 就绪
- ✅ 61 个依赖全部安装
- ✅ WebUI 运行于 http://127.0.0.1:9874
- ⚠️ 预训练模型待下载（v2Pro: s2Dv2Pro.pth, s2Gv2Pro.pth 等）

## RVC 结果
- ✅ PyTorch 2.7.1+cu128 + RTX 4060 CUDA 就绪
- ✅ 全部依赖安装（PKU 镜像）
- ✅ WebUI 运行于 http://127.0.0.1:7865
- ✅ hubert_base.pt + rmvpe.pt + pretrained_v2 已下载
- ✅ 循环导入修复：`train/preprocess.py` 加 `sys.path.insert(0, ...)`

## Gradio 4.x 兼容性修复
jinja2 3.1.6 + starlette 1.3.1 → `TypeError: unhashable type: 'dict'`
```bash
pip install jinja2==3.1.4 markupsafe==2.1.5 "starlette<0.40"
```

## HF 模型下载

ML 预训练模型（HuggingFace）在中国网络的下载策略：

| 方法 | 适用场景 | 可靠性 |
|---|---|---|
| `huggingface_hub` + 代理 | 小文件（<100MB） | ❌ 不稳定，SSL 频繁断 |
| `hf-mirror.com` + Python API | 批量下载 | ❌ 同上 |
| **浏览器 + VPN 手动下载** | 大文件（>500MB） | ✅ 最可靠 |
| `modelscope` CLI | 模型在 ModelScope 有镜像时 | ✅ 走国内节点 |

**实用流程：**
1. 先查 HF 文件列表：`curl --noproxy '*' -s "https://hf-mirror.com/api/models/<user>/<repo>" | python -c "import sys,json; [print(s['rfilename']) for s in json.load(sys.stdin)['siblings']]"`
2. 浏览器开 VPN 打开 `https://hf-mirror.com/<user>/<repo>/tree/main`，手动下关键文件
3. 放到对应目录后用 `ls -lh` 确认体积合理（.pt/.pth 通常 100MB~2GB）
