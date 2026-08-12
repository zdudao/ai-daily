"""验证 HTML 中五步推演渲染完整性"""
import re

html = open("news-data/daily-2026-08-12.html", encoding="utf-8").read()
empty_map = html.count('<div class="d-map-item"><b></b>')
total_map = html.count("d-map-item")
empty_stair = len(re.findall(r"阶段\d+（）：", html))
total_stair = html.count("阶段")
deduce_blocks = html.count('<details class="deduce">')
print(f"五步推演区块: {deduce_blocks}")
print(f"九域映射: 空 {empty_map} / 总 {total_map}")
print(f"落地阶梯: 空占位 {empty_stair} / 总 {total_stair}")
