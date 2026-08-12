"""生成 GitHub Pages 首页：最新日报内容 + 历史日报日期导航

扫描 news-data/daily-*.html，取最新一份作为首页（index.html），
在内容区顶部注入"📅 历史日报"日期链接条，点击可直达任意历史日报。

用法: uv run python scripts/build_index.py
"""
import glob
import re

INDEX = "index.html"


def main() -> int:
    files = sorted(glob.glob("news-data/daily-*.html"))
    if not files:
        print("❌ 未找到日报文件 news-data/daily-*.html")
        return 1

    latest = files[-1]
    html = open(latest, encoding="utf-8").read()

    # 历史日期链接（最新在前）
    links = []
    for f in reversed(files):
        m = re.search(r"daily-(\d{4})-(\d{2})-(\d{2})\.html", f)
        if not m:
            continue
        label = f"{m.group(2)}/{m.group(3)}"
        links.append(f'<a class="arc-link" href="{f}">{label}</a>')

    nav_style = (
        "<style>"
        ".archive-nav{display:flex;flex-wrap:wrap;align-items:center;gap:8px;"
        "margin:0 0 18px;padding:12px 16px;background:#1a1a1a;"
        "border:1px solid #2a2a2a;border-radius:12px}"
        ".archive-nav .arc-label{color:#888;font-size:12.5px;margin-right:4px}"
        ".archive-nav .arc-link{color:#8fa6ff;font-size:13px;text-decoration:none;"
        "padding:3px 10px;border:1px solid rgba(79,109,255,.5);border-radius:6px;"
        "transition:all .15s}"
        ".archive-nav .arc-link:hover{background:rgba(79,109,255,.15);color:#fff}"
        "</style>"
    )
    nav = (
        f'{nav_style}<div class="archive-nav">'
        f'<span class="arc-label">📅 历史日报</span>{" ".join(links)}'
        "</div>"
    )

    # 注入到内容区顶部（最新日报的 .content 之前）
    if '<div class="content">' in html:
        html = html.replace('<div class="content">', f'<div class="content">{nav}', 1)
    else:
        html = html.replace("<body>", f"<body>{nav}", 1)

    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 首页已生成: {INDEX}（最新日报 {latest}，历史 {len(links)} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
