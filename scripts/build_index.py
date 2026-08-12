"""生成 GitHub Pages 首页 + 历史日报侧边导航

- 扫描 news-data/daily-*.html，最新一份作为首页 index.html
- 每份日报侧栏注入"📅 历史日报"导航：
  - 按月分组（如 2026年8月）
  - 默认显示最近 6 条，更早的折叠在"更早日报 ▾"
  - 顶部"🏠 返回首页"按钮
- 幂等：带 <!--ARC_NAV--> 标记，已注入则整体替换，不会重复注入

用法: uv run python scripts/build_index.py
"""
import glob
import os
import re

INDEX = "index.html"
MAX_VISIBLE = 6  # 默认直接显示的最近日报条数，其余折叠

NAV_BEGIN = "<!--ARC_NAV-->"
NAV_END = "<!--/ARC_NAV-->"

NAV_STYLE = """
<style>
.arc-nav{margin:18px 4px 0;padding:10px;background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px}
.arc-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;gap:8px}
.arc-title{color:#c4ed1a;font-size:12.5px;font-weight:600;letter-spacing:.5px;white-space:nowrap}
.arc-home{color:#8fa6ff;font-size:12px;text-decoration:none;border:1px solid rgba(79,109,255,.5);border-radius:6px;padding:2px 8px;transition:all .15s;white-space:nowrap}
.arc-home:hover{background:rgba(79,109,255,.15);color:#fff}
.arc-month-label{color:#6b6f7a;font-size:11px;margin:9px 0 4px;letter-spacing:.5px}
.arc-list{display:flex;flex-direction:column;gap:4px}
.arc-link{color:#9aa7c7;font-size:13px;text-decoration:none;padding:4px 10px;border-radius:6px;border:1px solid transparent;transition:all .15s}
.arc-link:hover{background:rgba(79,109,255,.12);color:#fff}
.arc-link.active{color:#fff;background:rgba(79,109,255,.18);border-color:rgba(79,109,255,.55);border-left:3px solid #4f6dff}
.arc-more{margin-top:6px;border:none;background:none;padding:0}
.arc-more summary{cursor:pointer;color:#888;font-size:12px;padding:4px 10px;list-style:none;border-radius:6px;transition:all .15s}
.arc-more summary::-webkit-details-marker{display:none}
.arc-more summary:hover{color:#fff}
@media (max-width:860px){
  .arc-nav{margin:8px 4px 0}
  .arc-head{flex-wrap:wrap}
  .arc-list{flex-direction:row;overflow-x:auto;padding-bottom:4px}
  .arc-month-label{flex-shrink:0;margin:2px 6px 0 0}
  .arc-link{flex-shrink:0;border:1px solid #2a2a2a}
}
</style>
"""


def parse_date(path: str):
    m = re.search(r"daily-(\d{4})-(\d{2})-(\d{2})\.html$", path.replace("\\", "/"))
    return m.groups() if m else None


def nav_html(prefix: str, home: str, files: list[str], current: str) -> str:
    """生成历史导航。prefix: 链接前缀(index 用 news-data/，日报用空)；home: 返回首页链接"""
    items = []
    for f in reversed(files):
        d = parse_date(f)
        if not d:
            continue
        y, mo, day = d
        href = prefix + os.path.basename(f).replace("\\", "/")
        active = " active" if f == current else ""
        items.append((y, mo, day, href, active))

    if not items:
        return ""

    def render(rows) -> str:
        parts, last = [], None
        for y, mo, day, href, active in rows:
            key = f"{y}-{mo}"
            if key != last:
                parts.append(f'<div class="arc-month-label">{y}年{int(mo)}月</div>')
                last = key
            parts.append(f'<a class="arc-link{active}" href="{href}">{mo}/{day}</a>')
        return "".join(parts)

    body = (
        f'<div class="arc-nav" id="arc-nav">'
        f'<div class="arc-head"><span class="arc-title">📅 历史日报</span>'
        f'<a class="arc-home" href="{home}">🏠 返回首页</a></div>'
        f'{render(items[:MAX_VISIBLE])}'
    )
    if len(items) > MAX_VISIBLE:
        body += f"<details class=\"arc-more\"><summary>更早日报 ▾</summary>{render(items[MAX_VISIBLE:])}</details>"
    body += "</div>"
    return NAV_STYLE + body


def inject(html: str, prefix: str, home: str, files: list[str], current: str) -> str:
    nav = NAV_BEGIN + nav_html(prefix, home, files, current) + NAV_END
    if NAV_BEGIN in html:
        # 已注入过：整体替换（幂等）
        return re.sub(re.escape(NAV_BEGIN) + r".*?" + re.escape(NAV_END),
                      lambda _: nav, html, flags=re.S)
    # 首次注入：放到侧栏分类导航之后
    for marker in ("</nav>", "</aside>"):
        idx = html.find(marker)
        if idx != -1:
            return html[: idx + len(marker)] + nav + html[idx + len(marker):]
    return html  # 找不到注入点，原样返回


def main() -> int:
    files = sorted(glob.glob("news-data/daily-*.html"))
    if not files:
        print("❌ 未找到日报文件 news-data/daily-*.html")
        return 1

    latest = files[-1]

    # 1) 历史日报注入侧栏导航（不含最新一份，它作为首页内容源）
    for f in files[:-1]:
        html = open(f, encoding="utf-8").read()
        new = inject(html, prefix="", home="../index.html", files=files, current=f)
        if new != html:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(new)
            print(f"↪ 已注入导航: {f}")

    # 2) 最新日报 -> 首页 index.html（链接带 news-data/ 前缀，返回首页指向自身）
    html = open(latest, encoding="utf-8").read()
    html = inject(html, prefix="news-data/", home="index.html", files=files, current=latest)
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 首页已生成: {INDEX}（最新日报 {latest}，历史 {len(files) - 1} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
