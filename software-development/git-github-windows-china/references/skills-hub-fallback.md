# hermes skills install 超时 → 手动安装

当 `hermes skills install <hub-identifier>` 在中国网络下超时（即使代理在线），走本地克隆 + 手动复制路线。

## 流程

### 1. 先确认代理
```bash
timeout 3 bash -c 'echo > /dev/tcp/127.0.0.1/7897' 2>/dev/null && echo "PROXY OK" || echo "PROXY DOWN"
```

### 2. git clone 到 Windows 路径（不要用 /tmp）
```bash
git clone --depth 1 --single-branch https://github.com/<owner>/<repo>.git "C:/Users/53028/<repo>"
```

### 3. 手动复制技能到 Hermes skills 目录
```bash
mkdir -p "C:/Users/53028/AppData/Local/hermes/skills/<skill-name>"
cp -r "C:/Users/53028/<repo>/skills/<skill-name>/"* \
  "C:/Users/53028/AppData/Local/hermes/skills/<skill-name>/"
```

### 4. 验证
```bash
hermes skills list | grep -i <skill-name>
```

### 5. 清理
```bash
rm -rf "C:/Users/53028/<repo>"
```

## 为什么 hub install 会超时

`hermes skills install` 内部走 HTTP 请求拉取 SKILL.md，即使 git clone 走代理正常，HTTP 请求可能被 Clash 规则 REJECT 或不走代理。本地 clone + copy 绕过了这层问题。

## 已装技能的本地路径

`C:/Users/53028/AppData/Local/hermes/skills/` — 手动复制的技能和 hub 安装的在同一个目录，`hermes skills list` 都能看到。
