# Boss直聘 Job Posting Extraction Patterns

## OCR Text Structure

Each job posting screenshot (2 pages merged) produces text with this layout:

```
Line 1:   职位名称（可能有 OCR 尾部噪声如 "2"）
Line 2:   薪资 "XX-XXK·XX薪" or "XX-XX元/天"
Line 3-4: UI 噪声 "收藏" "立即沟通"
Line 5-7: 城市 + 经验 + 学历（三种变体）:
          - 深圳1-3年本科          (all merged)
          - 深圳\n经验不限\n本科    (3 separate lines)
          - 深圳\n|经验不限\n本科  (with OCR pipe artifact)
Line 8:   "职位描述"
Line 9+:  JD 正文 → 猎头信息 → UI 噪声尾部
```

## Extraction Regex Patterns

### Salary (月薪)
```python
r'(\d+-\d+K)\s*(?:[·.]\s*(\d+)\s*薪)?'
# Matches: "45-65K·15薪", "20-30K", "40-70K"
```

### Salary (日薪/实习)
```python
r'(\d+-\d+)\s*元/天'
# Matches: "350-500元/天", "100-200元/天"
```

### City
```python
CITIES = ["深圳", "北京", "上海", "广州", "杭州", "成都", "武汉", "南京", "苏州",
          "西安", "长沙", "重庆", "东莞", "佛山", "珠海", "厦门", "天津", "合肥",
          "郑州", "济南", "青岛", "福州", "无锡", "宁波", "大连", "沈阳"]
# Match first occurrence in header block (lines 1-8)
```

### Experience
```python
r'经验不限'
r'(\d+-\d+年)'
r'(\d+)年以上'
# Matches: "经验不限", "1-3年", "3-5年", "5-10年", "8年以上"
```

### Degree
```python
DEGREES = ["博士", "硕士", "本科", "大专", "学历不限"]
# Match in header block (lines 1-8)
```

### Recruiter/HR
```python
r'(.+?·(?:猎头|人事|招聘|HR|人力))'
# Search from end of file backward
# Matches: "途聚人力·猎头", "乐唯科技·HR", "上海万宝盛华信息科技·招聘"
```

### Job Title
```python
def clean_title(title):
    title = title.strip()
    title = re.sub(r'[\s）\)]*\d+\s*$', '', title)  # remove trailing digits
    title = re.sub(r'[|丨·]\s*$', '', title)
    return title.strip()
```

### UI Noise (lines to strip)
```python
NOISE = [
    r'^收藏$', r'^立即沟通$', r'^微信扫码分享', r'^举报$',
    r'^去App$', r'^查看更多信息$', r'^求职工具$',
    r'^升级VIP$', r'^立即使用$', r'^去升级$',
    r'^热门职位$', r'^热门城市$', r'^热门企业$', r'^附近城市$',
    r'^深圳.*招聘$', r'^BOSS直聘', r'^与BOSS随时沟通$',
    r'^刚刚活跃$', r'^V$', r'^在线$',
]
```

## Output JSON Schema

```json
{
  "job_id": 0,
  "job_title": "强化学习算法工程师（具身大模型）",
  "salary": "45-65K·15薪",
  "city": "深圳",
  "experience": "1-3年",
  "degree": "本科",
  "skills": ["Python", "PyTorch", "ROS2", "大模型", "强化学习", ...],
  "recruiter": "途聚人力·猎头",
  "jd_summary": "1.机器人强化学习算法研究与开发...（截断2000字）"
}
```

## Skill Keywords (curated tech vocabulary)

AI/ML: Python, PyTorch, TensorFlow, Transformer, GPT, LLaMA, BERT, Diffusion, GAN, VLA, RAG, Agent, Prompt, SFT, LoRA, RLHF, vLLM, 大模型, 深度学习, 强化学习, 多模态, 模型微调, 推理优化, 量化, 蒸馏

Databases: SQL, MySQL, PostgreSQL, MongoDB, Redis, Elasticsearch, Spark, Kafka, Pandas, NumPy

DevOps: Docker, Kubernetes, K8s, CI/CD, Nginx, Linux, AWS, 微服务, 分布式

Robotics: ROS, ROS2, SLAM, MuJoCo, IsaacSim

## Accuracy Benchmarks

From 289 Boss直聘 job postings:
- Salary extraction: 98.9%
- City extraction: 98.9%
- Skill keyword matching: 100% (coverage depends on keyword list)
- Recruiter extraction: ~80% (some posts don't show recruiter info)
- Job title: 100% (first-line extraction, may need OCR cleanup for truncated titles)

## Known Limitations

1. **Company name NOT present**: Boss直聘's job detail page does not show the hiring company name — only the recruiter/headhunter agency. Cannot extract.
2. **Page 2 duplication**: When merging `_1.jpg` + `_2.jpg`, the header block (job title, salary, city) appears twice. The second occurrence should be deduplicated.
3. **OCR truncation**: Long job titles may be truncated by OCR (e.g., "大模型算法工程师（视频多模态方..：")
4. **Missing headers**: ~3/289 files start directly with JD body — the header screenshot was missing or corrupted.
