"""检查 industry_map 为空或结构异常的条目"""
import json

data = json.load(open("news-data/fetch-2026-08-12.json", encoding="utf-8"))
es = [e for e in data["entries"] if e.get("deduce")]
empty = 0
for e in es:
    d = e["deduce"]
    m = d.get("industry_map")
    if not m:
        empty += 1
        print(f'❌ 无 industry_map: {e.get("title", "")[:35]}')
        continue
    if isinstance(m, list) and m and not isinstance(m[0], dict):
        empty += 1
        print(f'⚠️ industry_map 非dict列表: {e.get("title", "")[:35]} -> {str(m[0])[:60]}')
        continue
    # 检查字段名
    if isinstance(m, list) and m and isinstance(m[0], dict):
        keys = set(m[0].keys())
        if not (keys & {"area", "domain", "name", "sense", "sensitivity", "note", "insight", "desc"}):
            empty += 1
            print(f'⚠️ 字段名异常: {e.get("title", "")[:35]} -> {list(keys)}')
print(f"\n检查 {len(es)} 条，异常 {empty} 条")
