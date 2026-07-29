# 3X-UI Reality 配置坑 — 完整错误 + 修复步骤

## 症状

Xray 日志反复报错：

```
ERROR - XRAY: Failed to start: main: failed to load config files: [bin/config.json]
> infra/conf: failed to build inbound config with tag in-34356-tcp
> infra/conf: Failed to build REALITY config.
> infra/conf: empty "serverNames"
```

客户端 Mihomo 日志：

```
[TCP] dial GLOBAL ... --> ... error: 192.255.128.175:34356 connect error: REALITY authentication failed
```

## 根因

3X-UI v3.5.0 网页面板的 "安全" → "Reality" 标签页，填入"目标" (`www.microsoft.com:443`) 后，**SNI 下拉框没有自动填充**，且 publicKey 字段未写入数据库中的 `realitySettings`。

检查 config.json：

```json
"realitySettings": {
  "serverNames": [],      // ← 空数组！应为 ["www.microsoft.com"]
  "publicKey": null,       // ← 缺失！
  "privateKey": "uNVnbv...",
  "shortIds": ["18", ...],
  "target": "www.microsoft.com:443"
}
```

## 修复

SSH 到 VPS，直接用 Python 修数据库：

```python
import sqlite3, json
db = sqlite3.connect("/etc/x-ui/x-ui.db")

# 读取现存配置
row = db.execute("SELECT id, stream_settings FROM inbounds WHERE id=1").fetchone()
settings = json.loads(row[1])
rs = settings["realitySettings"]

# 修复
rs["serverNames"] = ["www.microsoft.com"]
rs["publicKey"] = "0fbmDJwB4N7YHy_t_8uCLSLUjaQhIutUE5mwad42UR4"  # 你的公钥

# 写回
db.execute("UPDATE inbounds SET stream_settings=? WHERE id=1",
           (json.dumps(settings),))
db.commit()
db.close()
```

然后重启：
```bash
x-ui restart
```

**注意**：不能手动改 `config.json` 文件——3X-UI 重启时会从数据库重新生成，覆盖手动修改。必须改数据库。

## 验证

重启后确认无错误：

```bash
journalctl -u x-ui --no-pager -n 5 | grep -i "error\|started"
```

正常输出应该是 `Xray 26.7.11 started` 且没有 `empty "serverNames"` 错误。
