# Grok Build 上手 Demo（会话 2026-07-19）

> 本会话期间编写的 Grok Build 演示，覆盖 headless / TUI / session续接 / 权限控制六个场景。
> 用 DeepSeek API 而非 xAI 内置模型，零额外成本。

## Demo 1：headless 最简脚本

```bash
mkdir -p /e/scratch/grok-demo1 && cd /e/scratch/grok-demo1 && git init
grok -m deepseek-v4 -p "写 fibonacci.py：命令行输入 n，打印前 n 个斐波那契数。if __name__=='__main__'。" --output-format json --yolo --cwd /e/scratch/grok-demo1
```
要点：`--yolo` 自动批准工具调用；`--output-format json` 可机读结果。

## Demo 2：交互 TUI

```bash
grok            # 启动 TUI
/model deepseek-v4   # 切换模型（省钱！）
```
然后试：`写 password_generator.py` → `加 pytest 测试` → `修改：默认含大写+数字`

## Demo 3：多文件项目（headless）

```bash
grok -m deepseek-v4 -p "创建 Markdown 笔记 CLI notes.py：SQLite + argparse。pytest 验证。" --output-format json --yolo --cwd /e/scratch/grok-demo3
```
观察 `num_turns` 字段了解工具循环轮数。

## Demo 4：session 续接迭代

```bash
grok -m deepseek-v4 -p "search 改成不区分大小写" --resume <sessionId> --output-format json --yolo
```

## Demo 5：只读审查

```bash
grok -m deepseek-v4 -p "审查 notes.py 安全问题/风格/bug。只读不修改。" --tools "read_file,grep,list_dir" --output-format json
```

## Demo 6：权限精细管控

```bash
grok -m deepseek-v4 -p "清理临时文件" --cwd /e/scratch --allow "Bash(rm*)" --deny "Bash(rm -rf*)" --output-format json
```

## 旗标速查

| 旗标 | 作用 |
|---|---|
| `-m deepseek-v4` | **每次都要**，否则 xAI 计费 |
| `-p "..."` | headless 非交互 |
| `--yolo` | 自动批准所有工具 |
| `--output-format json` | Hermes adapter 解析 |
| `--tools "a,b,c"` | 工具白名单 |
| `--allow / --deny` | 权限规则 |
| `--max-turns N` | 防死循环 |
| `--resume <id>` / `-c` | 续接 |

## 已知问题（本会话）

- grok 二进制未安装（国内需 VPN 访问 x.ai 安装脚本 + 首次 OAuth）
- VPN 端口 127.0.0.1:10808 本会话未开，`curl` + `powershell` 均超时
- 装完后 `~/.grok/config.toml` 已预配 DeepSeek API，可立即使用
