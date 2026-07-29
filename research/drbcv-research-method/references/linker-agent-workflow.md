# Linker Agent — 双向关系链修补工作流

## 适用场景

当以下情况之一满足时，启动本工作流：

- 新卡片批量生成后，需补全关系链
- 现有 vault 中检测到大量缺失逆向链接或孤立节点
- 新用户导入 vault 后，首次进行关系链审计

## 前置条件

- 所有概念卡已按 vault 模板生成，位于 `Concepts/` 目录
- 关系 section 使用 `[[wikilink]]` 格式
- 扫描器已识别出 vault 内所有概念卡名称

## 工作流总览（三阶段）

```
Phase 1: 解析 → 建图 → 补逆向链
Phase 2: 拯救孤立节点（加推导链）
Phase 3: 补级联逆向链 → 验证 → 报告
```

---

## Phase 0：探查与建图

### 0.1 收集所有概念卡

```python
import os, re
files = [f for f in os.listdir(CONCEPTS_DIR) if f.endswith('.md')]
card_names = set(f[:-3] for f in files)
```

### 0.2 提取所有 `[[wikilink]]` 关系

注意：排除 `[[Calculus]]` 等命名空间标签。

```python
def extract_wikilinks(content):
    links = re.findall(r'\[\[([^\]]+)\]\]', content)
    return [l for l in links if l != 'Calculus']
```

### 0.3 构建有向图并识别缺失

```python
graph = defaultdict(set)
for name in card_names:
    content = read_card(name)
    links = extract_wikilinks(content)
    for link in links:
        if link in card_names:
            graph[name].add(link)

# 找缺失逆向链：A → B 存在但 B → A 不存在
missing = []
for source in card_names:
    for target in graph[source]:
        if source not in graph[target]:
            missing.append((source, target))

# 找孤立节点：无入边也无出边
orphans = [n for n in card_names
           if not graph[n] and not any(n in graph[s] for s in card_names)]
```

### 0.4 确定每张卡的格式

vault 内卡片可能有多种格式，必须分别处理：

| 格式 | 特征 | 示例 section |
|------|------|-------------|
| **新格式** (new) | `## 关系` + `### → 指向` + `### ← 被指向` | 微分.md |
| **旧格式** (old) | `## 关系（★...）` + `### 由...推导而来` + `### 可推导出` | 不定积分.md |
| **无关系** (none) | 无 `## 关系` section 或使用 `## 与其他定理的关系` 替代 | 洛必达法则.md |
| **混合** (hybrid) | 一个文件包含两张合并卡，两种格式共存 | 导数定义.md |

```python
def detect_format(content):
    if '## 关系\n' in content and ('### → 指向' in content or '### ← 被指向' in content):
        if '## 关系（★' in content: return 'hybrid'
        return 'new'
    if '## 关系（★' in content or ('### 由...推导而来' in content or '### 可推导出' in content):
        return 'old'
    if '## 关系\n' in content: return 'new'
    if '## 与其他定理的关系' in content: return 'other'
    return 'none'
```

---

## Phase 1：补全逆向链接

### 策略

遍历 `missing` 列表，对每对 `(source, target)`：

1. **判断 source 中链接所在的 section 类型**：
   - source 中链接在 `→ 指向` / `可推导出` → target 需要加 `← 被指向` / `由...推导而来`
   - source 中链接在 `← 被指向` / `由...推导而来` → target 需要加 `→ 指向` / `可推导出`

2. **在 target 中找到正确 section 并追加**。必须检查是否已存在，避免重复。

### 插入辅助函数

```python
def find_section(content, header_prefix):
    """找到 ### 子节的起始行号。"""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith('### ') and header_prefix in s:
            return i
    return -1

def section_last_content_line(content, header_idx):
    """找到 ### 子节中最后一个非空内容行的行号。"""
    lines = content.split('\n')
    last = header_idx
    for j in range(header_idx + 1, len(lines)):
        s = lines[j].strip()
        if s.startswith('### ') or s.startswith('## '):
            break
        if s:  # 非空行
            last = j
    return last
```

### 新格式卡片插入模板

```python
# 在 ← 被指向 section 追加
bwd_idx = find_section(content, '← 被指向')
last = section_last_content_line(content, bwd_idx)
lines = content.split('\n')
for s in sources:
    seg = '\n'.join(lines[bwd_idx:last+1])
    if f'[[{s}]]' in seg:
        continue  # 已存在，跳过
    lines.insert(last+1, f'- [[{s}]] ({s} → {target})')
    last += 1
```

### 无关系 section 卡片处理

对于完全没有 `## 关系` 的卡片（如 concept-card 格式），需新建 section：

