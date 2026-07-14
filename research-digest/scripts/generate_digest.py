#!/usr/bin/env python3
"""
generate_digest.py — Tier C 自动化脚本（起点版本，先在 Tier A 跑稳关键词库再启用）

用法：
    pip install anthropic pyyaml --break-system-packages
    ANTHROPIC_API_KEY=... python scripts/generate_digest.py

流程：
1. 读 keywords.yaml
2. 读 papers.jsonl，取最近 7 天已收录的 arxiv_id 用于去重
3. 调用 Claude API（带 web_search tool），按 daily_digest_prompt.md 的结构产出 digest
4. 写入 digests/{yyyy}/{mm}/{date}.md
5. 从返回文本里提取 ```jsonl ...``` 代码块，追加进 papers.jsonl

注意：这是起点，不是成品——第一次跑完建议人工检查一遍输出质量，
   尤其是 "🔥 今日必看" 的判断是否靠谱，再决定要不要接入 GitHub Actions 自动 PR。
"""

import re
import json
import datetime
from pathlib import Path

import yaml
import anthropic

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.date.today().isoformat()


def load_keywords() -> dict:
    return yaml.safe_load((ROOT / "keywords.yaml").read_text(encoding="utf-8"))


def recent_seen_ids(days: int = 7) -> list[str]:
    path = ROOT / "papers.jsonl"
    if not path.exists():
        return []
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    ids = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if datetime.date.fromisoformat(rec["date_seen"]) >= cutoff:
            ids.append(rec["arxiv_id"])
    return ids


def build_prompt(keywords: dict, seen_ids: list[str]) -> str:
    template = (ROOT / "daily_digest_prompt.md").read_text(encoding="utf-8")
    prompt = template.replace("{DATE}", TODAY).replace(
        "{ALREADY_SEEN_ARXIV_IDS}", ", ".join(seen_ids) or "无"
    )
    prompt += "\n\n关键词库：\n```yaml\n" + yaml.dump(keywords, allow_unicode=True) + "```"
    return prompt


def call_claude(prompt: str) -> str:
    client = anthropic.Anthropic()
    resp = client.messages.create(
        model="claude-sonnet-5",
        max_tokens=4000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{"role": "user", "content": prompt}],
    )
    return "\n".join(
        block.text for block in resp.content if getattr(block, "type", "") == "text"
    )


def save_digest(text: str) -> Path:
    d = datetime.date.today()
    out_dir = ROOT / "digests" / f"{d.year}" / f"{d.month:02d}"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{TODAY}.md"
    out_path.write_text(text, encoding="utf-8")
    return out_path


def append_jsonl(text: str) -> None:
    match = re.search(r"```jsonl\n(.*?)```", text, re.S)
    if not match:
        print("warning: no jsonl block found in Claude's response, skipping papers.jsonl append")
        return
    with (ROOT / "papers.jsonl").open("a", encoding="utf-8") as f:
        for line in match.group(1).strip().splitlines():
            line = line.strip()
            if line:
                f.write(line + "\n")


def main() -> None:
    keywords = load_keywords()
    seen_ids = recent_seen_ids()
    prompt = build_prompt(keywords, seen_ids)
    text = call_claude(prompt)
    path = save_digest(text)
    append_jsonl(text)
    print(f"digest written to {path}")


if __name__ == "__main__":
    main()
