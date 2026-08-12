"""补分类：为当天精选新闻批量打"AI 能力类型"主分类（category），按 link 回写，保留原字段

用法: uv run python scripts/add_category.py [日期 YYYY-MM-DD, 默认今天]
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
from src.llm import call_llm, load_prompt, _parse_score_response
from src.storage import get_fetch_file, save_fetch_file

CATEGORIES = ("视频生成", "图像生成", "智能体与自动化", "文本与内容", "大模型与API", "平台与商业模式", "政策与宏观", "其他")


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
    targets = [
        e
        for e in entries
        if e.get("entity_relevant", True)
        and (e.get("score") or 0) >= min_score
        and not e.get("category")
    ]
    print(f"待打分类 {len(targets)} 条（精选 ≥{min_score} 且缺 category）...")
    if not targets:
        print("✅ 无待打条目")
        return 0

    # 分批（每批 ≤20 条）
    BATCH = 20
    prompt_path = config.get("llm", {}).get("prompts", {}).get("category", "prompts/category.md")
    all_hits = {}
    for i in range(0, len(targets), BATCH):
        batch = targets[i : i + BATCH]
        slim = [
            {
                "link": e.get("link", ""),
                "title": e.get("title", "")[:80],
                "source": e.get("source", ""),
                "score": e.get("score", 0),
                "entity_industry": e.get("entity_industry", []),
                "tags": e.get("tags", [])[:5],
                "entity_insight": e.get("entity_insight", "")[:150],
            }
            for e in batch
        ]
        prompt = load_prompt(
            prompt_path,
            entry_json=json.dumps(slim, ensure_ascii=False, indent=2),
        )
        try:
            response = await call_llm(
                prompt, config["llm"], response_format={"type": "json_object"}
            )
            results = _parse_score_response(response)
        except Exception as ex:
            print(f"⚠️ 批次{i//BATCH+1} 失败: {ex}")
            continue
        for r in results:
            link = r.get("link")
            cat = str(r.get("category", "")).strip()
            if not link or not cat:
                continue
            if cat not in CATEGORIES:
                # 模糊匹配（如"视频"→"视频生成"）
                cat = next((c for c in CATEGORIES if c in cat or cat in c), "其他")
            all_hits[link] = {"category": cat, "category_note": r.get("category_note", "")}
        print(f"  批次{i//BATCH+1}: 命中 {len(all_hits)}/{len(targets)}")

    if not all_hits:
        print("❌ 全部失败，未更新")
        return 1

    updated = 0
    for e in entries:
        hit = all_hits.get(e.get("link"))
        if hit:
            e["category"] = hit["category"]
            e["category_note"] = hit["category_note"]
            updated += 1

    save_fetch_file(fetch_file, data.get("meta", {}), entries)
    print(f"💾 已保存 {updated} 条: {fetch_file}")

    from collections import Counter

    cnt = Counter(e.get("category") for e in entries if e.get("category"))
    for k in CATEGORIES:
        if cnt.get(k):
            print(f"  {k}: {cnt[k]}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
