# 火山方舟 (Volcengine Ark) 接入笔记

实测时间: 2026-07. 端点与行为可能演进, 以官方文档为准。

## 基本信息

- Base URL: `https://ark.cn-beijing.volces.com/api/v3` (OpenAI 兼容, chat/completions)
- Key 格式: `ark-xxxxxxxx-....`
- 用户 Ark Key 存在 Hermes config `auxiliary.vision.api_key` (见主 SKILL.md)

## 模型列表与筛选

`GET /api/v3/models` 返回该账户可见的全部模型 (100+), **必须按 status 过滤**:

- `Shutdown` — 已下线, 调用报错
- `Retiring` — 还能用但即将退役, 别配到长期配置里
- `None`/空 — 正常在线

**注意**: 如果终端已设 `https_proxy` (如 Clash 7897), curl 走代理可能导致 SSL 握手失败 (Schannel 不兼容)。**GET /models 可以直连**, 先 `unset https_proxy http_proxy` 再 curl。

### 精确筛选视觉模型 (按 modalities 而非名字)

方舟返回的每个模型有 `modalities.input_modalities` 字段, 含 `"image"` 即为视觉模型。比按名字关键词筛选更准确:

```bash
unset https_proxy http_proxy HTTP_PROXY HTTPS_PROXY
curl -s https://ark.cn-beijing.volces.com/api/v3/models -H "Authorization: Bearer $ARK_KEY" | python3 -c "
import sys, json
data = json.load(sys.stdin)['data']
for m in data:
    status = m.get('status')
    if status in ('Shutdown', 'Retiring'):
        continue
    mods = m.get('modalities', {}).get('input_modalities', [])
    if 'image' in mods:
        print(m['id'], '|', status or 'active')
"
```

## 视觉模型选择 (2026-07 实测在线)

- `doubao-seed-2-1-pro-260628` — 当前使用, 同系列旗舰。turbo 版排队多容易超时卡住, pro 更稳
- `doubao-seed-2-0-lite-260428` — 轻量备选, 简单识图够用且快, turbo 卡住时可应急
- `doubao-seed-2-0-mini-260428` — 最轻最快, 适合低延迟场景
- doubao-seed 1.6+ / 2.x 全系原生多模态; seedream=生图, seedance=视频, 别配成视觉

**切模型命令**: `hermes config set auxiliary.vision.model <model-id>` (改完立即生效, 无需重启)

方舟上还挂着 `deepseek-v4-pro-260425` / `deepseek-v4-flash-260425` / `glm-5-2` / `kimi-k2` 等第三方模型, 主模型省钱备选。

## 坑

1. **最小图片尺寸**: 1x1 像素测试图直接 HTTP 400 Bad Request (无详细信息)。64x64 即可通过。写探针脚本时生成 ≥64px 的图。
2. **400 不带 body 细节时**先怀疑图片尺寸/格式, 再怀疑模型名。模型名必须带版本日期后缀 (如 `-260628`), 裸名不一定解析。
3. 模型 id 与 name 字段不同: id=`doubao-seed-2-1-turbo-260628` (带版本), API 调用用 id。
4. **POST chat/completions 需代理, GET /models 不用** ⚠️ 最坑: `GET /api/v3/models` 直连正常返回 200, 但 `POST /api/v3/chat/completions` 直连超时 (HTTP 000, \"All connection attempts failed\")。根因是火山方舟的 POST 端点在国内网络环境下可能需要走代理。**症状**: Hermes `vision_analyze` 报 `All connection attempts failed` 但 `/models` 直连 curl 正常。**修复**: 在 `~/.hermes/.env` (或 `$HERMES_HOME/.env`) 设置 `HTTPS_PROXY=http://127.0.0.1:7897` (指向 Clash Verge 混合端口), 重启 Hermes。如只想代理火山方舟而放行其他国内 API (硅基流动等), 配合 `NO_PROXY=api.siliconflow.cn,api.deepseek.com`。

## 相关: 硅基流动账户诊断

```bash
curl -s https://api.siliconflow.cn/v1/user/info -H "Authorization: Bearer $SF_KEY"
# data.balance=赠送余额, data.chargeBalance=充值余额, data.totalBalance 可为负(欠费)
# 任意模型调用返回 403 {"code":30001,"message":"...balance is insufficient"} = 欠费
```
