# Draw.io 知识地图生成指南

> 完整可执行脚本：`scripts/generate_drawio.py`
> 用法：`python generate_drawio.py domain.json`

## 核心原则：零连线

**Draw.io 无碰撞检测，程序化生成的线段必然会与节点或其他线段重叠。** 因此：

- **❌ 不生成任何 `<mxCell edge="1">` 边**
- **✅ 关系通过分组容器 + 框内文本注释表达**

## 最小可工作 XML 结构

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" version="24.0.0">
  <diagram name="标题" id="map">
    <mxGraphModel dx="1200" dy="500" grid="1" gridSize="10">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <!-- 所有节点放这里，必须有 parent="1" -->
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

## XML 铁律（违反必炸）

1. **必须有 `<?xml version="1.0" encoding="UTF-8"?>` 声明**
2. **所有 mxCell 必须有 `parent="1"`**（除 id="0" 和 id="1" 外）
3. **用 `write_file` 写出，不用 `execute_code`**（沙箱隔离）
4. **不生成 edge 元素**（程序化连线必然重叠）

## 语义分组容器布局

### 分组容器
```python
style = f'rounded=1;whiteSpace=wrap;fillColor={fill};strokeColor={stroke};opacity=25;fontSize=0;'
# 容器也需要 vertex="1" parent="1"
```

### 组标题：居中加粗，双语
```python
style = f'text;html=1;fontSize=14;fontColor={stroke};fontStyle=1;align=center;'
value = f'<b style="font-size:14px;">中文 English</b>'
```

### 五色方案（固定）
| 分组 | fillColor | strokeColor |
|------|-----------|-------------|
| 核心 Core | #DAE8FC | #6C8EBF |
| 架构 Architecture | #D5E8D4 | #82B366 |
| 参数 Parameters | #FFF2CC | #D6B656 |
| 集成 Integration | #E1D5E7 | #9673A6 |
| 关系 Relations | #F8CECC | #B85450 |

### 节点样式
```python
style = f'rounded=1;whiteSpace=wrap;fillColor=#FFFFFF;strokeColor={stroke};fontSize=11;fontStyle=0;strokeWidth=2;'
value = f'⬜ 中文名(EnglishName)'  # icon + 中英对照
```

### 关系文本注释（替代连线）

在每个分组容器底部添加浅色文本注释，描述该组节点之间的关系：

```python
note_style = 'text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;whiteSpace=wrap;'
note_value = '→ 酒馆依赖 API Key 连接模型<br/>→ 上下文管理依赖世界书'
```

- 每条关系一行，`→` 开头
- `<br/>` 换行
- 灰色小字（9px, #666666）
- 放在容器底部

## 布局计算

```python
gp_l, gp_t, gp_b = 15, 40, 18   # 容器内边距
nw, nh = 175, 52                  # 节点尺寸
ng = 20                           # 节点间距
group_gap = 20                    # 组间距

x = 30
for group in groups:
    rows = len(group.nodes)
    gw = nw + gp_l * 2
    gh = gp_t + rows * (nh + ng) - ng + gp_b
    # 如有注释：gh += 注释高度 + 间距
    # 容器: (x, 30, gw, gh)
    # 标题: (x, 35, gw, 30)
    # 节点: (x + gp_l, 30 + gp_t + ri * (nh + ng), nw, nh)
    x += gw + group_gap
```

## 常见炸法

| 症状 | 原因 | 修复 |
|------|------|------|
| 双击没反应 | 缺 `<?xml?>` 或 mxCell 缺 parent | 补声明 + 全部加 parent="1" |
| 打开空白 | 容器 mxCell 缺 vertex/parent | 容器也要 vertex="1" parent="1" |
| 节点堆在一列 | 用了 BFS 分层 | 改用语义分组 |
| 边交叉成蜘蛛网 | 画了连线 | **不画线**，用容器内文本注释代替 |
| 文件用户找不到 | execute_code 写的 | 改用 write_file |