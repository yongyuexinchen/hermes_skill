# 3X-UI 面板常见坑

## 1. Reality SNI 不保存（最坑）

**现象**：配好 Reality 入站后，`x-ui status` 正常，但 `journalctl -u x-ui` 报：
```
infra/conf: Failed to build REALITY config. > infra/conf: empty "serverNames"
```

**原因**：3X-UI Web UI 的 SNI 字段（下拉框）不会自动写入 `serverNames`。

**修复**：直接修 SQLite 数据库
```bash
python3 -c "
import sqlite3, json
db = sqlite3.connect('/etc/x-ui/x-ui.db')
row = db.execute('SELECT id, stream_settings FROM inbounds WHERE id=<ID>').fetchone()
settings = json.loads(row[1])
settings['realitySettings']['serverNames'] = ['www.microsoft.com']
db.execute('UPDATE inbounds SET stream_settings=? WHERE id=<ID>', (json.dumps(settings),))
db.commit()
" && x-ui restart
```

## 2. 数据库 vs config.json 同步

- 3X-UI 的权威数据在 `/etc/x-ui/x-ui.db`（SQLite）
- `/usr/local/x-ui/bin/config.json` 是每次重启时从数据库生成的
- **手动改 config.json 无效**——重启会被覆盖
- 改配置必须改数据库

## 3. mKCP 格式变更

Xray v26+ 废弃了旧的 mKCP header 格式：
```
The feature mkcp header & seed has been removed
```

**修复**：改用 TCP 传输，或使用新的 KCP 配置格式。

## 4. 面板 API 端口

3X-UI 的 API 在 `external-controller` 配置的端口上。默认通过命名管道 `\\.\pipe\verge-mihomo` 通信，不是 HTTP API。

## 5. 数据库快速查询

```bash
# 查看所有入站
sqlite3 /etc/x-ui/x-ui.db "SELECT id, remark, port, protocol FROM inbounds;"

# 查看表结构
sqlite3 /etc/x-ui/x-ui.db "PRAGMA table_info(inbounds);"
```
