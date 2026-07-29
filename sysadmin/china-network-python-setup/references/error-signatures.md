# Error Signatures & Fixes

## Proxy SSL Failures (Clash 127.0.0.1:7897)

### conda
```
Retrying after connection broken by 'SSLEOFError(8, '[SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1006)')'
Retrying after connection broken by 'ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)'
```
**Fix**: `unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY` + `--override-channels` with single Tsinghua channel.

### pip
```
WARNING: Retrying after connection broken by 'ProxyError('Cannot connect to proxy.', ConnectionResetError(10054, ...))': /whl/cu128/torch/
ERROR: Could not find a version that satisfies the requirement torch (from versions: none)
```
**Fix**: Download wheel file with curl, install locally. Or `pip install --proxy ""` with `no_proxy=*` set in environment.

### curl (schannel)
```
curl: (35) schannel: failed to receive handshake, SSL/TLS connection failed
```
Occurs when proxy is flaky for certain domains. **Fix**: Try `--noproxy '*'` or wait for proxy to stabilize.

## Site-Packages Issues

### "Defaulting to user installation"
```
Defaulting to user installation because normal site-packages is not writeable
```
pip falls back to `%APPDATA%/Python/Python3XX/site-packages` instead of conda env.

### "拒绝访问" during install
```
ERROR: Could not install packages due to an OSError: [WinError 5] 拒绝访问。
'C:\\Users\\53028\\AppData\\Roaming\\Python\\Python311\\site-packages\\~andas.libs\\...'
```
User-site files locked by other processes (Hermes server, other IDEs).

**Fix for both**: `pip install --target "C:/Users/<user>/.conda/envs/<env>/Lib/site-packages" --ignore-installed`

## Gradio Startup Errors

### Jinja2 template crash
```
File "...\\jinja2\\utils.py", line 515, in __getitem__
    rv = self._mapping[key]
TypeError: unhashable type: 'dict'
```
**Fix**: `pip install jinja2==3.1.4` (downgrade from 3.1.6)

### Localhost not accessible
```
ValueError: When localhost is not accessible, a shareable link must be created.
```
**Fix**: `export NO_PROXY="localhost,127.0.0.1,::1"` before running webui

### SSL_CERT_FILE missing
```
FileNotFoundError: [Errno 2] No such file or directory
... SSL_CERT_FILE=C:\Users\53028\.conda\envs\gpt-sovits/ssl/cacert.pem
```
**Fix**: `unset SSL_CERT_FILE` or point to `certifi/cacert.pem`

## Version Incompatibilities

### huggingface_hub: cannot import HfFolder
```
ImportError: cannot import name 'HfFolder' from 'huggingface_hub'
```
User-site has older `huggingface_hub` that doesn't have `HfFolder` (removed in newer versions).
**Fix**: Use `--target` and set `PYTHONPATH` to prioritize conda env packages.
