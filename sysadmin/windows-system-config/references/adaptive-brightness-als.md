# 自适应亮度 / 环境光传感器排查记录（2026-07）

## 结论
华硕天选5 Pro（TUF Gaming F16 FX607JV）**无环境光传感器**，Windows「自适应亮度」(ADAPTBRIGHT) 开了也是摆设。TUF/天选游戏本系列一贯不配 ALS——那是 Zenbook 灵耀 / ProArt 的配置。

## 证据
1. **设备管理器**：`Get-PnpDevice -Class Sensor` 抛 "找不到 PNPClass" 异常 → Sensor 设备类整个不存在，不是驱动缺失。全设备里唯一含 "light" 的是罗技鼠标 `G102 LIGHTSYNC`（RGB 灯效，干扰项）。
2. **官网规格页**：`https://www.asus.com.cn/laptops/for-gaming/tuf-gaming/asus-tuf-gaming-f16-2024/techspec/`（页面标题确认 = 天选5 Pro 规格参数）。全文搜「光线传感器/环境光/Adaptive」零命中；仅有 3 处「传感器」全在页脚广告（VivoWatch ECG/PPG、ROG 鼠标光学传感器）。
3. 屏幕本身支持软件调亮度：`WmiMonitorBrightness` 返回 CurrentBrightness=58, InstanceName=DISPLAY\CSW1632\...。

## 当前系统状态
- ADAPTBRIGHT 已设为 1（AC+DC）并 setactive——无副作用，留着无妨。
- 用户选择保持手动调节，拒绝了按时间段计划任务和 Twinkle Tray 方案。

## 替代方案（用户以后若改主意）
- 按时间段调亮度：计划任务 + `(Get-WmiObject -Namespace root/wmi -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, <0-100>)`
- Twinkle Tray：免费开源，托盘调亮度 + 日出日落规则，也支持外接显示器 DDC/CI。
- 屏幕忽明忽暗但与环境光无关 → Intel DPST（按画面内容省电调光），在显卡驱动/Armoury Crate 里关。

## ASUS 规格页抓取要点
- JS 重度渲染但规格数据内嵌在 HTML 里，curl -sL + UA 伪装可拿到（~300KB）。
- 型号映射：国际版 TUF Gaming F16 2024 = 国行天选5 Pro；FX607JV = i7-13650HX + RTX 4060 配置。
- 搜索引擎（Bing）对 curl 反爬返回无关垃圾结果，直接抓官网 techspec 页更可靠。
