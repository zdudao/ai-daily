"""补评：对重评时缺失 score（批次失败）或缺国产替代字段的条目单独重新评分

用法: uv run python scripts/rescore_failed.py [日期 YYYY-MM-DD, 默认今天]
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
from src.llm import score_batch
from src.storage import get_fetch_file, save_fetch_file, save_score_log


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
    print(f"📂 读取 {len(entries)} 条: {fetch_file}")

    # 缺 score 或实体相关缺国产替代字段 → 需要补评
    missing = [
        e
        for e in entries
        if not e.get("score")
        or (
            e.get("entity_relevant", True)
            and not e.get("entity_alternative")
        )
    ]
    # 去重（按 link）
    seen = set()
    unique = []
    for e in missing:
        link = e.get("link") or e.get("title")
        if link in seen:
            continue
        seen.add(link)
        unique.append(e)

    print(f"待补评 {len(unique)} 条（缺 score / 缺国产替代字段）...")
    if not unique:
        print("✅ 无待补评条目")
        return 0

    scored, errors = await score_batch(unique, config["llm"])
    if errors:
        print(f"⚠️ 补评错误: {errors[0]}")
    if not scored:
        print("❌ 补评失败")
        return 1

    by_link = {e.get("link"): e for e in scored if e.get("link")}
    replaced = 0
    for i, entry in enumerate(entries):
        new = by_link.get(entry.get("link"))
        if new:
            entries[i] = new
            replaced += 1
    print(f"✅ 已更新 {replaced} 条")

    data["entries"] = entries
    save_fetch_file(fetch_file, data.get("meta", {}), entries)
    print(f"💾 已保存: {fetch_file}")

    log_path = save_score_log(entries, config)
    print(f"📝 评分日志已更新: {log_path}")

    # 新分布
    min_score = config["filter"]["min_score"]
    hot = sum(1 for e in entries if (e.get("score") or 0) >= config["filter"]["hot_threshold"])
    digest = sum(1 for e in entries if min_score <= (e.get("score") or 0) < config["filter"]["hot_threshold"])
    print(f"📊 新分布: 热点(≥{config['filter']['hot_threshold']})={hot}, 精选={digest}, 过滤={len(entries)-hot-digest}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
