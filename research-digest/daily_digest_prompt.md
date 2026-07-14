# 每日 LLM / KV Cache 研究 Digest — Prompt 模板

日期：{DATE}
已收录，跳过不要重复：{ALREADY_SEEN_ARXIV_IDS}

请基于下面的关键词库执行搜索并产出结构化 digest（关键词库见附件 keywords.yaml，
或直接贴在这条消息下面）。

## 执行要求

1. 对 tier_0 / tier_1 / tier_2 / watchlist 分别搜索，不要合并成一个大 query 一次搜完——
   合并查询只会拿到每个方向都很表面的结果。重点找过去 24-48 小时内的新 arXiv 论文、
   GitHub 新 release、有分量的技术 blog/报告。
2. 对每条命中，判断是否与「KV cache 算法/系统层面（压缩、复用、eviction、position 管理）」
   或「agentic 场景下落回 KV cache/context 管理」直接相关。按 deprioritize 规则过滤掉无关
   内容,不要为了凑数量硬塞进来。
3. 按下面的结构输出，不要写成长段落堆砌：

---

### 🔥 今日必看（0-3 条，只放对我们的研究方向有直接影响的）
- **[标题]**（arXiv id，作者/机构）— 一句话讲清楚它跟已有参照系
  （StreamingLLM / SnapKV / ChunkKV / CacheBlend / CacheClip 等）比新在哪，
  对现有假设/风险清单构成支持还是挑战。

### 📄 新论文（按 tier 分类，每条一行：标题 + 一句话 takeaway）
#### KV Cache 压缩/驱逐
#### KV Cache 复用 / Position Re-indexing
#### Systems / Serving
#### Agentic Context 管理

### 🏗️ 工程/生态动态（vLLM / LMCache / SGLang 等仓库的新 release、RFC、issue 讨论）

### 🗑️ 过滤掉的（可选，1-2 条说明"为什么今天判定不相关"，帮助迭代关键词库）

---

4. 最后单独给出一段 JSONL 代码块，用于追加进 `papers.jsonl`（每条一行，不要加多余文字）：

```jsonl
{"date_seen": "{DATE}", "arxiv_id": "...", "title": "...", "tags": ["tier_0:KV cache eviction"], "one_line": "...", "relevance": "supports / challenges / orthogonal / background", "status": "to-read"}
```
