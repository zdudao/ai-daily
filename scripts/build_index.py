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

from src.html_render import _ADVICE_EMOJI, adv_nav_html  # noqa: E402

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
  var chips = document.querySelectorAll(".adv-chip");
  var cards = document.querySelectorAll(".card[data-adv]");
  var groups = document.querySelectorAll(".cat-group");
  function apply(cls){
    cards.forEach(function(c){ c.style.display = (cls === "all" || c.getAttribute("data-adv") === cls) ? "" : "none"; });
    groups.forEach(function(s){
      var any = false;
      s.querySelectorAll(".card").forEach(function(c){ if (c.style.display !== "none") any = true; });
      s.style.display = any ? "" : "none";
    });
  }
  chips.forEach(function(c){
    c.addEventListener("click", function(){
      chips.forEach(function(x){ x.classList.toggle("active", x === c); });
      apply(c.getAttribute("data-cls"));
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  });
  apply("all");
  chips.forEach(function(c){ c.classList.toggle("active", c.getAttribute("data-cls") === "all"); });
})();
</script>
"""


ADV_BEGIN = "<!--ADV_NAV-->"
ADV_END = "<!--/ADV_NAV-->"

# 打赏卡片：样式 + 结构（图片按目录区分前缀：index 用根目录，日报用 ../）
DONATE_STYLE = """
<style>
.donate{margin:18px 4px 0;padding:14px;background:#1a1a1a;border:1px solid rgba(196,237,26,.15);border-radius:12px;text-align:center}
.donate-title{color:#c4ed1a;font-size:13px;font-weight:700;letter-spacing:.5px;margin:0 0 6px}
.donate-desc{color:#888;font-size:11.5px;line-height:1.65;margin:0 0 10px;text-align:left}
.donate-qr{width:118px;height:118px;border-radius:8px;border:1px solid #2a2a2a;object-fit:contain;background:#fff;padding:4px;box-sizing:border-box}
.donate-tip{color:#6b6f7a;font-size:11px;margin:8px 0 0;letter-spacing:.5px}
@media (max-width:860px){
  .donate{margin:8px 4px 0}
  .donate-qr{width:92px;height:92px}
}
</style>
"""


DONATE_BEGIN = "<!--DONATE-->"
DONATE_END = "<!--/DONATE-->"


def inject_donate(html: str, prefix: str) -> str:
    """侧栏底部注入打赏赞助卡片（每次重建，prefix 按页面目录区分）。"""
    # 清理旧注入（含历史残缺块），保证 index/daily 目录前缀正确
    html = re.sub(r"</div>\s*<!--DONATE-->", "<!--DONATE-->", html)  # 删除游离闭合标签残留
    html = re.sub(re.escape(DONATE_BEGIN) + r".*?" + re.escape(DONATE_END), "", html, flags=re.S)
    html = re.sub(r'<div class="donate">.*?</div>', "", html, flags=re.S)
    html = re.sub(r'<div class="donate-(?:title|desc|tip)">.*?</div>', "", html, flags=re.S)
    html = re.sub(r'<img class="donate-qr"[^>]*>', "", html)
    html = re.sub(r"<style>\s*\.donate\s*\{.*?</style>", "", html, flags=re.S)
    block = (
        DONATE_BEGIN
        + DONATE_STYLE
        + '<div class="donate">'
        + '<p class="donate-title">☕ 请老许喝碗胡辣汤</p>'
        + '<p class="donate-desc">这份日报每天抓取几百条 AI 资讯、逐条研判、'
          '写成开封话讲给你听，背后是实打实的人工和算力成本。'
          '觉得有用，扫码支持一下，让日报能一直做下去。</p>'
        + f'<img class="donate-qr" src="{prefix}donate.png" alt="打赏二维码">'
        + '<p class="donate-tip">微信 / 支付宝 扫码打赏</p>'
        + "</div>"
        + DONATE_END
    )
    idx = html.rfind("</aside>")
    if idx == -1:
        return html
    return html[:idx] + block + html[idx:]


def inject_adv(html: str) -> str:
    """给日报补注入/重建"行动分级"导航（过滤 + 分级图标）。

    - 给每张卡片加锚点 id + data-adv（用于点击过滤）
    - 评分数字替换为行动分级图标
    - 侧栏插入行动分级导航（含"全部新闻"），脚本放 body 末尾
    - 幂等/可升级：先清理旧注入（标记块/旧样式/旧脚本/卡片旧属性）再重建
    """
    # --- 1) 清理旧注入，保证可重复运行且能升级旧版本 ---
    html = re.sub(re.escape(ADV_BEGIN) + r".*?" + re.escape(ADV_END), "", html, flags=re.S)
    # 移除所有已存在的行动分级导航块（新版 html_render 自带/旧版注入均无标记，按结构特征清）
    html = re.sub(r'<nav class="adv-nav">.*?</nav>', "", html, flags=re.S)
    html = re.sub(r"<style>\s*\.adv-nav\s*\{.*?</style>", "", html, flags=re.S)
    # 只删除"行动分级"脚本块（特征：包含 .adv-chip 选择器），不影响页面原有脚本
    html = re.sub(
        r"<script>(?:(?!</script>).)*\.adv-chip(?:(?!</script>).)*</script>",
        "",
        html,
        flags=re.S,
    )
    # 还原所有卡片为干净开标签（去掉旧 id/data-adv 属性）
    html = re.sub(r'<div class="card"[^>]*>', '<div class="card">', html)

    # --- 2) 卡片加锚点 id + data-adv ---
    starts = [m.end() for m in re.finditer(r'<div class="card">', html)]
    if not starts:
        return html

    ids: dict = {}
    counts: dict = {}
    for i, s in enumerate(starts):
        e = starts[i + 1] if i + 1 < len(starts) else len(html)
        m = re.search(r'<span class="badge advice (act|try|watch|skip)">', html[s:e])
        if not m:
            continue
        cls = m.group(1)
        counts[cls] = counts.get(cls, 0) + 1
        ids[i] = f'id="adv-{cls}-{counts[cls]}" data-adv="{cls}"'
    # 从后往前应用替换，避免索引偏移
    for i in range(len(starts) - 1, -1, -1):
        if i not in ids:
            continue
        html = html[: starts[i] - 18] + f'<div class="card" {ids[i]}>' + html[starts[i]:]

    # --- 3) 评分数字 → 行动分级图标（评分保留在数据层，页面不显示分数） ---
    html = re.sub(
        r'<span class="score (act|try|watch|skip)">\d+</span>',
        lambda m: (
            f'<span class="score {m.group(1)}" title="行动分级">'
            f"{_ADVICE_EMOJI[m.group(1)]}</span>"
        ),
        html,
    )

    # --- 4) 插入导航（含样式）与脚本 ---
    advice_cnt = {
        name: counts[cls]
        for cls, name in ADV_CLS_TO_NAME.items()
        if counts.get(cls)
    }
    nav = adv_nav_html(advice_cnt)
    if not nav:
        return html

    block = ADV_BEGIN + ADV_STYLE + nav + ADV_END
    idx = html.find("</nav>")
    if idx == -1:
        return html
    html = html[: idx + 6] + block + html[idx + 6:]
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

    # 1) 所有日报注入侧栏导航（含最新一份，保证任意日期页都能返回首页/切换日期）
    for f in files:
        html = open(f, encoding="utf-8").read()
        new = inject(html, prefix="", home="../index.html", files=files, current=f)
        new = inject_adv(new)
        new = inject_donate(new, "../")
        if new != html:
            with open(f, "w", encoding="utf-8") as fh:
                fh.write(new)
            print(f"↪ 已注入导航: {f}")

    # 2) 最新日报 -> 首页 index.html（index 版导航：链接带 news-data/ 前缀，返回首页指向自身）
    html = open(latest, encoding="utf-8").read()
    html = inject(html, prefix="news-data/", home="index.html", files=files, current=latest)
    html = inject_adv(html)
    html = inject_donate(html, "")
    with open(INDEX, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ 首页已生成: {INDEX}（最新日报 {latest}，历史 {len(files) - 1} 条）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
