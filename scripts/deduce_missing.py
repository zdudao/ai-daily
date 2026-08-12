"""补推演：为缺少 deduce 的精选新闻单独重试（最多 3 次）"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from src.config import get_timezone, load_config
from src.llm import generate_deduction


async def main() -> int:
    config = load_config()

    from src.storage import get_fetch_file, save_fetch_file

    fetch_file = get_fetch_file()
    with open(fetch_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    min_score = config["filter"]["min_score"]
    missing = [
        e
        for e in entries
        if e.get("entity_relevant", True)
        and (e.get("score") or 0) >= min_score
        and not e.get("deduce")
    ]
    print(f"待补推演 {len(missing)} 条...")
    if not missing:
        print("✅ 无待补推演条目")
        return 0

    done = 0
    for e in missing:
        for attempt in range(3):
            d, err = await generate_deduction(e, config["llm"])
            if err is None and d:
                e["deduce"] = d
                done += 1
                print(f'  ✅ [{attempt + 1}次] {e.get("title", "")[:35]}')
                break
            print(f'  ⚠️ 第{attempt + 1}次失败: {e.get("title", "")[:25]} {err}')
        else:
            print(f'  ❌ 最终失败: {e.get("title", "")[:35]}')

    data["entries"] = entries
    save_fetch_file(fetch_file, data.get("meta", {}), entries)
    print(f"💾 已保存: {fetch_file}（本次补推演 {done} 条）")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
