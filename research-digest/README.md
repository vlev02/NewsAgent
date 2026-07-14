# LLM 研究追踪 Routine — 使用说明

## 目录结构

```
research-digest/                  # 建议作为已有 repo 的子目录，而不是单独开新 repo
├── README.md                     # 本文件
├── keywords.yaml                 # 关键词库（分层，随时间迭代）
├── daily_digest_prompt.md        # 每日执行的 prompt 模板
├── digests/
│   └── 2026/07/2026-07-14.md     # 每日产出，按 年/月 分文件夹
├── papers.jsonl                  # 结构化论文追踪表（去重 + 长期检索用，首次运行自动创建）
└── scripts/                      # 可选：自动化脚本（Tier C）
    ├── generate_digest.py
    └── ../.github/workflows/daily-digest.yml
```

`papers.jsonl` 是这套系统的核心资产,不是 `digests/*.md`。md 文件是给人看的、一次性的；
jsonl 是给你（或 Claude）查询的："我之前是不是看过某篇讲 co-attended survivors 的论文？"
"过去一个月里有几篇挑战了 R1？" 这些问题都是查 jsonl,不是翻 md。

## 三档执行方式

从 Tier A 开始跑 1-2 周，等 keywords.yaml 稳定下来、你确认信噪比可以接受了，再考虑要不要升级。
不要一上来就搭 Tier C——自动化的前提是关键词库已经调好了，不然只是在自动生产噪音。

### Tier A · 纯手动（推荐起步）

每天（或想到的时候）：

1. 开一个新 Claude 对话，或者复用一个固定 Project（把 keywords.yaml 作为 Project 知识库传进去，
   这样不用每次都贴一遍）。
2. 把 `daily_digest_prompt.md` 整段贴过去，替换 `{DATE}`，`{ALREADY_SEEN_ARXIV_IDS}` 从
   `papers.jsonl` 里取最近 7 天的 id（防止同一篇论文连续几天都出现在 digest 里）。
3. Claude 会按关键词分层搜索、产出结构化 digest。
4. 存成 `digests/2026/07/2026-07-14.md`，把新论文追加进 `papers.jsonl`。
5. `git add -A && git commit -m "digest: 2026-07-14" && git push`。

单次成本大概 5-10 分钟。这一步同时也是在训练你的 keywords.yaml——发现新术语（比如某篇论文
自造了个新词）就加进去；发现某个词连续两周只带来噪音，就降级或删掉。

### Tier B · Claude Code / Cowork 辅助

把 repo clone 到本地，用 Claude Code 或 Cowork 打开，直接说"跑一下今天的 digest routine"——
它会自己读 keywords.yaml、读 papers.jsonl 去重、搜索、写文件、git commit，把 5 个手动步骤收成
一句话。想要完全自动的话，可以在本机加一个 cron / launchd job，每天早上跑：

```bash
claude code -p "read README.md in research-digest/ and run today's digest routine"
```

### Tier C · GitHub Actions 全自动

`scripts/generate_digest.py` + `.github/workflows/daily-digest.yml`：Actions 按 cron 定时跑脚本
（用 Anthropic API 的 web_search tool），生成 digest，**开一个 PR 而不是直接 commit** —— 建议保留
人工过一眼再合并，自动摘要偶尔会误判相关性，尤其是刚开始那几周关键词库还没调好的时候。
需要在 repo 的 Settings → Secrets 里加 `ANTHROPIC_API_KEY`。

## 要不要开一个在线 GitHub repo？

值得，即使暂时不做任何自动化：

- **可追溯**：git log 本身就是"我什么时候第一次关注到这个方向"的时间线，写论文 related work
  时经常要回头找"我当时是怎么判断这篇跟我们的关系的"——`papers.jsonl` 里的 `relevance_to_reclaim`
  字段就是干这个用的。
- **可 diff**：keywords.yaml 每次改动都有记录，能看出关注点是怎么演化的（比如从纯 KV cache
  压缩逐渐扩展到 agentic context 管理）。
- **纯文本、可 grep**：不依赖某个笔记软件的 vendor lock-in,Claude Code 也能直接读写，不需要额外
  的 MCP 连接。
- 如果内容涉及未发表的想法（比如 ReClaim 的具体假设/风险表），建议设为 **private**；如果哪天想
  让 lab 里其他人 subscribe，再单独考虑要不要拆一个 public 的出来。
