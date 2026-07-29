# 批量建卡 delegate_task 提示词模板

当处理超大规模建卡任务（40+ 概念 / 整本书），用 `delegate_task` 并行分派 3 个 leaf agent。

## 通用模板

```markdown
## 任务
阅读第X章N份逐字稿，创建约M张知识卡片。

## 源文件（D:\\Contents\\DRBCV-Knowledge\\<domain>\\Sources\\）
1. source_file.md → **概念名** (discriminant/procedure/comparison/theorem)
2. ...

## 合并建议（可选）
- 046+047 概念+代码 → 合并为「xxx」卡
- ...

## 已有卡片（格式参考，必须提供！）
- D:\\Contents\\DRBCV-Knowledge\\<domain>\\Concepts\\xxx.md
- D:\\Contents\\DRBCV-Knowledge\\<domain>\\Concepts\\yyy.md
- （至少 2-3 张作为格式参考）

## 格式要求
每张卡必须包含：frontmatter + 类型判定 + 是什么 + 正例≥2 + 反例≥1 + 详细解释 + **类比（夸张比喻+生活映射表）** + 个人见解留空 + wikilink 关系。程序型含代码+复杂度。

## 类比要求（必须给具体比喻方向！每个概念给 1-2 个比喻灵感）
- 概念A = 比喻1，比喻2
- 概念B = 比喻3
- ...

## 输出
每张卡一个 .md 写入 D:\\Contents\\DRBCV-Knowledge\\<domain>\\Concepts\\
```

## 关键注意事项

1. **类比不能由 agent 自由发挥**——必须在 prompt 中给每个概念 1-2 个比喻灵感，否则 agent 倾向于写干巴巴的学术定义。写法：「栈 = 手枪弹夹（最后压入最先射出）」而非「栈要有比喻」
2. **提供 2-3 张已有卡片路径**作为格式参考——agent 会模仿其结构
3. **明确合并策略**（如概念+代码、插入+删除合并为一张）避免 agent 产生过于碎片化的卡片
4. **每批最多 3 个 agent**（`delegation.max_concurrent_children` 限制）
5. **源文件路径必须用 Windows 绝对路径** `D:\\...\\`，不要 MSYS 风格 `/d/...`
6. **首轮先做前 3 章做验证**——检查子 agent 产出质量（类比质量、wikilink 完整性），确认无误后再继续后续章节
7. **子 agent 返回后做快速抽查**：随机打开 2-3 张卡检查类比栏是否存在、wikilink 是否正确
8. **缺卡补刀流程**：子 agent 可能因迭代限制未完成全部卡片——返回后立即 `ls Concepts/ | wc -l` 统计实际产出 vs 预期，缺的部分重新发起一个小范围 delegate_task（≤8 张卡），上下文只传未完成的源文件 + 已有格式参考
9. **每 agent 卡片数上限**：单个 agent 处理 ≥15 张卡时失败率高，建议每个 agent 控制在 8-12 张。若一个模块超过 15 张，拆成两个子任务并行或分两轮

## 已验证成功的分派方案

| 轮次 | Agent 1 | Agent 2 | Agent 3 | 产出 |
|------|---------|---------|---------|------|
| 数据结构 Round1 | Ch1 绪论(4卡) | Ch2 线性表(10卡) | Ch3 栈队列(11卡) | 25卡 |
| 数据结构 Round2 | Ch4 串(5卡) | Ch5 树(12卡) | Ch6 图(12卡) | 29卡 |
| 数据结构 Round3 | Ch7 查找(14卡) | Ch8 排序(15卡) | — | 29卡 |
| 线代 Round1 | Ch1-2 行列式+矩阵(7卡) | Ch3-4 方程组+向量(7卡) | Ch5-6 特征值+二次型(5卡) | 19卡 |
| FastAPI Round1 | 基础入门(12文件→10卡) | 进阶+ORM(13文件→11卡) | 头条新闻+部分用户(22文件→8卡) | 29卡 |
| FastAPI Round2 | 用户模块补刀(10文件→8卡) | 收藏+历史(10文件→9卡) | 缓存+AI(7文件→7卡) | 24卡 |

每轮耗时约 5-6 分钟。
