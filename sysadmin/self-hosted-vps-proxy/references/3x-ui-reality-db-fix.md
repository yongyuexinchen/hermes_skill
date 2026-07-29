# 3X-UI Reality 配置修复（数据库直修）

## 问题

3X-UI v3.5.0 创建 VLESS + Reality 入站时，面板的 "目标" 字段填入后，**SNI（serverNames）不会自动填充**，`publicKey` 也可能为空。
面板保存后直接写 SQLite 数据库，重启时从数据库生成 `config.json`——所以手动改 `config.json` 无效。

## 症状

Xray 日志反复报错：
```
ERROR - XRAY: Failed to start: main: failed to load config files: [bin/config.json]
> infra/conf: failed to build inbound config with tag in-34356-tcp
> infra/conf: Failed to build REALITY config.
> infra/conf: empty "serverNames"
ERROR - Failure in running xray-core: exit status 23
```

`x-ui status` 显示 `active (running)` 但 Xray 子进程一直在崩溃重试。

## 诊断

```bash
# 检查数据库中的 stream_settings
ssh root@<IP> 'python3 -c "
import sqlite3, json
db = sqlite3.connect(\"/etc/x-ui/x-ui.db\")
row = db.execute(\"SELECT id, remark, stream_settings FROM inbounds WHERE id=1\").fetchone()
settings = json.loads(row[2])
rs = settings.get(\"realitySettings\", {})
print(\"serverNames:\", rs.get(\"serverNames\"))
print(\"publicKey:\", rs.get(\"publicKey\"))
db.close()
"'
```

如果 `serverNames: []` 或 `publicKey: None` → 需要修复。

## 修复命令

```bash
ssh root@<IP> 'python3 -c "
import sqlite3, json
db = sqlite3.connect(\"/etc/x-ui/x-ui.db\")
row = db.execute(\"SELECT id, stream_settings FROM inbounds WHERE id=1\").fetchone()
settings = json.loads(row[1])
rs = settings[\"realitySettings\"]
rs[\"serverNames\"] = [\"www.microsoft.com\"]
rs[\"publicKey\"] = \"<从面板安全页复制的公钥>\"
db.execute(\"UPDATE inbounds SET stream_settings=? WHERE id=1\", (json.dumps(settings),))
db.commit()
print(\"DB updated. serverNames:\", rs[\"serverNames\"])
db.close()
" && x-ui restart'
```

## 验证

```bash
ssh root@<IP> "sleep 3 && journalctl -u x-ui --no-pager --since '20 seconds ago' | grep -i 'error\|started'"
```

应该看到 `Xray <version> started` 且没有 `empty "serverNames"` 错误。

## 为什么不能直接改 config.json

3X-UI 的设计：SQLite DB 是唯一真相源。重启时从 DB 读取所有入站配置，重新生成 `/usr/local/x-ui/bin/config.json`。直接改 JSON 文件会被覆盖。
