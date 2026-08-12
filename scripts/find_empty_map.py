"""定位仍为空的九域映射：检查数据中 industry_map 为空/异常字段的条目"""
import json

data = json.load(open("news-data/fetch-2026-08-12.json", encoding="utf-8"))
es = [e for e in data["entries"] if e.get("deduce")]
for e in es:
    m = e["deduce"].get("industry_map")
    if not m:
        print(f'❌ industry_map 为空: {e.get("title", "")[:40]}')
        continue
    # 检查元素是否有可渲染字段
    for item in m if isinstance(m, list) else []:
        if not isinstance(item, dict):
            print(f'⚠️ 非dict: {e.get("title", "")[:40]}')
            break
        has = item.get("area") or item.get("domain") or item.get("name") or item.get("领域名")
        if not has:
            print(f'⚠️ 无领域名: {e.get("title", "")[:40]} -> {str(item)[:80]}')
            break
