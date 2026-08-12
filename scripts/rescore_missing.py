"""补评：对重评时 link 未匹配的条目单独重新评分

用法: uv run python scripts/rescore_missing.py
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from src.config import get_timezone, load_config
from src.llm import score_batch


async def main() -> int:
    config = load_config()
    tz = get_timezone(config)

    from src.storage import get_fetch_file, save_fetch_file

    fetch_file = get_fetch_file()
    with open(fetch_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    # 定位仍未获得新评分的条目：实体相关但缺 entity_industry / entity_advice
    missing = [
        e
        for e in entries
        if e.get("entity_relevant", True)
        and (not e.get("entity_industry") or not e.get("entity_advice"))
    ]
    print(f"待补评 {len(missing)} 条（实体相关但缺行业/行动字段）...")
    if not missing:
        print("✅ 无待补评条目")
        return 0

    scored, errors = await score_batch(missing, config["llm"])
    if errors:
        print(f"⚠️ 补评错误: {errors[0]}")
    if not scored:
        print("❌ 补评失败")
        return 1

    # 用新评分替换（link 按原样匹配）
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

    # 重新生成评分日志
    from src.storage import save_score_log

    log_path = save_score_log(entries, config)
    print(f"📝 评分日志已更新: {log_path}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
