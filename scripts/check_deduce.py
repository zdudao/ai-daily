"""统计五步推演成功率"""
import json

data = json.load(open("news-data/fetch-2026-08-12.json", encoding="utf-8"))
es = data["entries"]
qualified = [
    e
    for e in es
    if e.get("entity_relevant", True) and (e.get("score") or 0) >= 60
]
with_deduce = [e for e in qualified if e.get("deduce")]
print(f"精选总数: {len(qualified)}")
print(f"有推演: {len(with_deduce)}")
print(f"无推演: {len(qualified) - len(with_deduce)}")
for e in qualified:
    if not e.get("deduce"):
        print(f'  ❌ [{e.get("score")}] {e.get("source")}: {e.get("title", "")[:45]}')
