"""生成 GitHub Pages 首页 + 历史日报侧边导航 + 行动分级导航

- 扫描 news-data/daily-*.html，最新一份作为首页 index.html
- 每份日报侧栏注入"📅 历史日报"导航：
  - 按月分组（如 2026年8月）
  - 默认显示最近 6 条，更早的折叠在"更早日报 ▾"
  - 顶部"🏠 返回首页"按钮
- 每份日报侧栏注入"⚡ 行动分级"导航（旧版 HTML 无此功能时补注入）：
  - 按 立即行动/小成本试用/观望/暂不跟进 分组，点击直达该分级第一张新闻卡片
  - 新版 HTML 由 html_render.py 生成自带，此处检测到即跳过（幂等）
- 幂等：历史导航带 <!--ARC_NAV--> 标记，行动分级带 class="adv-nav"，均不重复注入

用法: uv run python scripts/build_index.py
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.html_render import adv_nav_html  # noqa: E402

INDEX = "index.html"
MAX_VISIBLE = 6  # 默认直接显示的最近日报条数，其余折叠

NAV_BEGIN = "<!--ARC_NAV-->"
NAV_END = "<!--/ARC_NAV-->"

ADV_CLS_TO_NAME = {
    "act": "立即行动",
    "try": "小成本试用",
    "watch": "观望",
    "skip": "暂不跟进",
}

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


# 旧版日报补注入"行动分级"导航时附带的样式与脚本（与 html_render.py 一致）
ADV_STYLE = """
<style>
.adv-nav { display: flex; flex-direction: column; gap: 4px; margin-top: 14px; padding-top: 14px; border-top: 1px solid #2a2a2a; }
.adv-label { color: #666666; font-size: 11px; letter-spacing: 1.5px; padding: 0 12px 4px; }
.adv-chip {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 12px; border-radius: 8px;
  background: transparent; border: 1px solid transparent; border-left: 3px solid transparent;
  color: #666666; font-size: 13px; text-decoration: none; transition: all .15s;
}
.adv-chip:hover { background: rgba(255,255,255,.04); color: #cccccc; }
.adv-chip.act { border-left-color: rgba(196,237,26,.6); }
.adv-chip.try { border-left-color: rgba(184,122,255,.6); }
.adv-chip.watch { border-left-color: rgba(79,109,255,.7); }
.adv-chip.skip { border-left-color: rgba(119,119,119,.6); }
.adv-chip.active { background: rgba(255,255,255,.06); color: #ffffff; font-weight: 700; }
.adv-chip .adv-n {
  color: #888888; background: rgba(255,255,255,.08); border-radius: 20px;
  padding: 0 8px; font-size: 12px; font-weight: 600; min-width: 22px; text-align: center;
}
.adv-chip.act .adv-n { color: #c4ed1a; background: rgba(196,237,26,.1); }
.adv-chip.try .adv-n { color: #d8c4f5; background: rgba(184,122,255,.12); }
.adv-chip.watch .adv-n { color: #8fa6ff; background: rgba(79,109,255,.12); }
.adv-chip.skip .adv-n { color: #9a9a9a; background: rgba(119,119,119,.1); }
.adv-chip.active .adv-n { background: rgba(255,255,255,.16); }
.card { scroll-margin-top: 18px; }
@media (max-width:860px){
  .adv-nav { flex-direction: row; flex-wrap: wrap; align-items: center; }
  .adv-label { width: 100%; }
}
</style>
"""

# 脚本必须放在 body 末尾执行（此时 .adv-chip 已存在于 DOM），否则监听器绑定失败
ADV_SCRIPT = """
<script>
(function(){
  var advChips = document.querySelectorAll(".adv-chip");
  function setAdvActive(hash){
    advChips.forEach(function(c){
      var h = c.getAttribute("href");
      c.classList.toggle("active", hash.indexOf(h) === 0);
    });
  }
  advChips.forEach(function(c){ c.addEventListener("click", function(){ setAdvActive(c.getAttribute("href")); }); });
  window.addEventListener("hashchange", function(){ setAdvActive(location.hash); });
  setAdvActive(location.hash);
})();
</script>
"""


def inject_adv(html: str) -> str:
    """旧版日报补注入"行动分级"导航：给卡片加锚点 id，侧栏加分级导航。幂等。"""
    if 'class="adv-nav"' in html:
        return html

    starts = [m.end() for m in re.finditer(r'<div class="card">', html)]
    if not starts:
        return html

    # 正序编号（页面第一张卡 = -1），与 html_render.py 生成的规则一致
    ids: dict = {}
    counts: dict = {}
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(html)
        m = re.search(r'<span class="badge advice (act|try|watch|skip)">', html[s:e])
        if not m:
            continue
        cls = m.group(1)
        counts[cls] = counts.get(cls, 0) + 1
        ids[i] = f'id="adv-{cls}-{counts[cls]}"'
    # 从后往前应用替换，避免索引偏移
    for i in range(len(starts) - 1, -1, -1):
        if i not in ids:
            continue
        html = html[: starts[i] - 18] + f'<div class="card" {ids[i]}>' + html[starts[i]:]

    advice_cnt = {
        name: counts[cls]
        for cls, name in ADV_CLS_TO_NAME.items()
        if counts.get(cls)
    }
    nav = adv_nav_html(advice_cnt)
    if not nav:
        return html

    # 导航（含样式）插到分类导航后；脚本插到 </body> 前保证 DOM 就绪
    idx = html.find("</nav>")
    if idx == -1:
        return html
    html = html[: idx + 6] + ADV_STYLE + nav + html[idx + 6:]
    bidx = html.rfind("</body>")
    if bidx != -1:
        html = html[:bidx] + ADV_SCRIPT + html[bidx:]
    return html


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
        new = inject_adv(new)
        if new != html:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(new)
            print(f"↪ 已注入导航: {f}")

    # 2) 最新日报 -> 首页 index.html（链接带 news-data/ 前缀，返回首页指向自身）
    html = open(latest, encoding="utf-8").read()
    html = inject(html, prefix="news-data/", home="index.html", files=files, current=latest)
    html = inject_adv(html)
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 首页已生成: {INDEX}（最新日报 {latest}，历史 {len(files) - 1} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
