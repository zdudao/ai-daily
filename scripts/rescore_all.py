"""用新的"实体商业观察者"评分标准重新评分当天 fetch 数据，并更新 JSON 与评分日志

用法: uv run python scripts/rescore_all.py [日期 YYYY-MM-DD, 默认今天]
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
from src.storage import save_fetch_file, save_score_log


async def main() -> int:
    config = load_config()
    tz = get_timezone(config)
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.now(tz).date().isoformat()

    from src.storage import get_fetch_file

    fetch_file = get_fetch_file(date.fromisoformat(day))
    if not os.path.exists(fetch_file):
        print(f"❌ 文件不存在: {fetch_file}")
        return 1

    with open(fetch_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    print(f"📂 读取 {len(entries)} 条条目: {fetch_file}")
    if not entries:
        print("⚠️ 无条目可重评")
        return 0

    print("🤖 使用新评分标准重新评分...")
    scored, errors = await score_batch(entries, config["llm"])
    if errors:
        print(f"⚠️ [score_batch] {len(errors)} 个错误: {errors[0]}")
    if not scored:
        print("❌ 评分全部失败，数据未更新")
        return 1

    # 重评后保留原 meta，更新 entries（含新 score/tags/summary/reason）
    data["meta"] = data.get("meta", {})
    data["meta"]["rescore_note"] = "已按实体商业观察者标准重新评分"
    data["meta"]["rescore_at"] = datetime.now(tz).isoformat()
    data["entries"] = scored
    save_fetch_file(fetch_file, data["meta"], scored)
    print(f"💾 已更新 {len(scored)} 条: {fetch_file}")

    # 重新生成评分日志
    log_path = save_score_log(scored, config)
    print(f"📝 评分日志已更新: {log_path}")

    # 汇总新分布
    hot = sum(1 for e in scored if (e.get("score") or 0) >= config["filter"]["hot_threshold"])
    digest = sum(
        1
        for e in scored
        if config["filter"]["min_score"] <= (e.get("score") or 0) < config["filter"]["hot_threshold"]
    )
    dropped = sum(1 for e in scored if (e.get("score") or 0) < config["filter"]["min_score"])
    print(
        f"📊 新分布: 热点(≥{config['filter']['hot_threshold']})={hot}, "
        f"精选={digest}, 过滤={dropped}, 共 {len(scored)}"
    )

    print("\n🔥 新热点（新标准下 ≥90 分）:")
    for e in sorted(scored, key=lambda x: x.get("score") or 0, reverse=True):
        if (e.get("score") or 0) >= config["filter"]["hot_threshold"]:
            print(f'  [{e.get("score")}] {e.get("source")}: {e.get("title", "")[:50]}')
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