```python
# 找到插入位置（在 ## 类比 或 ## 个人见解 之前）
insert_at = len(lines)
for marker in ['## 类比', '## 个人见解']:
    for i, line in enumerate(lines):
        if line.strip().startswith(marker) and i < insert_at:
            insert_at = i
            break

parts = ['', '## 关系', '']
parts.append('### → 指向')
parts.append('- （待补充正向链接）')
parts.append('')
parts.append('### ← 被指向')
for s in sources:
    parts.append(f'- [[{s}]] ({s} → {target})')
new_section = '\n'.join(parts)
lines[insert_at:insert_at] = new_section.split('\n')
```

---

## Phase 2：拯救孤立节点

孤立节点是既无出边也无入边的卡片。需要推断其在知识体系中的位置。

### 层次推断

根据知识领域预定义层次映射表：

```python
HIERARCHY = {
    'ε-N语言（伊普西隆-大恩语言）': ['数列极限（ε-N定义）'],
    '数列极限（ε-N定义）': ['两个重要极限', '夹逼定理', '单调有界准则'],
    '函数极限（ε-δ定义）': ['两个重要极限', '无穷小与无穷大'],
    '左导数与右导数（单侧导数）': ['导数定义'],
    '导数定义': ['左导数与右导数（单侧导数）', '导数的几何意义', '可导与连续的关系'],
    '费马引理': ['导数定义', '极值'],
    '罗尔定理': ['费马引理', '极值', '连续性与间断点'],
    '拉格朗日中值定理': ['罗尔定理', '费马引理'],
    '柯西中值定理': ['拉格朗日中值定理', '罗尔定理'],
    '泰勒公式': ['拉格朗日中值定理', '高阶导数'],
    '麦克劳林公式': ['泰勒公式'],
    '皮亚诺余项': ['泰勒公式'],
    '拉格朗日余项': ['泰勒公式', '拉格朗日中值定理'],
    '定积分的定义': ['黎曼和', '数列极限（ε-N定义）'],
    '牛顿-莱布尼茨公式': ['定积分的定义', '原函数存在定理', '变上限积分求导定理'],
    '变上限积分函数': ['定积分的定义', '原函数'],
    '变上限积分求导定理': ['变上限积分函数', '导数定义'],
    '定积分的换元法': ['牛顿-莱布尼茨公式', '定积分的定义'],
    '定积分的分部积分法': ['牛顿-莱布尼茨公式', '分部积分法'],
    # ... 每张孤立卡对应其 1-3 个父概念
}
```

规则：每张孤立卡添加 `由...推导而来（依赖） → [父概念1, 父概念2, ...]` 链接。

### 处理示例

```python
for orphan in orphans:
    parents = HIERARCHY.get(orphan, [])
    if not parents:
        continue
    # 找到 由...推导而来 section（旧格式）或 ← 被指向（新格式）
    # 追加父概念链接，标注说明
```

---

## Phase 3：补级联逆向链

Phase 2 在孤立节点中添加了指向父概念的链接，这产生了**新的缺失逆向链**（父概念未指向孤立节点）。必须运行第二轮修补。

### 验证循环

```python
# 每次修补后重新建图
graph2 = build_graph(card_names)
remaining = []
for s in card_names:
    for t in graph2[s]:
        if s not in graph2[t]:
            remaining.append((s, t))
# 修补 remaining，循环直到收敛
```

通常 **2 轮**即可收敛到 100% 双向。

---

## 验证标准

| 指标 | 合格标准 |
|------|---------|
| 有向链接总数 | ≥ 原始 2 倍（112 张卡约 400+） |
| 唯一概念对 (A-B) | 全部双向 |
| 缺失逆向链 | 0 |
| 孤立节点 | 0 |
| 链接健康度 | 100% |

---

## 已知 Pitfalls

1. **混合格式卡片**（如 导数定义.md 合并了两张卡）：优先添加至新格式 section，若新旧并存可能需两次操作
2. **级联遗漏**：第一轮修补后必然产生新的缺失，必须运行第二轮
3. **名称不一致**：`[[wikilink]]` 中的名称必须与文件名完全一致（含全角/半角空格、括号格式）
4. **插入位置错误**：用 `section_last_content_line` 时需区分空行和非空行，避免插在 section 分隔行之后
5. **重复链接**：追加前必须检查 `[[link]]` 是否已在该子节出现，用字符串包含判断
6. **concept-card 格式卡片**：此类卡片没有 `## 关系` section，使用 `|---` 分隔符和 `## 定义/定理` 等 section，需要从头创建 `## 关系`
7. **LaTeX 中的 `[[`**：确保无 LaTeX 公式包含 `[[` 被误认为 wikilink；检查 `$$` 块和行内 `$` 公式

---

## 脚本工具参考

完整实现见：[scripts/linker-patch.py](scripts/linker-patch.py) / [scripts/linker-verify.py](scripts/linker-verify.py)