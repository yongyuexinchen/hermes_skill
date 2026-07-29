# Hermes 多机环境同步

> 换电脑后一键恢复 Hermes + Grok Build + DRBCV 知识库完整工作环境。

## 仓库

| 仓库 | 用途 |
|------|------|
| `yongyuexinchen/hermes-env` | Skills + Config + Cron + Memories + Grok 配置 + setup.sh |
| `yongyuexinchen/drbcv-knowledge` | 5 vaults 281 张卡 + 共享模板（数学公式规范） |
| `yongyuexinchen/hermes-grok-integration` | 架构分析 + 集成方案（只读参考） |

## 新机部署

```bash
# 1. 安装 Hermes 桌面应用（官网 .exe）
# 2. 一键同步
git clone https://github.com/yongyuexinchen/hermes-env.git
cd hermes-env && bash scripts/setup.sh
# 3. 编辑两处 Key
#    ~/.grok/config.toml              → api_key = "sk-..."
#    ~/AppData/Local/hermes/config.yaml → api_key: sk-...
```

setup.sh 自动 6 步：[0] 检测 Hermes Agent → [1] npm 装 Grok CLI → [2] 同步 config.yaml → [3] 同步全部 Skills → [4] 同步 Cron + Memories → [5] 配 Grok config → [6] clone 知识库。

## 日常同步

```bash
cd ~/hermes-env && git pull && bash scripts/setup.sh
cd ~/DRBCV-Knowledge && git pull
```

## 注意事项

- Hermes Agent 本体（2.3G Python venv）不在 git 里——需官网安装
- API Key 不提交——GitHub push protection 自动拦截
- 国内 git push 需 VPN：`git config --global http.proxy http://127.0.0.1:7897`
