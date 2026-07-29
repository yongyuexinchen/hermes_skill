---
name: windows-system-config
description: Windows系统设置与硬件查询（电源/亮度/设备/传感器），通过git-bash里调用powercfg与PowerShell完成。含MSYS引号坑、GBK乱码、硬件能力验证流程。
---

# Windows 系统配置与硬件查询（git-bash 环境）

## 触发条件
用户要求调整 Windows 系统设置（电源计划、屏幕亮度、自适应亮度、设备管理），或询问"我的电脑有没有 X 硬件/功能"。

## 核心命令

### powercfg（电源/显示设置）
```bash
# 查询当前方案的显示子组（含自适应亮度 ADAPTBRIGHT、亮度 VIDEONORMALLEVEL）
powercfg -q SCHEME_CURRENT SUB_VIDEO

# 开启自适应亮度（AC=交流 DC=电池，改完必须 setactive 才生效）
powercfg -setacvalueindex SCHEME_CURRENT SUB_VIDEO ADAPTBRIGHT 1
powercfg -setdcvalueindex SCHEME_CURRENT SUB_VIDEO ADAPTBRIGHT 1
powercfg -setactive SCHEME_CURRENT
```

### 硬件查询（PowerShell via powershell.exe）
```bash
# 机器型号（判断笔记本型号再去官网查规格）
powershell.exe -NoProfile -Command "Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer, Model | Format-List"

# 环境光传感器检测：Sensor 设备类整个不存在 = 无光传感器（不是驱动问题）
powershell.exe -NoProfile -Command "Get-PnpDevice -Class Sensor | Select FriendlyName, Status"

# 屏幕是否支持软件调亮度（报错 = 外接显示器需 DDC/CI 工具如 Twinkle Tray）
powershell.exe -NoProfile -Command "Get-CimInstance -Namespace root/wmi -ClassName WmiMonitorBrightness | Select CurrentBrightness"
```

## 坑（MSYS/git-bash 专属）

1. **`$_` 被 bash 吞掉**：`powershell.exe -Command "...$_..."` 用双引号时，bash 会把 `$_` 展开成上一条命令的参数（如 `/c/Users/53028`），导致诡异的 PowerShell 报错。**外层必须用单引号**：`powershell.exe -NoProfile -Command 'Get-PnpDevice | Where-Object { $_.Name -match "x" }'`，PS 内部字符串改用双引号。
2. **`/flag` 会被 MSYS 转成路径**：powercfg 等工具统一用短横线形式 `-setacvalueindex`，不用 `/setacvalueindex`。
3. **中文 Windows 下 powercfg 输出 GBK 乱码**：GUID 别名（ADAPTBRIGHT 等）和十六进制值仍可读，靠别名和数值判断，不要依赖中文字段名。
4. **`Get-PnpDevice -Class Sensor` 在无传感器机器上直接抛异常**（找不到 PNPClass），这本身就是"没有传感器"的答案，不是命令写错。

## 硬件能力结论的验证流程（用户明确要求过）

对"这台电脑有没有 X 功能"的结论，**本地扫描 + 官方规格页双重验证**，不能只靠本地扫描下结论：
1. `Win32_ComputerSystem` 拿到具体型号。
2. 抓厂商官方规格页 curl 验证（华硕国行：`asus.com.cn/.../techspec/`，注意国行型号名不同，如 FX607JV = 天选5 Pro）。用 python 正则剥 HTML 后搜关键词（传感器/sensor/nits/Adaptive），并检查命中处上下文——页脚广告里的"传感器"是干扰项。
3. 给用户呈现证据链（本地扫描 + 官网原文 + 产品线定位），而不是只给结论。

### 联网查证的降级路径
浏览器超时 → curl 直连；代理探测：`curl --socks5-hostname 127.0.0.1:10808 -o /dev/null -w "%{http_code}"` 返回 000 = VPN 没开，国内站点直接直连。Bing 对 curl 会反爬返回垃圾结果——优先抓厂商官网规格页而不是搜索引擎。

## 已知机器事实
用户主机：华硕天选5 Pro（TUF Gaming F16 FX607JV），无环境光传感器（自适应亮度开关无效），屏幕支持软件调亮度，Intel DPST 会按画面内容调光。详见 references/adaptive-brightness-als.md。
