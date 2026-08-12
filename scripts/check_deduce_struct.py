"""检查 deduce 实际数据结构的字段名"""
import json

data = json.load(open("news-data/fetch-2026-08-12.json", encoding="utf-8"))
es = data["entries"]
with_d = [e for e in es if e.get("deduce")]
if not with_d:
    print("无 deduce 数据")
    raise SystemExit

d = with_d[0]["deduce"]
print("deduce 顶层字段:", list(d.keys()))
print()
print("industry_map 结构:", json.dumps(d.get("industry_map"), ensure_ascii=False, indent=2)[:600])
print()
print("staircase 结构:", json.dumps(d.get("staircase"), ensure_ascii=False, indent=2)[:600])
print()
print("action_card:", json.dumps(d.get("action_card"), ensure_ascii=False, indent=2)[:400])
