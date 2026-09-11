"""Preview Xiaohongshu post HTML."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

INDEX = Path(r"d:\绿联云办公\项目 水龙头项目 CodeAudit_项目文档\assets\pandaone-agent-2026\index.html")
OUT = Path(r"d:\绿联云办公\项目 水龙头项目 CodeAudit_项目文档\assets\pandaone-agent-2026\preview.png")


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=2)
        page = await ctx.new_page()
        await page.goto(f"file://{INDEX}", wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)
        await page.screenshot(path=str(OUT), full_page=False)
        print("OK", OUT)
        await browser.close()


asyncio.run(main())