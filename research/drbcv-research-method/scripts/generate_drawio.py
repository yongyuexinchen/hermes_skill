"""
Draw.io 知识地图生成脚本 — 零连线 + 语义分组容器布局
用法: python generate_drawio.py <domain>.json
输出: <domain>.drawio（与 JSON 同目录）

铁律：
- 不画任何 edge/连线（程序化生成必重叠）
- 关系用容器底部灰色文本注释表达
- 语义分组 + 五色容器
- 所有 mxCell 必须有 parent="1"
"""
import json, os, sys

# === 五色方案（固定） ===
GROUPS = [
    ("核心 Core",       "#DAE8FC", "#6C8EBF"),
    ("架构 Architecture", "#D5E8D4", "#82B366"),
    ("参数 Parameters",   "#FFF2CC", "#D6B656"),
    ("集成 Integration",  "#E1D5E7", "#9673A6"),
    ("关系 Relations",    "#F8CECC", "#B85450"),
]

STATUS = {
    "unexplored": ("#FFFFFF", None),       # 白底，边框用组色
    "exploring":  ("#FFF3CD", "#FFC107"),
    "exploded":   ("#D4EDDA", "#28A745"),
    "core":       ("#CCE5FF", "#007BFF"),
}
ICONS = {"unexplored": "⬜", "exploring": "🔄", "exploded": "✅", "core": "📌"}

# 布局常量
GP_L, GP_T, GP_B = 15, 40, 18
NW, NH = 175, 52
NG = 20
GROUP_GAP = 20


def generate(json_path, relations=None):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = {n["id"]: n for n in data["nodes"]}
    if relations is None:
        relations = {}

    # 自动分配节点到分组（按数据中的 groups 或均分到五色）
    if "groups" in data and data["groups"]:
        gdefs = data["groups"]
    else:
        all_ids = [n["id"] for n in data["nodes"]]
        k = max(1, len(all_ids) // len(GROUPS) + (1 if len(all_ids) % len(GROUPS) else 0))
        gdefs = []
        for i, (gn, fc, sc) in enumerate(GROUPS):
            chunk = all_ids[i*k:(i+1)*k]
            if chunk:
                gdefs.append((gn, chunk, fc, sc))

    # 补全颜色
    final_groups = []
    for gdef in gdefs:
        gn, nids = gdef[0], gdef[1]
        fc, sc = "#E0E0E0", "#999999"
        if len(gdef) >= 4:
            fc, sc = gdef[2], gdef[3]
        else:
            for gcn, gfc, gsc in GROUPS:
                if gn[:2] == gcn[:2]:
                    fc, sc = gfc, gsc
                    break
        final_groups.append((gn, nids, fc, sc))

    # 计算画布
    gdata = []
    gx = 30
    for gn, nids, fc, sc in final_groups:
        rows = len(nids)
        gw = NW + GP_L * 2
        gh = GP_T + rows * (NH + NG) - NG + GP_B
        note_text = relations.get(gn, "")
        note_h = 0
        if note_text:
            note_h = (note_text.count('\n') + 1) * 14 + 10
            gh += note_h + 8
        gdata.append((gn, nids, fc, sc, gx, 30, gw, gh, note_h, note_text))
        gx += gw + GROUP_GAP

    tw = gx - GROUP_GAP
    mh = max(g[6] for g in gdata)

    # 生成 XML
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<mxfile host="app.diagrams.net" version="24.0.0"><diagram name="{data["domain"]}" id="map"><mxGraphModel dx="{tw+50}" dy="{30+mh+50}" grid="1" gridSize="10"><root>',
        '<mxCell id="0"/><mxCell id="1" parent="0"/>',
    ]
    cell_id = 2

    for gn, nids, fc, sc, gx, gy, gw, gh, note_h, note_text in gdata:
        # 容器
        parts.append(f'<mxCell id="{cell_id}" value="" style="rounded=1;whiteSpace=wrap;fillColor={fc};strokeColor={sc};opacity=25;fontSize=0;" vertex="1" parent="1"><mxGeometry x="{gx}" y="{gy}" width="{gw}" height="{gh}" as="geometry"/></mxCell>')
        cell_id += 1
        # 标题
        parts.append(f'<mxCell id="{cell_id}" value="&lt;b style=&quot;font-size:14px;&quot;&gt;{gn}&lt;/b&gt;" style="text;html=1;fontSize=14;fontColor={sc};fontStyle=1;align=center;" vertex="1" parent="1"><mxGeometry x="{gx}" y="{gy+5}" width="{gw}" height="30" as="geometry"/></mxCell>')
        cell_id += 1
        # 节点
        for ri, nid in enumerate(nids):
            node = nodes.get(nid)
            if not node: continue
            nx, ny = gx + GP_L, gy + GP_T + ri * (NH + NG)
            status = node.get("status", "unexplored")
            nfill, nstroke = STATUS[status]
            if nstroke is None:
                nstroke = sc
            icon = ICONS.get(status, "⬜")
            label = f"{icon} {node['label']}".replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            parts.append(f'<mxCell id="{cell_id}" value="{label}" style="rounded=1;whiteSpace=wrap;fillColor={nfill};strokeColor={nstroke};fontSize=11;fontStyle=0;strokeWidth=2;" vertex="1" parent="1"><mxGeometry x="{nx}" y="{ny}" width="{NW}" height="{NH}" as="geometry"/></mxCell>')
            cell_id += 1
        # 关系注释
        if note_text:
            nx, ny = gx + 10, gy + gh - note_h - 3
            nh_html = note_text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
            parts.append(f'<mxCell id="{cell_id}" value="{nh_html}" style="text;html=1;fontSize=9;fontColor=#666666;align=left;spacingLeft=8;whiteSpace=wrap;" vertex="1" parent="1"><mxGeometry x="{nx}" y="{ny}" width="{gw-20}" height="{note_h}" as="geometry"/></mxCell>')
            cell_id += 1

    parts.append('</root></mxGraphModel></diagram></mxfile>')
    result = '\n'.join(parts)

    drawio_path = json_path.replace(".json", ".drawio")
    with open(drawio_path, "w", encoding="utf-8") as f:
        f.write(result)

    unexplored = sum(1 for n in data["nodes"] if n.get("status") == "unexplored")
    exploded = sum(1 for n in data["nodes"] if n.get("status") in ("exploded", "core"))
    print(f"Generated: {drawio_path}")
    print(f"Groups: {len(final_groups)} | Nodes: {len(data['nodes'])} | ✅{exploded} | ⬜{unexplored}")
    return drawio_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_drawio.py <domain>.json")
        sys.exit(1)
    generate(sys.argv[1])
