"""诊断 wechat2rss.bestblogs.dev 服务：并发检查所有微信源，输出失效/慢速清单

用法: uv run python scripts/check_wechat2rss.py
"""
import asyncio
import os
import sys
import time

import aiohttp

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import merge_sources, load_config

TIMEOUT = 15


async def check(session: aiohttp.ClientSession, feed: dict) -> dict:
    url = feed["xmlUrl"]
    start = time.monotonic()
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as resp:
            body = await resp.text()
            elapsed = time.monotonic() - start
            return {
                "title": feed["title"],
                "url": url,
                "code": resp.status,
                "elapsed": round(elapsed, 1),
                "body_head": body[:60].replace("\n", " "),
            }
    except asyncio.TimeoutError:
        return {
            "title": feed["title"],
            "url": url,
            "code": "TIMEOUT",
            "elapsed": round(time.monotonic() - start, 1),
            "body_head": "",
        }
    except Exception as e:
        return {
            "title": feed["title"],
            "url": url,
            "code": "ERR",
            "elapsed": round(time.monotonic() - start, 1),
            "body_head": f"{e}",
        }


async def main() -> int:
    config = load_config()
    sources = merge_sources(config["sources"])
    wechat = [s for s in sources if "wechat2rss.bestblogs.dev" in s.get("xmlUrl", "")]
    if not wechat:
        print("未找到 wechat2rss 源")
        return 0

    print(f"共 {len(wechat)} 个 wechat2rss 源，开始并发检查 (timeout={TIMEOUT}s)...")
    sem = asyncio.Semaphore(15)

    async def limited(feed):
        async with sem:
            return await check(session, feed)

    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[limited(f) for f in wechat])

    ok = [r for r in results if r["code"] == 200]
    notfound = [r for r in results if r["code"] == 500]
    slow = [r for r in results if r["code"] == 200 and r["elapsed"] > 8]
    timeout = [r for r in results if r["code"] == "TIMEOUT"]
    errs = [r for r in results if r["code"] == "ERR"]

    print(f"\n✅ 正常: {len(ok)} | ❌ 500/feed not found: {len(notfound)} | "
          f"⏱️ 慢速(>8s): {len(slow)} | ⏰ 超时: {len(timeout)} | ⚠️ 错误: {len(errs)}")

    if notfound:
        print("\n=== 失效源 (500 feed not found, 建议加入 config block) ===")
        for r in notfound:
            print(f'{{"title": "{r["title"]}", "xmlUrl": "{r["url"]}"}},')

    if slow:
        print("\n=== 慢速但可用 (elapsed > 8s) ===")
        for r in slow:
            print(f'{r["title"]}: {r["elapsed"]}s')

    if timeout:
        print("\n=== 超时 (需更长 timeout 或服务不稳定) ===")
        for r in timeout:
            print(f'{r["title"]}: {r["elapsed"]}s')

    if errs:
        print("\n=== 其他错误 ===")
        for r in errs:
            print(f'{r["title"]}: {r["body_head"]}')

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
