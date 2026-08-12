"""补推演：对高分级（≥deduce_min_score）缺 card 或缺 deduce 的条目重试生成顾问行动卡片

用法: uv run python scripts/retry_deduce.py [日期 YYYY-MM-DD, 默认今天]
"""
import asyncio
import json
import os
import sys
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from src.config import get_timezone, load_config
from src.llm import generate_deduction
from src.storage import get_fetch_file, save_fetch_file


def _has_new_card(d) -> bool:
    """是否已是新版顾问行动卡片（顶层 industry_impact/feasibility + card 含 decision/memo）"""
    if not isinstance(d, dict):
        return False
    card = d.get("card")
    if not isinstance(card, dict):
        return False
    return (
        bool(d.get("industry_impact"))
        and bool(d.get("feasibility"))
        and bool(card.get("decision"))
        and bool(card.get("memo"))
    )


async def main() -> int:
    config = load_config()
    tz = get_timezone(config)
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.now(tz).date().isoformat()

    fetch_file = get_fetch_file(date.fromisoformat(day))
    if not os.path.exists(fetch_file):
        print(f"❌ 文件不存在: {fetch_file}")
        return 1

    with open(fetch_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    min_score = config["filter"]["min_score"]
    deduce_min = config["filter"].get("deduce_min_score", 65)
    targets = [
        e
        for e in entries
        if e.get("entity_relevant", True)
        and (e.get("score") or 0) >= deduce_min
        and not _has_new_card(e.get("deduce"))
    ]
    print(f"待补卡片 {len(targets)} 条（精选 ≥{deduce_min} 且缺新版 card）...")
    if not targets:
        print("✅ 无待补条目")
        return 0

    ok = 0
    for e in targets:
        success = False
        for attempt in range(1, 4):
            deduce_data, err = await generate_deduction(e, config["llm"])
            if not err and isinstance(deduce_data.get("card"), dict):
                e["deduce"] = deduce_data
                ok += 1
                success = True
                break
            print(f"  ⚠️ 第{attempt}次: {e.get('title','')[:25]} -> {err or 'card缺失'}")
        if not success:
            print(f"  ❌ 放弃: {e.get('title','')[:40]}")

    save_fetch_file(fetch_file, data.get("meta", {}), entries)
    print(f"💾 已保存: {fetch_file} | 成功 {ok}/{len(targets)}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
