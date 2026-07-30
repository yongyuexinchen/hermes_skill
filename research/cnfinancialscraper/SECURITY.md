# 安全策略与漏洞披露（SECURITY）

> cn-financial-scraper v4.3+ 安全说明与漏洞报告指引。
> 我们的目标：**用户能放心使用，作者能快速响应**，不替代通用 Web 安全实践。

---

## 🛡️ 我们的安全承诺

1. **无硬编码凭证** — 所有 API Key/Token 通过环境变量或 `config/local.json`（已 gitignore）传入
2. **无后台数据收集** — 数据存本地，不向任何第三方回传用户数据
3. **可审计** — 所有 `subprocess`/`shell` 调用均使用 list 形式（非 `shell=True`），无 `eval()`/`exec()`
4. **依赖固定版本** — `requirements.txt` 锁定主版本号，定期通过 `pip-audit` 扫描漏洞

---

## ✅ 安全审计结果（v4.3）

### 自动化扫描覆盖

| 类别 | 检查工具 | 结果 |
|------|---------|------|
| 硬编码密钥 | `grep -E "(api_key|secret|password)\s*=\s*['\"]"` | ✅ 无 |
| `eval` / `exec` | `grep -E "eval\(|exec\("` | ✅ 无 |
| `subprocess shell=True` | 自定义 AST 检查 | ✅ 无 |
| 不安全反序列化 | `grep "pickle.load\|marshal.load"` | ✅ 无（用 JSON） |
| 路径遍历 | 路径拼接 user input 检查 | ✅ 无 |
| TLS 证书验证关闭 | `grep "verify=False"` | ⚠️ 见下方说明 |
| 不安全随机数 | `random` 用法 | ⚠️ 仅用于 UA 轮换（非安全场景） |

### ⚠️ 已知可接受风险

#### 风险 1：HTTP 证书验证偶发性关闭

**位置**：`scripts/http_utils.py` 部分 fallback 路径中可选 `verify=False`

**触发条件**：用户代理开启 MITM（中间人）代理时未安装 CA 证书

**风险等级**：🟡 中
- 不会**主动**关闭证书验证
- 仅作为最后兜底（仅在用户明确启用 `disable_ssl_verify()` 时）

**缓解措施**：
```python
# 推荐：安装代理 CA 证书到系统（参见 TROUBLESHOOTING.md 1.2 / 2.2）
# 不要用：disable_ssl_verify() # ⚠️ 仅调试用

# 实际生产代码不应用 disable_ssl_verify()，应：
# 1. 把代理 CA 加进系统证书库
# 2. 或维持 verify=True，遇到错误时换代理或用 requests 的 verify 参数指定 PEM
```

---

## 🔍 用户自查建议（运维）

### 1. 检查本地配置没有泄露密钥

```bash
# 在项目根目录运行（应无输出）
grep -rE "(api_key|secret|password|token)\s*=\s*['\"][a-zA-Z0-9]{8,}" \
    --include="*.py" --include="*.json" --include="*.yaml" . 2>/dev/null
```

### 2. 验证依赖没有已知漏洞

```bash
pip install pip-audit
pip-audit -r requirements.txt
```

### 3. 确认没有意外 git 跟踪

```bash
git ls-files | grep -E "config/local|\.env$|credentials"  # 应无输出
```

### 4. 验证 MCP 工具没有泄露内部信息

```python
# 检查 mcp_server.py 的错误处理是否向客户端泄漏堆栈
python mcp_server.py --check
# 应该看到「所有错误路径均经过 sanitize，堆栈仅本地日志」
```

---

## 🚨 漏洞披露（Responsible Disclosure）

发现安全漏洞？请**不要**公开发 GitHub Issue，按以下流程报告：

### 报告模板

```
**漏洞描述**：[一句话]
**组件**：[例如 scripts/http_utils.py 某函数]
**影响版本**：[例如 v4.3.x → v4.3.5]
**影响范围**：[本地数据泄露 / 远程代码执行 / 其他]
**PoC（可选）**：[最小重现步骤]
**修复建议（可选）**：[您觉得应该怎么修]
```

### 联系方式

1. **邮件**：`security@example.com`（示例地址，请以实际仓库描述为准）
2. **微信群**：见 README.md
3. **紧急响应时间**：工作日 24 小时内首次响应

### 我们承诺

- ✅ 24h 确认收到
- ✅ 评估后 7 天内给出修复方案或解释
- ✅ 修复后向报告者致谢（除非要求匿名）
- ❌ 不向第三方分享漏洞细节（修复前）

---

## 📋 历史修复记录

| 版本 | CVE | 描述 | 修复 |
|------|-----|------|------|
| v4.3.1 | — | 用户报告 disable_ssl_verify 被误用，已加文档警告 | 已添加本文档 |
| v4.3.0 | — | 提升字符串拼接 → 列表形式的 subprocess 调用 | ✅ 在 v4.3 重构 |

---

## 🔗 相关资料

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — 错误码速查表
- [README.md](README.md) — 安装与基础使用
- [Python Security Best Practices](https://docs.python.org/3/library/security_warnings.html)

---

*最后更新：v4.3.1（2026-07-28）*
