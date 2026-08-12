"""分析当天 fetch 数据的评分分布，说明哪些新闻显示/不显示"""
import json
from collections import Counter

data = json.load(open("news-data/fetch-2026-08-12.json", encoding="utf-8"))
entries = data["entries"]
print(f"总条目: {len(entries)}")

scores = [e.get("score", 0) for e in entries]
ge90 = [e for e in entries if e.get("score", 0) >= 90]
ge60 = [e for e in entries if 60 <= e.get("score", 0) < 90]
lt60 = [e for e in entries if e.get("score", 0) < 60]
print(f"评分>=90 (热点/即时推送): {len(ge90)}")
print(f"60<=评分<90 (进每日digest): {len(ge60)}")
print(f"评分<60 (被过滤丢弃): {len(lt60)}")

print("\n=== 各来源条数 top 15 ===")
c = Counter(e.get("source", "") for e in entries)
for s, n in c.most_common(15):
    print(f"{n:3d}  {s}")

print("\n=== 评分>=90 的新闻 ===")
for e in ge90:
    print(f'  [{e.get("score")}] {e.get("source")}: {e.get("title", "")[:60]}')

print("\n=== 评分 60-89 抽样 (前10) ===")
for e in ge60[:10]:
    print(f'  [{e.get("score")}] {e.get("source")}: {e.get("title", "")[:60]}')
