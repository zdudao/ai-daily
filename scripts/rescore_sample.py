"""用新评分标准对当天 fetch 数据抽样重新评分，验证 prompt 生效

用法: uv run python scripts/rescore_sample.py [条数]
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from src.config import load_config
from src.llm import score_batch


async def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    config = load_config()

    data = json.load(open("news-data/fetch-2026-08-12.json", encoding="utf-8"))
    entries = data["entries"]

    # 抽样：尽量覆盖不同来源
    seen_sources = set()
    sample = []
    for e in entries:
        src = e.get("source", "")
        if src not in seen_sources:
            seen_sources.add(src)
            sample.append(e)
        if len(sample) >= n:
            break
    # 不足则补齐
    if len(sample) < n:
        sample.extend([e for e in entries if e not in sample][: n - len(sample)])

    print(f"抽样 {len(sample)} 条重新评分（新实体商业视角）...")
    scored, errors = await score_batch(sample, config["llm"])
    if errors:
        print(f"⚠️ 评分错误: {errors}")

    scored.sort(key=lambda e: e.get("score") or 0, reverse=True)
    for e in scored:
        print(f'  [{e.get("score")}] {e.get("source")}: {e.get("title", "")[:40]}')
        print(f'      reason: {e.get("reason", "(无)")[:80]}')
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
