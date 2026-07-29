# 3X-UI Reality 数据库修复

## 问题

3X-UI 面板创建 Reality 入站时，SNI 和 publicKey 可能未写入数据库，导致 Xray 报错：
```
infra/conf: empty "serverNames"
```

## 根因

3X-UI 重启时从 SQLite 数据库 `/etc/x-ui/x-ui.db` 重新生成 `config.json`。直接改 config.json 会被覆盖。

## 修复步骤

### 1. 查看当前状态
```bash
python3 -c "
import sqlite3, json
db = sqlite3.connect('/etc/x-ui/x-ui.db')
row = db.execute('SELECT id, remark, stream_settings FROM inbounds WHERE id=1').fetchone()
settings = json.loads(row[2])
rs = settings.get('realitySettings', {})
print('serverNames:', rs.get('serverNames'))
print('publicKey:', rs.get('publicKey'))
print('shortIds:', rs.get('shortIds'))
print('privateKey:', rs.get('privateKey'))
db.close()
"
```

### 2. 修复缺失字段
```bash
python3 -c "
import sqlite3, json
db = sqlite3.connect('/etc/x-ui/x-ui.db')
row = db.execute('SELECT id, stream_settings FROM inbounds WHERE id=1').fetchone()
settings = json.loads(row[1])
rs = settings['realitySettings']
rs['serverNames'] = ['www.microsoft.com']
rs['publicKey'] = 'YOUR_PUBLIC_KEY'
settings['realitySettings'] = rs
db.execute('UPDATE inbounds SET stream_settings=? WHERE id=1', (json.dumps(settings),))
db.commit()
print('Fixed. Restarting...')
db.close()
"
```

### 3. 重启
```bash
x-ui restart
```

### 4. 验证
```bash
journalctl -u x-ui --no-pager -n 5 | grep -i 'error\|started'
```
看到 `Xray 26.x.x started` 且无 ERROR 即成功。
